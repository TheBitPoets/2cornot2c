//go:build linux

// thebitlab-pilot-activate is the reviewed stage-0 production bootstrap.
//
// It is built with CGO_ENABLED=0. Before the first dynamic exec it creates a
// kernel-identified read-only snapshot, verifies the exact Noble amd64 Python
// runtime/loader trees and the externally pinned toolchain, then execs isolated
// Python. The Python activation fence adopts this transaction and replaces it
// with its broader stage-1 fence without an unfrozen code-loading interval.
package main

import (
	"bufio"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"
)

const (
	canonicalLauncher = "/usr/sbin/thebitlab-pilot-activate"
	toolsRoot         = "/usr/lib/thebitlab/pilot-tools"
	trustPin          = "/etc/thebitlab/trust/pilot-toolchain.json"
	pythonPath        = "/usr/bin/python3"
	manifestName      = "pilot-toolchain-manifest.json"
	runtimeAuthority  = "/run/thebitlab"
	runtimeRoot       = runtimeAuthority + "/pilot-activation-fence"
	transactionRoot   = runtimeRoot + "/transactions"
	statePath         = runtimeRoot + "/state.json"
	activationLock    = runtimeRoot + "/activation.lock"
	stateSchema       = "thebitlab.activation-fence.v2"
	manifestSchema    = "thebitlab.activation-fence-manifest.v1"
	mountSourcePrefix = "thebitlab-pilot-fence:"
	transactionName   = "trusted-static-bootstrap"
	manifestFile      = "transaction-manifest.json"
)

var (
	idPattern     = regexp.MustCompile(`^[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?$`)
	shaPattern    = regexp.MustCompile(`^[0-9a-f]{64}$`)
	commitPattern = regexp.MustCompile(`^[0-9a-f]{40}$`)
	tokenPattern  = regexp.MustCompile(`^[1-9][0-9]{0,19}-[0-9a-f]{32}$`)
)

var toolchainFiles = []string{
	"scripts/__init__.py",
	"scripts/nginx_config_ast.py",
	"scripts/pilot_environment.py",
	"scripts/pilot_ubuntu_activation.py",
	"scripts/pilot_trusted_activation_fence.py",
	"scripts/pilot_native_execution_closure.py",
	"scripts/pilot_ubuntu_reviewed_executables.py",
	"scripts/pilot_ubuntu_reviewed_native_code.py",
	"scripts/pilot_ubuntu_loader_lookup_policy.py",
	"scripts/validate_pilot_deployment.py",
	"schemas/pilot-deployment.schema.json",
	"schemas/pilot-deployment-v1-legacy.schema.json",
	"schemas/pilot-environment.schema.json",
	"deploy/pilot/templates/thebitlab-process-error-log.conf.template",
	"deploy/pilot/templates/thebitlab-log-format.conf.template",
	"deploy/pilot/templates/thebitlab-nginx.conf.template",
	"deploy/pilot/templates/thebitlab-logrotate.conf.template",
	"deploy/pilot/templates/thebitlab.service.template",
	"deploy/pilot/legacy-v1/thebitlab-log-format.conf.template",
	"deploy/pilot/legacy-v1/thebitlab-nginx.conf.template",
	"deploy/pilot/legacy-v1/thebitlab.service.template",
}

// These are explicit release data derived from the pinned Noble image. They are
// never learned or refreshed from the production host.
type treePolicy struct {
	Path   string
	SHA256 string
	Dirs   int
	Files  int
	Links  int
}

var bootstrapTrees = []treePolicy{
	{"/usr/lib/x86_64-linux-gnu", "84e0e21402a88414b237e0e144d6b8901831e4412fe27b04ee468f5d69a7a7df", 115, 1033, 74},
	{"/usr/lib/python3.12", "94cce3010870569d66c0c1b6521761b1f6e73b385beda080b3b5884aaf4f5bec", 90, 1193, 2},
	{"/usr/lib/python3/dist-packages", "414c6baefe31cf63e443acfddd890f690f3b4350d7aca1ceeba27650d1bfff3b", 19, 158, 0},
	{"/usr/local/lib", "d015c7c7f7c12500a9f3d7e1520ec39813e3bf728dd1e971568d5abf51ecde37", 3, 0, 0},
	{"/usr/lib64", "ef218388b1c4e9377d8b38d22e8ea0dc6460826a3f2a6db3409f36f6b42345e0", 1, 0, 1},
	{"/etc/ld.so.conf.d", "a45437fec9ac83840168e8bc2ba519d759b5a75c912a573def950c29db095da3", 1, 2, 0},
}

var bootstrapFiles = map[string]string{
	"/usr/bin/python3.12":  "1643dacd9feaedc58f3cc581e4d22577dfe25c09b10282936186ccf0f2e61118",
	"/etc/ld.so.cache":     "cce0b33c762f0c8de876998628011571c731267320958a596784d53e8d21af1b",
	"/etc/ld.so.conf":      "d4b198c463418b493208485def26a6f4c57279467b9dfa491b70433cedb602e8",
	"/etc/nsswitch.conf":   "eec30745bade42a3f3f792e4d4192e57d2bcfe8e472433b1de426fe39a39cddb",
	"/etc/ssl/openssl.cnf": "529815b0dd4bd6608bafeeb3d410b0683374e61aef792b3e3f38b3767d26f747",
}

var snapshotTargets = []string{
	"/usr/bin", "/usr/sbin", "/usr/lib", "/usr/lib64", "/usr/local", "/etc",
}

var usrmergeAliases = map[string]string{
	"/bin": "usr/bin", "/sbin": "usr/sbin", "/lib": "usr/lib", "/lib64": "usr/lib64",
}

type mountRecord struct {
	MountID    int
	ParentID   int
	MajorMinor string
	Root       string
	MountPoint string
	Options    []string
	Filesystem string
	Source     string
}

type targetRecord struct {
	Path            string           `json:"path"`
	Kind            string           `json:"kind"`
	Lower           string           `json:"lower"`
	Snapshot        string           `json:"snapshot"`
	Created         bool             `json:"created"`
	Manifest        map[string][]any `json:"manifest"`
	SourceHardlinks []string         `json:"source_hardlinks"`
}

type aliasRecord struct {
	Path     string `json:"path"`
	Target   string `json:"target"`
	Snapshot string `json:"snapshot"`
}

type witnessRecord struct {
	MountID    int      `json:"mount_id"`
	ParentID   int      `json:"parent_id"`
	MajorMinor string   `json:"major_minor"`
	Filesystem string   `json:"filesystem"`
	Source     string   `json:"source"`
	Root       string   `json:"root"`
	MountPoint string   `json:"mount_point"`
	Options    []string `json:"options"`
}

type transaction struct {
	Name    string         `json:"name"`
	Token   string         `json:"token"`
	Phase   string         `json:"phase"`
	Root    string         `json:"root"`
	Targets []targetRecord `json:"targets"`
	Aliases []aliasRecord  `json:"aliases"`
	Mount   *witnessRecord `json:"mount,omitempty"`
}

type stateDocument struct {
	Schema       string        `json:"schema"`
	BootID       string        `json:"boot_id"`
	Poisoned     bool          `json:"poisoned"`
	Transactions []transaction `json:"transactions"`
}

type immutableDocument struct {
	Schema      string      `json:"schema"`
	Transaction transaction `json:"transaction"`
}

type bootstrapFence struct {
	Transaction  transaction
	Root         string
	LowerMounts  []string
	External     []string
	AliasesMade  []string
	StateWritten bool
	LockFD       int
}

type pinDocument struct {
	SchemaVersion           string `json:"schema_version"`
	ToolchainID             string `json:"toolchain_id"`
	ToolchainManifestSHA256 string `json:"toolchain_manifest_sha256"`
	LauncherSHA256          string `json:"launcher_sha256"`
	ReleaseCommit           string `json:"release_commit"`
}

type toolchainManifest struct {
	SchemaVersion string            `json:"schema_version"`
	ToolchainID   string            `json:"toolchain_id"`
	ReleaseCommit string            `json:"release_commit"`
	Files         map[string]string `json:"files"`
}

func fail(format string, values ...any) error { return fmt.Errorf(format, values...) }

func decodeMountField(value string) string {
	replacements := []struct{ old, new string }{{`\040`, " "}, {`\011`, "\t"}, {`\012`, "\n"}, {`\134`, `\`}}
	for _, item := range replacements {
		value = strings.ReplaceAll(value, item.old, item.new)
	}
	return value
}

func mountRecords() ([]mountRecord, error) {
	file, err := os.Open("/proc/self/mountinfo")
	if err != nil {
		return nil, fail("mountinfo non leggibile: %w", err)
	}
	defer file.Close()
	var records []mountRecord
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		parts := strings.SplitN(scanner.Text(), " - ", 2)
		if len(parts) != 2 {
			return nil, errors.New("mountinfo non interpretabile")
		}
		left, right := strings.Fields(parts[0]), strings.Fields(parts[1])
		if len(left) < 6 || len(right) < 3 {
			return nil, errors.New("mountinfo incompleto")
		}
		mountID, e1 := strconv.Atoi(left[0])
		parentID, e2 := strconv.Atoi(left[1])
		if e1 != nil || e2 != nil {
			return nil, errors.New("mountinfo ID non canonico")
		}
		records = append(records, mountRecord{
			mountID, parentID, left[2], decodeMountField(left[3]), decodeMountField(left[4]),
			strings.Split(left[5], ","), right[0], decodeMountField(right[1]),
		})
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return records, nil
}

func topMount(path string) (*mountRecord, error) {
	records, err := mountRecords()
	if err != nil {
		return nil, err
	}
	var result *mountRecord
	for index := range records {
		if records[index].MountPoint == path {
			copy := records[index]
			result = &copy
		}
	}
	return result, nil
}

func witness(record *mountRecord) *witnessRecord {
	options := append([]string(nil), record.Options...)
	sort.Strings(options)
	return &witnessRecord{record.MountID, record.ParentID, record.MajorMinor, record.Filesystem, record.Source, record.Root, record.MountPoint, options}
}

func canonicalRuntimeDirectory(metadata *syscall.Stat_t, mode fs.FileMode) bool {
	return metadata.Mode&syscall.S_IFMT == syscall.S_IFDIR &&
		metadata.Uid == 0 && metadata.Gid == 0 &&
		metadata.Mode&07777 == uint32(mode.Perm())
}

func attestRuntimeAuthorityInventory(descriptor int) error {
	if _, err := syscall.Seek(descriptor, 0, 0); err != nil {
		return err
	}
	duplicate, err := syscall.Dup(descriptor)
	if err != nil {
		return err
	}
	directory := os.NewFile(uintptr(duplicate), runtimeAuthority)
	entries, readErr := directory.Readdirnames(-1)
	closeErr := directory.Close()
	if readErr != nil {
		return readErr
	}
	if closeErr != nil {
		return closeErr
	}
	for _, entry := range entries {
		switch entry {
		case "app", "logrotate", "pilot-activation-fence", "pilot-private-runtime":
		default:
			return fail("entry runtime authority inattesa: %s", entry)
		}
	}
	return nil
}

func ensureRuntimeAuthorityDirectory() error {
	runFD, err := syscall.Open("/run", syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW|syscall.O_CLOEXEC, 0)
	if err != nil {
		return err
	}
	defer syscall.Close(runFD)
	var runBefore syscall.Stat_t
	if err := syscall.Fstat(runFD, &runBefore); err != nil || !canonicalRuntimeDirectory(&runBefore, 0755) {
		return errors.New("/run runtime authority non canonica")
	}
	parentCreated := false
	if err := syscall.Mkdirat(runFD, "thebitlab", 0755); err == nil {
		parentCreated = true
	} else if err != syscall.EEXIST {
		return err
	}
	parentFD, err := syscall.Openat(runFD, "thebitlab", syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW|syscall.O_CLOEXEC, 0)
	if err != nil {
		return err
	}
	defer syscall.Close(parentFD)
	if parentCreated {
		if err := syscall.Fchmod(parentFD, 0755); err != nil {
			return err
		}
		if err := syscall.Fsync(runFD); err != nil {
			return err
		}
	}
	var parentOpen syscall.Stat_t
	if err := syscall.Fstat(parentFD, &parentOpen); err != nil || !canonicalRuntimeDirectory(&parentOpen, 0755) {
		return errors.New("/run/thebitlab runtime authority non canonica")
	}
	parentPath, err := os.Lstat(runtimeAuthority)
	if err != nil {
		return err
	}
	parentStat, ok := parentPath.Sys().(*syscall.Stat_t)
	if !ok || parentStat.Dev != parentOpen.Dev || parentStat.Ino != parentOpen.Ino || !canonicalRuntimeDirectory(parentStat, 0755) {
		return errors.New("/run/thebitlab runtime authority instabile")
	}
	if err := attestRuntimeAuthorityInventory(parentFD); err != nil {
		return err
	}
	leafCreated := false
	if err := syscall.Mkdirat(parentFD, "pilot-activation-fence", 0700); err == nil {
		leafCreated = true
	} else if err != syscall.EEXIST {
		return err
	}
	leafFD, err := syscall.Openat(parentFD, "pilot-activation-fence", syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW|syscall.O_CLOEXEC, 0)
	if err != nil {
		return err
	}
	defer syscall.Close(leafFD)
	if leafCreated {
		if err := syscall.Fchmod(leafFD, 0700); err != nil {
			return err
		}
		if err := syscall.Fsync(parentFD); err != nil {
			return err
		}
	}
	var leafOpen syscall.Stat_t
	if err := syscall.Fstat(leafFD, &leafOpen); err != nil || !canonicalRuntimeDirectory(&leafOpen, 0700) {
		return errors.New("runtime bootstrap leaf non canonica")
	}
	leafPath, err := os.Lstat(runtimeRoot)
	if err != nil {
		return err
	}
	leafStat, ok := leafPath.Sys().(*syscall.Stat_t)
	if !ok || leafStat.Dev != leafOpen.Dev || leafStat.Ino != leafOpen.Ino || !canonicalRuntimeDirectory(leafStat, 0700) {
		return errors.New("runtime bootstrap leaf instabile")
	}
	var parentAfter syscall.Stat_t
	if err := syscall.Fstat(parentFD, &parentAfter); err != nil || parentAfter.Dev != parentOpen.Dev || parentAfter.Ino != parentOpen.Ino {
		return errors.New("runtime authority parent sostituita")
	}
	return attestRuntimeAuthorityInventory(parentFD)
}

func ensureRootOnlyDirectory(path string, mode fs.FileMode) error {
	if err := ensureRuntimeAuthorityDirectory(); err != nil {
		return err
	}
	if path != runtimeRoot {
		if err := os.MkdirAll(path, mode); err != nil {
			return err
		}
	}
	info, err := os.Lstat(path)
	if err != nil {
		return err
	}
	statValue, ok := info.Sys().(*syscall.Stat_t)
	if !ok || info.Mode()&os.ModeSymlink != 0 || !canonicalRuntimeDirectory(statValue, mode) {
		return fail("runtime bootstrap non root-only: %s", path)
	}
	return nil
}

func fsyncDirectory(path string) error {
	file, err := os.Open(path)
	if err != nil {
		return err
	}
	defer file.Close()
	return file.Sync()
}

func atomicJSON(path string, value any, mode fs.FileMode) error {
	parent := filepath.Dir(path)
	if err := ensureRootOnlyDirectory(runtimeRoot, 0700); err != nil {
		return err
	}
	if err := ensureRootOnlyDirectory(transactionRoot, 0700); err != nil {
		return err
	}
	file, err := os.CreateTemp(parent, "."+filepath.Base(path)+".")
	if err != nil {
		return err
	}
	name := file.Name()
	defer os.Remove(name)
	if err := file.Chmod(mode); err != nil {
		file.Close()
		return err
	}
	encoder := json.NewEncoder(file)
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(value); err != nil {
		file.Close()
		return err
	}
	if err := file.Sync(); err != nil {
		file.Close()
		return err
	}
	if err := file.Close(); err != nil {
		return err
	}
	if err := os.Rename(name, path); err != nil {
		return err
	}
	return fsyncDirectory(parent)
}

func bootID() (string, error) {
	data, err := os.ReadFile("/proc/sys/kernel/random/boot_id")
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(data)), nil
}

func writeState(fence *bootstrapFence) error {
	id, err := bootID()
	if err != nil {
		return err
	}
	if err := atomicJSON(statePath, stateDocument{stateSchema, id, false, []transaction{fence.Transaction}}, 0600); err != nil {
		return err
	}
	fence.StateWritten = true
	return nil
}

func acquireLock() (int, error) {
	if err := ensureRootOnlyDirectory(runtimeRoot, 0700); err != nil {
		return -1, err
	}
	fd, err := syscall.Open(activationLock, syscall.O_RDWR|syscall.O_CREAT, 0600)
	if err != nil {
		return -1, err
	}
	deadline := time.Now().Add(30 * time.Second)
	lock := syscall.Flock_t{Type: syscall.F_WRLCK, Whence: 0, Start: 0, Len: 0}
	for {
		err = syscall.FcntlFlock(uintptr(fd), syscall.F_SETLK, &lock)
		if err == nil {
			return fd, nil
		}
		if err != syscall.EAGAIN && err != syscall.EACCES {
			syscall.Close(fd)
			return -1, err
		}
		if time.Now().After(deadline) {
			syscall.Close(fd)
			return -1, errors.New("timeout lock bootstrap")
		}
		time.Sleep(100 * time.Millisecond)
	}
}

func randomToken() (string, error) {
	data := make([]byte, 16)
	file, err := os.Open("/dev/urandom")
	if err != nil {
		return "", err
	}
	_, err = io.ReadFull(file, data)
	file.Close()
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("%d-%s", os.Getpid(), hex.EncodeToString(data)), nil
}

func shaFileFollow(path string) (string, error) {
	file, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer file.Close()
	info, err := file.Stat()
	if err != nil {
		return "", err
	}
	st := info.Sys().(*syscall.Stat_t)
	if !info.Mode().IsRegular() || st.Uid != 0 || info.Mode().Perm()&0022 != 0 {
		return "", fail("file seguito con metadata unsafe: %s", path)
	}
	hash := sha256.New()
	if _, err := io.Copy(hash, file); err != nil {
		return "", err
	}
	return hex.EncodeToString(hash.Sum(nil)), nil
}

func shaFile(path string) (string, error) {
	fd, err := syscall.Open(path, syscall.O_RDONLY|syscall.O_CLOEXEC|syscall.O_NOFOLLOW, 0)
	if err != nil {
		return "", err
	}
	file := os.NewFile(uintptr(fd), path)
	defer file.Close()
	var before, after syscall.Stat_t
	if err := syscall.Fstat(fd, &before); err != nil {
		return "", err
	}
	if before.Mode&syscall.S_IFMT != syscall.S_IFREG {
		return "", fail("file non regolare: %s", path)
	}
	hash := sha256.New()
	if _, err := io.Copy(hash, file); err != nil {
		return "", err
	}
	if err := syscall.Fstat(fd, &after); err != nil {
		return "", err
	}
	if before.Dev != after.Dev || before.Ino != after.Ino || before.Size != after.Size || before.Mtim != after.Mtim || before.Ctim != after.Ctim {
		return "", fail("file mutato durante hash: %s", path)
	}
	if before.Uid != 0 || before.Mode&0022 != 0 {
		return "", fail("metadata file unsafe: %s", path)
	}
	return hex.EncodeToString(hash.Sum(nil)), nil
}

func manifestTree(root string) (map[string][]any, []string, error) {
	manifest := map[string][]any{}
	hardlinks := []string{}
	err := filepath.WalkDir(root, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if path == root {
			return nil
		}
		rel, err := filepath.Rel(root, path)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(rel)
		if strings.ContainsAny(rel, "\x00\n\r") {
			return fail("path snapshot non canonico: %q", rel)
		}
		info, err := os.Lstat(path)
		if err != nil {
			return err
		}
		statValue, ok := info.Sys().(*syscall.Stat_t)
		if !ok {
			return fail("stat Linux assente: %s", path)
		}
		mode, uid, gid := uint32(statValue.Mode), uint32(statValue.Uid), uint32(statValue.Gid)
		switch statValue.Mode & syscall.S_IFMT {
		case syscall.S_IFDIR:
			manifest[rel] = []any{"d", mode, uid, gid}
		case syscall.S_IFREG:
			digest, err := shaFile(path)
			if err != nil {
				return err
			}
			manifest[rel] = []any{"f", mode, uid, gid, statValue.Size, digest}
			if statValue.Nlink != 1 {
				hardlinks = append(hardlinks, rel)
			}
		case syscall.S_IFLNK:
			target, err := os.Readlink(path)
			if err != nil {
				return err
			}
			manifest[rel] = []any{"l", mode, uid, gid, target}
		default:
			return fail("tipo snapshot vietato: %s", path)
		}
		return nil
	})
	sort.Strings(hardlinks)
	return manifest, hardlinks, err
}

func manifestsEqual(left, right map[string][]any) bool {
	leftJSON, _ := json.Marshal(left)
	rightJSON, _ := json.Marshal(right)
	return bytes.Equal(leftJSON, rightJSON)
}

func firstManifestDifference(left, right map[string][]any) string {
	keys := make([]string, 0, len(left)+len(right))
	seen := map[string]bool{}
	for key := range left { seen[key] = true; keys = append(keys, key) }
	for key := range right { if !seen[key] { keys = append(keys, key) } }
	sort.Strings(keys)
	for _, key := range keys {
		leftJSON, _ := json.Marshal(left[key]); rightJSON, _ := json.Marshal(right[key])
		if !bytes.Equal(leftJSON, rightJSON) { return fmt.Sprintf("%s source=%s snapshot=%s", key, leftJSON, rightJSON) }
	}
	return "unknown"
}

func copyRegular(source, destination string, info fs.FileInfo) error {
	fd, err := syscall.Open(source, syscall.O_RDONLY|syscall.O_CLOEXEC|syscall.O_NOFOLLOW, 0)
	if err != nil {
		return err
	}
	input := os.NewFile(uintptr(fd), source)
	defer input.Close()
	var before, after syscall.Stat_t
	if err := syscall.Fstat(fd, &before); err != nil {
		return err
	}
	if before.Mode&syscall.S_IFMT != syscall.S_IFREG {
		return fail("source cambiata tipo: %s", source)
	}
	output, err := os.OpenFile(destination, os.O_CREATE|os.O_EXCL|os.O_WRONLY, info.Mode().Perm())
	if err != nil {
		return err
	}
	_, copyErr := io.Copy(output, input)
	syncErr := output.Sync()
	closeErr := output.Close()
	if copyErr != nil {
		return copyErr
	}
	if syncErr != nil {
		return syncErr
	}
	if closeErr != nil {
		return closeErr
	}
	if err := syscall.Fstat(fd, &after); err != nil {
		return err
	}
	if before.Dev != after.Dev || before.Ino != after.Ino || before.Size != after.Size || before.Mtim != after.Mtim || before.Ctim != after.Ctim {
		return fail("source mutata durante copia: %s", source)
	}
	if err := os.Chown(destination, int(before.Uid), int(before.Gid)); err != nil {
		return err
	}
	return syscall.Chmod(destination, before.Mode&07777)
}

func copyTree(source, destination string) error {
	rootInfo, err := os.Lstat(source)
	if err != nil {
		return err
	}
	if !rootInfo.IsDir() || rootInfo.Mode()&os.ModeSymlink != 0 {
		return fail("source directory non canonica: %s", source)
	}
	if err := os.Mkdir(destination, rootInfo.Mode().Perm()); err != nil {
		return err
	}
	rootStat := rootInfo.Sys().(*syscall.Stat_t)
	if os.Chown(destination, int(rootStat.Uid), int(rootStat.Gid)) != nil {
		return fail("chown root snapshot fallita: %s", destination)
	}
	if err := syscall.Chmod(destination, rootStat.Mode&07777); err != nil { return err }
	return filepath.WalkDir(source, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if path == source {
			return nil
		}
		rel, err := filepath.Rel(source, path)
		if err != nil {
			return err
		}
		target := filepath.Join(destination, rel)
		info, err := os.Lstat(path)
		if err != nil {
			return err
		}
		statValue := info.Sys().(*syscall.Stat_t)
		switch statValue.Mode & syscall.S_IFMT {
		case syscall.S_IFDIR:
			if err := os.Mkdir(target, info.Mode().Perm()); err != nil {
				return err
			}
			if err := os.Chown(target, int(statValue.Uid), int(statValue.Gid)); err != nil {
				return err
			}
			return syscall.Chmod(target, statValue.Mode&07777)
		case syscall.S_IFREG:
			return copyRegular(path, target, info)
		case syscall.S_IFLNK:
			value, err := os.Readlink(path)
			if err != nil {
				return err
			}
			if err := os.Symlink(value, target); err != nil {
				return err
			}
			return os.Lchown(target, int(statValue.Uid), int(statValue.Gid))
		default:
			return fail("tipo source vietato: %s", path)
		}
	})
}

func treeIdentity(root string) (string, int, int, int, error) {
	var paths []string
	err := filepath.WalkDir(root, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		paths = append(paths, path)
		return nil
	})
	if err != nil {
		return "", 0, 0, 0, err
	}
	sort.Slice(paths, func(i, j int) bool {
		left, _ := filepath.Rel(root, paths[i])
		right, _ := filepath.Rel(root, paths[j])
		if left == "" {
			left = "."
		}
		if right == "" {
			right = "."
		}
		return left < right
	})
	hash := sha256.New()
	dirs, files, links := 0, 0, 0
	for _, path := range paths {
		rel, _ := filepath.Rel(root, path)
		rel = filepath.ToSlash(rel)
		if rel == "" {
			rel = "."
		}
		if strings.ContainsAny(rel, "\x00\n\r") {
			return "", 0, 0, 0, fail("tree path non canonico: %q", rel)
		}
		info, err := os.Lstat(path)
		if err != nil {
			return "", 0, 0, 0, err
		}
		st := info.Sys().(*syscall.Stat_t)
		fields := []string{rel}
		switch st.Mode & syscall.S_IFMT {
		case syscall.S_IFDIR:
			dirs++
			fields = append(fields, "d", strconv.FormatUint(uint64(st.Mode), 10), strconv.Itoa(int(st.Uid)), strconv.Itoa(int(st.Gid)))
		case syscall.S_IFREG:
			files++
			digest, err := shaFile(path)
			if err != nil {
				return "", 0, 0, 0, err
			}
			fields = append(fields, "f", strconv.FormatUint(uint64(st.Mode), 10), strconv.Itoa(int(st.Uid)), strconv.Itoa(int(st.Gid)), strconv.FormatInt(st.Size, 10), digest)
		case syscall.S_IFLNK:
			links++
			value, err := os.Readlink(path)
			if err != nil {
				return "", 0, 0, 0, err
			}
			fields = append(fields, "l", strconv.FormatUint(uint64(st.Mode), 10), strconv.Itoa(int(st.Uid)), strconv.Itoa(int(st.Gid)), value)
		default:
			return "", 0, 0, 0, fail("tree type vietato: %s", path)
		}
		hash.Write([]byte(strings.Join(fields, "\x00") + "\n"))
	}
	return hex.EncodeToString(hash.Sum(nil)), dirs, files, links, nil
}

func testInterlock() bool {
	info, err := os.Lstat("/run/thebitlab-ephemeral-activation-test")
	if err != nil {
		return false
	}
	st := info.Sys().(*syscall.Stat_t)
	data, err := os.ReadFile("/run/thebitlab-ephemeral-activation-test")
	return err == nil && info.Mode().IsRegular() && st.Uid == 0 && st.Gid == 0 && info.Mode().Perm() == 0600 && string(data) == "ephemeral-only\n"
}

func testPoint(point string) {
	if !testInterlock() {
		return
	}
	if os.Getenv("THEBITLAB_ACTIVATION_CRASH_POINT") == point {
		os.Exit(97)
	}
	requested := false
	for _, candidate := range strings.Split(os.Getenv("THEBITLAB_BOOTSTRAP_PAUSE_POINT"), ",") {
		if candidate == point { requested = true; break }
	}
	if !requested {
		return
	}
	_ = os.WriteFile("/run/thebitlab-bootstrap-phase", []byte(point+"\n"), 0600)
	deadline := time.Now().Add(60 * time.Second)
	for time.Now().Before(deadline) {
		if data, err := os.ReadFile("/run/thebitlab-bootstrap-continue"); err == nil && string(data) == point+"\n" {
			_ = os.Remove("/run/thebitlab-bootstrap-continue")
			return
		}
		time.Sleep(5 * time.Millisecond)
	}
	fmt.Fprintln(os.Stderr, "ERRORE: timeout test-only bootstrap pause")
	os.Exit(98)
}

func establishFence(lockFD int) (*bootstrapFence, error) {
	if os.Geteuid() != 0 {
		return nil, errors.New("production activation richiede root")
	}
	selfNS, e1 := os.Readlink("/proc/self/ns/mnt")
	pid1NS, e2 := os.Readlink("/proc/1/ns/mnt")
	if e1 != nil || e2 != nil || selfNS != pid1NS {
		return nil, errors.New("bootstrap richiede mount namespace PID 1")
	}
	if _, err := os.Lstat(statePath); err == nil {
		return nil, errors.New("fence stale presente: recovery manuale/fail-closed")
	} else if !os.IsNotExist(err) {
		return nil, err
	}
	testPoint("bootstrap_started")
	token, err := randomToken()
	if err != nil {
		return nil, err
	}
	if !tokenPattern.MatchString(token) {
		return nil, errors.New("token bootstrap non canonico")
	}
	root := filepath.Join(transactionRoot, token)
	if err := ensureRootOnlyDirectory(runtimeRoot, 0700); err != nil {
		return nil, err
	}
	if err := ensureRootOnlyDirectory(transactionRoot, 0700); err != nil {
		return nil, err
	}
	if err := os.Mkdir(root, 0700); err != nil {
		return nil, err
	}
	fence := &bootstrapFence{Root: root, LockFD: lockFD}
	for index, path := range snapshotTargets {
		fence.Transaction.Targets = append(fence.Transaction.Targets, targetRecord{path, "directory", fmt.Sprintf("lower/%04d", index), fmt.Sprintf("snapshot/%04d", index), false, map[string][]any{}, []string{}})
	}
	for _, path := range []string{"/bin", "/sbin", "/lib", "/lib64"} {
		source := "/" + usrmergeAliases[path]
		index := sort.SearchStrings(snapshotTargets, source)
		// snapshotTargets are not lexical, so resolve explicitly.
		index = -1
		for candidate, value := range snapshotTargets {
			if value == source {
				index = candidate
				break
			}
		}
		if index < 0 {
			return nil, fail("alias source fuori snapshot: %s", path)
		}
		fence.Transaction.Aliases = append(fence.Transaction.Aliases, aliasRecord{path, usrmergeAliases[path], fmt.Sprintf("snapshot/%04d", index)})
	}
	fence.Transaction.Name, fence.Transaction.Token, fence.Transaction.Phase, fence.Transaction.Root = transactionName, token, "planned", root
	if err := writeState(fence); err != nil {
		return fence, err
	}
	testPoint("bootstrap_before_root_mount")
	if err := syscall.Mount(mountSourcePrefix+token, root, "tmpfs", syscall.MS_NOSUID|syscall.MS_NODEV, "mode=0700,size=512m"); err != nil {
		return fence, err
	}
	testPoint("bootstrap_after_root_mount")
	record, err := topMount(root)
	if err != nil || record == nil {
		return fence, fail("root mount bootstrap non attestabile: %v", err)
	}
	if record.Filesystem != "tmpfs" || record.Source != mountSourcePrefix+token || record.Root != "/" {
		return fence, errors.New("root mount bootstrap identity divergente")
	}
	fence.Transaction.Mount, fence.Transaction.Phase = witness(record), "witnessed"
	if err := writeState(fence); err != nil {
		return fence, err
	}
	if err := os.Mkdir(filepath.Join(root, "lower"), 0700); err != nil {
		return fence, err
	}
	if err := os.Mkdir(filepath.Join(root, "snapshot"), 0700); err != nil {
		return fence, err
	}
	for index := range fence.Transaction.Targets {
		target := &fence.Transaction.Targets[index]
		lower, snapshot := filepath.Join(root, target.Lower), filepath.Join(root, target.Snapshot)
		if err := os.Mkdir(lower, 0700); err != nil {
			return fence, err
		}
		if err := syscall.Mount(target.Path, lower, "", syscall.MS_BIND, ""); err != nil {
			return fence, err
		}
		fence.LowerMounts = append(fence.LowerMounts, lower)
		before, hardlinks, err := manifestTree(lower)
		if err != nil {
			return fence, err
		}
		if err := copyTree(lower, snapshot); err != nil {
			return fence, err
		}
		after, _, err := manifestTree(lower)
		if err != nil {
			return fence, err
		}
		copied, _, err := manifestTree(snapshot)
		if err != nil {
			return fence, err
		}
		if !manifestsEqual(before, after) {
			return fence, fail("snapshot source instabile: %s %s", target.Path, firstManifestDifference(before, after))
		}
		if !manifestsEqual(after, copied) {
			return fence, fail("snapshot divergente: %s %s", target.Path, firstManifestDifference(after, copied))
		}
		target.Manifest, target.SourceHardlinks = copied, hardlinks
		if index == 0 {
			testPoint("bootstrap_during_snapshot")
		}
	}
	if err := writeState(fence); err != nil {
		return fence, err
	}
	// Predict the final root options in the immutable authority document.
	final := witness(record)
	optionSet := map[string]bool{"ro": true, "nosuid": true, "nodev": true}
	for _, option := range record.Options {
		if option != "rw" {
			optionSet[option] = true
		}
	}
	final.Options = final.Options[:0]
	for option := range optionSet {
		final.Options = append(final.Options, option)
	}
	sort.Strings(final.Options)
	fence.Transaction.Mount, fence.Transaction.Phase = final, "sealed"
	if err := atomicJSON(filepath.Join(root, manifestFile), immutableDocument{manifestSchema, fence.Transaction}, 0600); err != nil {
		return fence, err
	}
	if err := syscall.Mount("", root, "", syscall.MS_REMOUNT|syscall.MS_RDONLY|syscall.MS_NOSUID|syscall.MS_NODEV, "mode=0700"); err != nil {
		return fence, err
	}
	record, err = topMount(root)
	if err != nil || record == nil {
		return fence, errors.New("root remount bootstrap non attestabile")
	}
	fence.Transaction.Mount = witness(record)
	if record.Filesystem != "tmpfs" || record.Source != mountSourcePrefix+token || !contains(record.Options, "ro") || !contains(record.Options, "nosuid") || !contains(record.Options, "nodev") {
		return fence, errors.New("root bootstrap non sealed")
	}
	testPoint("bootstrap_after_seal")
	for _, target := range fence.Transaction.Targets {
		if err := syscall.Mount(filepath.Join(root, target.Snapshot), target.Path, "", syscall.MS_BIND, ""); err != nil {
			return fence, err
		}
		fence.External = append(fence.External, target.Path)
	}
	for _, alias := range fence.Transaction.Aliases {
		info, err := os.Lstat(alias.Path)
		if err != nil {
			return fence, err
		}
		st := info.Sys().(*syscall.Stat_t)
		value, err := os.Readlink(alias.Path)
		if err != nil || st.Uid != 0 || st.Gid != 0 || value != alias.Target {
			return fence, fail("alias usrmerge baseline divergente: %s", alias.Path)
		}
		if err := os.Remove(alias.Path); err != nil {
			return fence, err
		}
		if err := os.Mkdir(alias.Path, 0755); err != nil {
			return fence, err
		}
		if err := syscall.Mount(filepath.Join(root, alias.Snapshot), alias.Path, "", syscall.MS_BIND, ""); err != nil {
			return fence, err
		}
		fence.AliasesMade = append(fence.AliasesMade, alias.Path)
	}
	fence.Transaction.Phase = "active"
	if err := writeState(fence); err != nil {
		return fence, err
	}
	return fence, nil
}

func contains(values []string, wanted string) bool {
	for _, value := range values {
		if value == wanted {
			return true
		}
	}
	return false
}

func cleanupFence(fence *bootstrapFence) {
	if fence == nil {
		return
	}
	for index := len(fence.AliasesMade) - 1; index >= 0; index-- {
		_ = syscall.Unmount(fence.AliasesMade[index], syscall.MNT_DETACH)
		_ = os.Remove(fence.AliasesMade[index])
		_ = os.Symlink(usrmergeAliases[fence.AliasesMade[index]], fence.AliasesMade[index])
	}
	for index := len(fence.External) - 1; index >= 0; index-- {
		_ = syscall.Unmount(fence.External[index], syscall.MNT_DETACH)
	}
	for index := len(fence.LowerMounts) - 1; index >= 0; index-- {
		_ = syscall.Unmount(fence.LowerMounts[index], syscall.MNT_DETACH)
	}
	if fence.Root != "" {
		_ = syscall.Unmount(fence.Root, syscall.MNT_DETACH)
		_ = os.Remove(fence.Root)
	}
	if fence.StateWritten {
		_ = os.Remove(statePath)
		_ = fsyncDirectory(runtimeRoot)
	}
}

func attestBootstrapRuntime() error {
	if info, err := os.Lstat("/etc/ld.so.preload"); err == nil {
		return fail("/etc/ld.so.preload deve essere assente (type=%s)", info.Mode().String())
	} else if !os.IsNotExist(err) {
		return err
	}
	if _, err := os.Lstat("/usr/lib/python312.zip"); err == nil {
		return errors.New("python312.zip deve essere EXPECTED_ABSENT")
	} else if !os.IsNotExist(err) {
		return err
	}
	link, err := os.Readlink("/usr/bin/python3")
	if err != nil || link != "python3.12" {
		return errors.New("alias /usr/bin/python3 divergente")
	}
	loader, err := os.Readlink("/lib64/ld-linux-x86-64.so.2")
	if err != nil || loader != "../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2" {
		return errors.New("alias PT_INTERP divergente")
	}
	for path, expected := range bootstrapFiles {
		actual, err := shaFile(path)
		if err != nil {
			return err
		}
		if actual != expected {
			return fail("bootstrap digest divergente: %s", path)
		}
	}
	for _, policy := range bootstrapTrees {
		digest, dirs, files, links, err := treeIdentity(policy.Path)
		if err != nil {
			return err
		}
		if digest != policy.SHA256 || dirs != policy.Dirs || files != policy.Files || links != policy.Links {
			return fail("bootstrap lookup tree divergente: %s digest=%s counts=%d/%d/%d", policy.Path, digest, dirs, files, links)
		}
	}
	return nil
}

func rejectDuplicateJSON(data []byte) error {
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.UseNumber()
	var visit func() error
	visit = func() error {
		token, err := decoder.Token()
		if err != nil {
			return err
		}
		delimiter, ok := token.(json.Delim)
		if !ok {
			return nil
		}
		switch delimiter {
		case '{':
			seen := map[string]bool{}
			for decoder.More() {
				keyToken, err := decoder.Token()
				if err != nil {
					return err
				}
				key, ok := keyToken.(string)
				if !ok || seen[key] {
					return errors.New("JSON con chiave duplicata/non canonica")
				}
				seen[key] = true
				if err := visit(); err != nil {
					return err
				}
			}
			end, err := decoder.Token()
			if err != nil || end != json.Delim('}') {
				return errors.New("JSON object non terminato")
			}
		case '[':
			for decoder.More() {
				if err := visit(); err != nil {
					return err
				}
			}
			end, err := decoder.Token()
			if err != nil || end != json.Delim(']') {
				return errors.New("JSON array non terminato")
			}
		default:
			return errors.New("JSON delimiter inatteso")
		}
		return nil
	}
	if err := visit(); err != nil {
		return err
	}
	if _, err := decoder.Token(); err != io.EOF {
		return errors.New("JSON con trailing data")
	}
	return nil
}

func strictJSON(path string, destination any) ([]byte, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	if err := rejectDuplicateJSON(data); err != nil {
		return nil, err
	}
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(destination); err != nil {
		return nil, err
	}
	return data, nil
}

func trustedRegular(path string, directory bool) error {
	clean := filepath.Clean(path)
	if !filepath.IsAbs(path) || clean != path {
		return fail("trusted path non canonico: %s", path)
	}
	current := "/"
	parts := strings.Split(strings.TrimPrefix(path, "/"), "/")
	for index, part := range parts {
		current = filepath.Join(current, part)
		info, err := os.Lstat(current)
		if err != nil {
			return err
		}
		st := info.Sys().(*syscall.Stat_t)
		wantDir := index < len(parts)-1 || directory
		if info.Mode()&os.ModeSymlink != 0 || st.Uid != 0 || info.Mode().Perm()&0022 != 0 || (wantDir != info.IsDir()) {
			return fail("trusted path metadata divergente: %s", current)
		}
		if !wantDir && !info.Mode().IsRegular() {
			return fail("trusted file non regolare: %s", current)
		}
	}
	return nil
}

func verifyInstallation() (string, pinDocument, error) {
	var pin pinDocument
	if err := trustedRegular(trustPin, false); err != nil {
		return "", pin, err
	}
	if err := trustedRegular(canonicalLauncher, false); err != nil {
		return "", pin, err
	}
	if _, err := strictJSON(trustPin, &pin); err != nil {
		return "", pin, err
	}
	if pin.SchemaVersion != "thebitlab.pilot-toolchain-pin.v1" || !idPattern.MatchString(pin.ToolchainID) || !shaPattern.MatchString(pin.ToolchainManifestSHA256) || !shaPattern.MatchString(pin.LauncherSHA256) || !commitPattern.MatchString(pin.ReleaseCommit) {
		return "", pin, errors.New("external trust pin non canonico")
	}
	selfDigest, err := shaFileFollow("/proc/self/exe")
	if err != nil {
		return "", pin, err
	}
	launcherDigest, err := shaFile(canonicalLauncher)
	if err != nil {
		return "", pin, err
	}
	if selfDigest != pin.LauncherSHA256 || launcherDigest != pin.LauncherSHA256 {
		return "", pin, errors.New("launcher static digest diverso dal pin esterno")
	}
	root := filepath.Join(toolsRoot, pin.ToolchainID)
	if err := trustedRegular(root, true); err != nil {
		return "", pin, err
	}
	manifestPath := filepath.Join(root, manifestName)
	if err := trustedRegular(manifestPath, false); err != nil {
		return "", pin, err
	}
	var manifest toolchainManifest
	raw, err := strictJSON(manifestPath, &manifest)
	if err != nil {
		return "", pin, err
	}
	digest := sha256.Sum256(raw)
	if hex.EncodeToString(digest[:]) != pin.ToolchainManifestSHA256 || manifest.SchemaVersion != "thebitlab.pilot-toolchain.v1" || manifest.ToolchainID != pin.ToolchainID || manifest.ReleaseCommit != pin.ReleaseCommit {
		return "", pin, errors.New("toolchain manifest divergente dal pin")
	}
	expected := map[string]bool{}
	for _, name := range toolchainFiles {
		expected[name] = true
	}
	if len(manifest.Files) != len(expected) {
		return "", pin, errors.New("toolchain file inventory inatteso")
	}
	for name, expectedDigest := range manifest.Files {
		if !expected[name] || !shaPattern.MatchString(expectedDigest) {
			return "", pin, fail("toolchain manifest entry inattesa: %s", name)
		}
		path := filepath.Join(root, filepath.FromSlash(name))
		if err := trustedRegular(path, false); err != nil {
			return "", pin, err
		}
		actual, err := shaFile(path)
		if err != nil {
			return "", pin, err
		}
		if actual != expectedDigest {
			return "", pin, fail("toolchain file modificato: %s", name)
		}
	}
	actualFiles := map[string]bool{}
	err = filepath.WalkDir(root, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if path == root {
			return nil
		}
		rel, _ := filepath.Rel(root, path)
		rel = filepath.ToSlash(rel)
		info, err := os.Lstat(path)
		if err != nil {
			return err
		}
		st := info.Sys().(*syscall.Stat_t)
		if info.Mode()&os.ModeSymlink != 0 || st.Uid != 0 || info.Mode().Perm()&0022 != 0 {
			return fail("toolchain metadata unsafe: %s", rel)
		}
		if info.Mode().IsRegular() {
			actualFiles[rel] = true
		}
		return nil
	})
	if err != nil {
		return "", pin, err
	}
	actualFiles[manifestName] = actualFiles[manifestName]
	if len(actualFiles) != len(expected)+1 || !actualFiles[manifestName] {
		return "", pin, errors.New("toolchain actual inventory inatteso")
	}
	for name := range expected {
		if !actualFiles[name] {
			return "", pin, fail("toolchain file assente: %s", name)
		}
	}
	return root, pin, nil
}

func sanitizedEnvironment(root string, pin pinDocument, fence *bootstrapFence) []string {
	environment := []string{
		"HOME=/root", "LANG=C.UTF-8", "LC_ALL=C.UTF-8", "PATH=/usr/sbin:/usr/bin:/sbin:/bin",
		"THEBITLAB_TRUSTED_TOOLCHAIN_ID=" + pin.ToolchainID,
		"THEBITLAB_TRUSTED_TOOLCHAIN_ROOT=" + root,
		"THEBITLAB_STATIC_BOOTSTRAP_TOKEN=" + fence.Transaction.Token,
		"THEBITLAB_STATIC_BOOTSTRAP_LOCK_FD=" + strconv.Itoa(fence.LockFD),
	}
	if testInterlock() {
		for _, name := range []string{"THEBITLAB_EPHEMERAL_CRASH_TEST", "THEBITLAB_ACTIVATION_CRASH_POINT", "THEBITLAB_ACTIVATION_CRASH_FENCE_NAME", "THEBITLAB_BOOTSTRAP_PAUSE_POINT"} {
			if value := os.Getenv(name); value != "" {
				environment = append(environment, name+"="+value)
			}
		}
	}
	return environment
}

func run() (result error) {
	if err := os.Chdir("/"); err != nil {
		return err
	}
	lockFD, err := acquireLock()
	if err != nil {
		return err
	}
	fence, err := establishFence(lockFD)
	if err != nil {
		cleanupFence(fence)
		syscall.Close(lockFD)
		return err
	}
	defer func() {
		if result != nil {
			cleanupFence(fence)
			syscall.Close(lockFD)
		}
	}()
	if err := attestBootstrapRuntime(); err != nil {
		return err
	}
	root, pin, err := verifyInstallation()
	if err != nil {
		return err
	}
	testPoint("bootstrap_before_python_exec")
	code := "import runpy,sys;root=sys.argv.pop(1);sys.path.insert(0,root);runpy.run_module('scripts.pilot_ubuntu_activation',run_name='__main__')"
	arguments := []string{pythonPath, "-I", "-B", "-c", code, root}
	arguments = append(arguments, os.Args[1:]...)
	testPoint("bootstrap_python_exec")
	return syscall.Exec(pythonPath, arguments, sanitizedEnvironment(root, pin, fence))
}

func main() {
	if filepath.Clean(os.Args[0]) != canonicalLauncher {
		fmt.Fprintln(os.Stderr, "ERRORE: production activation consentita solo dal launcher statico installato")
		os.Exit(2)
	}
	if err := run(); err != nil {
		fmt.Fprintf(os.Stderr, "ERRORE: trusted static bootstrap: %v\n", err)
		os.Exit(2)
	}
}
