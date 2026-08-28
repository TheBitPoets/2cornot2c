//go:build linux

// thebitlab-private-runtime is the production S0/S1 authority for issue #704.
// The CGO-free static artifact builds and seals both roots, publishes the exact
// read-only S1:S0 composition, and is the target handoff broker. It never runs a
// dynamic host helper before pivoting the target into the synthetic root.
package main

import (
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
	"runtime"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"
)

const (
	runtimeAuthority = "/run/thebitlab"
	runtimeHost      = runtimeAuthority + "/pilot-private-runtime"
	s0Host           = runtimeHost + "/s0"
	s1Host          = runtimeHost + "/s1"
	mergedHost      = runtimeHost + "/merged"
	controlHost     = runtimeHost + "/control"
	stateHost       = runtimeHost + "/state.json"
	managerDrop     = "/run/systemd/system/nginx.service.d"
	managerDropFile = managerDrop + "/70-thebitlab-private-runtime.conf"
	launcherHost    = "/usr/sbin/thebitlab-private-runtime"
	pinHost         = "/etc/thebitlab/trust/pilot-private-runtime.json"
	s0Source        = "thebitlab-private-s0"
	s1Source        = "thebitlab-private-s1"
	managerSource   = "thebitlab-private-manager"
	stateSchema     = "thebitlab.private-runtime-state.v1"
	manifestSchema  = "thebitlab.private-runtime-manifest.v1"
	deploymentsRoot = "/etc/thebitlab/deployments"
)

var treePolicies = map[string]treePolicy{
	"/usr/lib/x86_64-linux-gnu":      {"84e0e21402a88414b237e0e144d6b8901831e4412fe27b04ee468f5d69a7a7df", 115, 1033, 74},
	"/usr/lib/python3.12":            {"94cce3010870569d66c0c1b6521761b1f6e73b385beda080b3b5884aaf4f5bec", 90, 1193, 2},
	"/usr/lib/python3/dist-packages": {"414c6baefe31cf63e443acfddd890f690f3b4350d7aca1ceeba27650d1bfff3b", 19, 158, 0},
}

var s1TreePolicies = map[string]treePolicy{
	"/etc/nginx":             {"026a39869452bd2aec4be2036ff05a4d0c2729f8e89b6721ec90f16465413b6b", 7, 13, 3},
	"/usr/share/nginx":       {"647df966b9c27faa03fe3cd07c0d8dbbcacd59370fbfd39f354a520d2db38457", 3, 3, 1},
	"/usr/lib/nginx/modules": {"51139bd9cf430b672599fb5c24af46318f7421d6c9f901439238ef4a818a876a", 1, 2, 0},
}

var s0Files = map[string]string{
	"/usr/bin/python3.12":  "1643dacd9feaedc58f3cc581e4d22577dfe25c09b10282936186ccf0f2e61118",
	"/etc/nsswitch.conf":   "eec30745bade42a3f3f792e4d4192e57d2bcfe8e472433b1de426fe39a39cddb",
	"/etc/ssl/openssl.cnf": "529815b0dd4bd6608bafeeb3d410b0683374e61aef792b3e3f38b3767d26f747",
	"/etc/passwd":          "5dbc7ebdf180bd84f58372b8dbd071f5bb175799ea23e197ff1732975f2b3f3b",
	"/etc/group":           "b5132aaf99e107c060b1f25cb3324e193dd83cb6bbf70f777b0d83a7638c49fe",
}

var s1Files = map[string]string{
	"/usr/sbin/nginx":             "1f16b72bea2f44e5d04fe6cf9e3e4b0dec53a82c50c7c1533c302a8ecaeccacf",
	"/usr/sbin/start-stop-daemon": "81faf821fdfdf1dc2991b71dfbd6a21116085f931bfeb0fd7b2623911a4831b4",
}

var candidateBundleFiles = []string{
	"firewall/origin-exposure.json",
	"logrotate/thebitlab",
	"manifest.normalized.json",
	"nginx/thebitlab-log-format.conf",
	"nginx/thebitlab-process-error-log.conf",
	"nginx/thebitlab.conf",
	"systemd/thebitlab.service",
}

var candidateLinks = map[string]string{
	"/etc/nginx/modules-enabled/90-thebitlab-process-error-log.conf": "/etc/thebitlab/current/nginx/thebitlab-process-error-log.conf",
	"/etc/nginx/conf.d/thebitlab-log-format.conf":                    "/etc/thebitlab/current/nginx/thebitlab-log-format.conf",
	"/etc/nginx/sites-enabled/thebitlab.conf":                        "/etc/thebitlab/current/nginx/thebitlab.conf",
	"/etc/logrotate.d/thebitlab":                                     "/etc/thebitlab/current/logrotate/thebitlab",
	"/etc/systemd/system/thebitlab.service":                          "/etc/thebitlab/current/systemd/thebitlab.service",
}

type treePolicy struct {
	SHA256             string
	Dirs, Files, Links int
}
type counters struct {
	FilesRead      int64 `json:"files_read"`
	BytesRead      int64 `json:"bytes_read"`
	FilesCopied    int64 `json:"files_copied"`
	BytesCopied    int64 `json:"bytes_copied"`
	HashOperations int64 `json:"hash_operations"`
	BytesHashed    int64 `json:"bytes_hashed"`
}
type metrics struct {
	Stage               string   `json:"stage"`
	WallSeconds         float64  `json:"wall_seconds"`
	CPUSeconds          float64  `json:"cpu_seconds"`
	Counters            counters `json:"counters"`
	Identities          int      `json:"identities"`
	OverlapIdentities   int      `json:"overlap_identities,omitempty"`
	OverlapBytes        int64    `json:"overlap_bytes,omitempty"`
	DuplicateCopies     int64    `json:"duplicate_copies"`
	PTInterp            string   `json:"pt_interp,omitempty"`
	PythonPolicy        string   `json:"python_policy,omitempty"`
	CompositionSeconds  float64  `json:"composition_seconds,omitempty"`
	ManagerFenceSeconds float64  `json:"manager_fence_seconds,omitempty"`
}
type objectIdentity struct {
	SHA256 string `json:"sha256"`
	Size   int64  `json:"size"`
	Stage  string `json:"stage"`
}
type manifest struct {
	Schema                  string                    `json:"schema"`
	Token                   string                    `json:"token"`
	MountSource             string                    `json:"mount_source"`
	Root                    string                    `json:"root"`
	Objects                 map[string]objectIdentity `json:"objects"`
	Links                   map[string]string         `json:"links,omitempty"`
	Metrics                 metrics                   `json:"metrics"`
	SelfSHA256              string                    `json:"self_sha256"`
	ToolchainID             string                    `json:"toolchain_id,omitempty"`
	ToolchainManifestSHA256 string                    `json:"toolchain_manifest_sha256,omitempty"`
	CandidateBundle         string                    `json:"candidate_bundle,omitempty"`
	CandidateLockSHA256     string                    `json:"candidate_lock_sha256,omitempty"`
}
type pinDocument struct {
	SchemaVersion           string `json:"schema_version"`
	ToolchainID             string `json:"toolchain_id"`
	ToolchainManifestSHA256 string `json:"toolchain_manifest_sha256"`
	LauncherSHA256          string `json:"launcher_sha256"`
	ReleaseCommit           string `json:"release_commit"`
}
type toolchainDocument struct {
	SchemaVersion string            `json:"schema_version"`
	ToolchainID   string            `json:"toolchain_id"`
	ReleaseCommit string            `json:"release_commit"`
	Files         map[string]string `json:"files"`
}

type mountIdentity struct {
	MountID      int      `json:"mount_id"`
	ParentID     int      `json:"parent_id"`
	MajorMinor   string   `json:"major_minor"`
	Root         string   `json:"root"`
	MountPoint   string   `json:"mount_point"`
	Options      []string `json:"options"`
	Filesystem   string   `json:"filesystem"`
	Source       string   `json:"source"`
	SuperOptions []string `json:"super_options"`
}

type runtimeState struct {
	Schema                  string                   `json:"schema"`
	Token                   string                   `json:"token"`
	Phase                   string                   `json:"phase"`
	S0ManifestSHA256        string                   `json:"s0_manifest_sha256"`
	S1ManifestSHA256        string                   `json:"s1_manifest_sha256"`
	ToolchainID             string                   `json:"toolchain_id"`
	ToolchainManifestSHA256 string                   `json:"toolchain_manifest_sha256"`
	BrokerSHA256            string                   `json:"broker_sha256"`
	DropinSHA256            string                   `json:"dropin_sha256"`
	CandidateBundle         string                   `json:"candidate_bundle"`
	CandidateLockSHA256     string                   `json:"candidate_lock_sha256"`
	RuntimeDevice           uint64                   `json:"runtime_device"`
	RuntimeInode            uint64                   `json:"runtime_inode"`
	Mounts                  map[string]mountIdentity `json:"mounts"`
}

type deploymentLock struct {
	SchemaVersion string            `json:"schema_version"`
	DeploymentID  string            `json:"deployment_id"`
	ReleaseCommit string            `json:"release_commit"`
	Files         map[string]string `json:"files"`
}

type candidateManifest struct {
	Origin struct {
		TLSCertificateFile string `json:"tls_certificate_file"`
		TLSPrivateKeyFile  string `json:"tls_private_key_file"`
	} `json:"origin"`
}

type copier struct {
	root    string
	c       counters
	objects map[string]objectIdentity
	stage   string
}

func cpuSeconds() float64 {
	var usage syscall.Rusage
	_ = syscall.Getrusage(syscall.RUSAGE_SELF, &usage)
	return float64(usage.Utime.Sec+usage.Stime.Sec) + float64(usage.Utime.Usec+usage.Stime.Usec)/1e6
}
func hexDigest(sum []byte) string { return hex.EncodeToString(sum) }
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
			return fmt.Errorf("entry runtime authority inattesa: %s", entry)
		}
	}
	return nil
}
func attestRuntimeAuthorityDirectory(create bool) error {
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
	if create {
		if err := syscall.Mkdirat(runFD, "thebitlab", 0755); err == nil {
			parentCreated = true
		} else if err != syscall.EEXIST {
			return err
		}
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
	if create {
		if err := syscall.Mkdirat(parentFD, "pilot-private-runtime", 0700); err == nil {
			leafCreated = true
		} else if err != syscall.EEXIST {
			return err
		}
	}
	leafFD, err := syscall.Openat(parentFD, "pilot-private-runtime", syscall.O_RDONLY|syscall.O_DIRECTORY|syscall.O_NOFOLLOW|syscall.O_CLOEXEC, 0)
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
		return errors.New("private-runtime leaf non canonica")
	}
	leafPath, err := os.Lstat(runtimeHost)
	if err != nil {
		return err
	}
	leafStat, ok := leafPath.Sys().(*syscall.Stat_t)
	if !ok || leafStat.Dev != leafOpen.Dev || leafStat.Ino != leafOpen.Ino || !canonicalRuntimeDirectory(leafStat, 0700) {
		return errors.New("private-runtime leaf instabile")
	}
	var parentAfter syscall.Stat_t
	if err := syscall.Fstat(parentFD, &parentAfter); err != nil || parentAfter.Dev != parentOpen.Dev || parentAfter.Ino != parentOpen.Ino {
		return errors.New("runtime authority parent sostituita")
	}
	return attestRuntimeAuthorityInventory(parentFD)
}
func ensureDir(path string, mode fs.FileMode) error {
	if path == runtimeHost {
		return attestRuntimeAuthorityDirectory(true)
	}
	if err := os.MkdirAll(path, mode); err != nil {
		return err
	}
	info, err := os.Lstat(path)
	if err != nil {
		return err
	}
	st, ok := info.Sys().(*syscall.Stat_t)
	if !ok || !info.IsDir() || info.Mode()&os.ModeSymlink != 0 || st.Uid != 0 || info.Mode().Perm()&0022 != 0 {
		return fmt.Errorf("directory unsafe: %s", path)
	}
	return nil
}
func writeJSON(path string, value any) error {
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	if err := os.WriteFile(path, data, 0600); err != nil {
		return err
	}
	return nil
}
func stableCopy(source, destination string, expected string, c *counters) (string, int64, error) {
	fd, err := syscall.Open(source, syscall.O_RDONLY|syscall.O_CLOEXEC|syscall.O_NOFOLLOW, 0)
	if err != nil {
		return "", 0, err
	}
	in := os.NewFile(uintptr(fd), source)
	defer in.Close()
	var before, after syscall.Stat_t
	if err := syscall.Fstat(fd, &before); err != nil {
		return "", 0, err
	}
	if before.Mode&syscall.S_IFMT != syscall.S_IFREG || before.Uid != 0 || before.Mode&0022 != 0 {
		return "", 0, fmt.Errorf("source file unsafe: %s", source)
	}
	if err := os.MkdirAll(filepath.Dir(destination), 0755); err != nil {
		return "", 0, err
	}
	out, err := os.OpenFile(destination, os.O_WRONLY|os.O_CREATE|os.O_EXCL, fs.FileMode(before.Mode&07777))
	if err != nil {
		return "", 0, err
	}
	h := sha256.New()
	n, copyErr := io.Copy(io.MultiWriter(out, h), in)
	closeErr := out.Close()
	if copyErr != nil {
		return "", 0, copyErr
	}
	if closeErr != nil {
		return "", 0, closeErr
	}
	if err := syscall.Fstat(fd, &after); err != nil {
		return "", 0, err
	}
	if before.Dev != after.Dev || before.Ino != after.Ino || before.Size != after.Size || before.Mtim != after.Mtim || before.Ctim != after.Ctim || n != before.Size {
		return "", 0, fmt.Errorf("source changed during one-pass copy: %s", source)
	}
	if err := os.Chown(destination, int(before.Uid), int(before.Gid)); err != nil {
		return "", 0, err
	}
	if err := syscall.Chmod(destination, before.Mode&07777); err != nil {
		return "", 0, err
	}
	digest := hexDigest(h.Sum(nil))
	c.FilesRead++
	c.FilesCopied++
	c.HashOperations++
	c.BytesRead += n
	c.BytesCopied += n
	c.BytesHashed += n
	if expected != "" && digest != expected {
		return digest, n, fmt.Errorf("reviewed digest mismatch: %s actual=%s", source, digest)
	}
	return digest, n, nil
}
func (cp *copier) file(path, expected string) error {
	digest, size, err := stableCopy(path, filepath.Join(cp.root, strings.TrimPrefix(path, "/")), expected, &cp.c)
	if err != nil {
		return err
	}
	cp.objects[path] = objectIdentity{digest, size, cp.stage}
	return nil
}
func (cp *copier) bytesFile(path string, data []byte, expected string, mode fs.FileMode) error {
	digestRaw := sha256.Sum256(data)
	digest := hexDigest(digestRaw[:])
	if digest != expected {
		return fmt.Errorf("reviewed in-memory digest mismatch: %s", path)
	}
	destination := filepath.Join(cp.root, strings.TrimPrefix(path, "/"))
	if err := os.MkdirAll(filepath.Dir(destination), 0755); err != nil {
		return err
	}
	if err := os.WriteFile(destination, data, mode); err != nil {
		return err
	}
	n := int64(len(data))
	cp.c.FilesRead++
	cp.c.FilesCopied++
	cp.c.HashOperations++
	cp.c.BytesRead += n
	cp.c.BytesCopied += n
	cp.c.BytesHashed += n
	cp.objects[path] = objectIdentity{digest, n, cp.stage}
	return nil
}
func recordLine(hash io.Writer, relative, kind string, st *syscall.Stat_t, extra ...string) {
	fields := []string{relative, kind, strconv.FormatUint(uint64(st.Mode), 10), strconv.Itoa(int(st.Uid)), strconv.Itoa(int(st.Gid))}
	fields = append(fields, extra...)
	_, _ = hash.Write([]byte(strings.Join(fields, "\x00") + "\n"))
}
func (cp *copier) tree(source string, policy treePolicy) error {
	return cp.treeFrom(source, source, policy)
}
func (cp *copier) treeFrom(source, lexicalRoot string, policy treePolicy) error {
	destination := filepath.Join(cp.root, strings.TrimPrefix(lexicalRoot, "/"))
	paths := []string{source}
	err := filepath.WalkDir(source, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if path != source {
			paths = append(paths, path)
		}
		return nil
	})
	if err != nil {
		return err
	}
	sort.Slice(paths, func(i, j int) bool {
		li, _ := filepath.Rel(source, paths[i])
		lj, _ := filepath.Rel(source, paths[j])
		if li == "." {
			li = "."
		}
		if lj == "." {
			lj = "."
		}
		return filepath.ToSlash(li) < filepath.ToSlash(lj)
	})
	h := sha256.New()
	dirs, files, links := 0, 0, 0
	for _, path := range paths {
		rel, _ := filepath.Rel(source, path)
		rel = filepath.ToSlash(rel)
		if rel == "" {
			rel = "."
		}
		info, err := os.Lstat(path)
		if err != nil {
			return err
		}
		st := info.Sys().(*syscall.Stat_t)
		target := destination
		if rel != "." {
			target = filepath.Join(destination, filepath.FromSlash(rel))
		}
		switch st.Mode & syscall.S_IFMT {
		case syscall.S_IFDIR:
			dirs++
			if err := os.MkdirAll(target, info.Mode().Perm()); err != nil {
				return err
			}
			if err := os.Chown(target, int(st.Uid), int(st.Gid)); err != nil {
				return err
			}
			if err := syscall.Chmod(target, st.Mode&07777); err != nil {
				return err
			}
			recordLine(h, rel, "d", st)
		case syscall.S_IFREG:
			files++
			digest, size, err := stableCopy(path, target, "", &cp.c)
			if err != nil {
				return err
			}
			recordLine(h, rel, "f", st, strconv.FormatInt(size, 10), digest)
			lexical := lexicalRoot
			if rel != "." {
				lexical = filepath.Join(lexicalRoot, filepath.FromSlash(rel))
			}
			cp.objects[lexical] = objectIdentity{digest, size, cp.stage}
		case syscall.S_IFLNK:
			links++
			value, err := os.Readlink(path)
			if err != nil {
				return err
			}
			if err := os.MkdirAll(filepath.Dir(target), 0755); err != nil {
				return err
			}
			if err := os.Symlink(value, target); err != nil {
				return err
			}
			if err := os.Lchown(target, int(st.Uid), int(st.Gid)); err != nil {
				return err
			}
			recordLine(h, rel, "l", st, value)
		default:
			return fmt.Errorf("forbidden source type: %s", path)
		}
	}
	digest := hexDigest(h.Sum(nil))
	if policy.SHA256 != "" && (digest != policy.SHA256 || dirs != policy.Dirs || files != policy.Files || links != policy.Links) {
		return fmt.Errorf("reviewed tree mismatch: %s digest=%s counts=%d/%d/%d", source, digest, dirs, files, links)
	}
	return nil
}
func treeIdentity(root string) (treePolicy, error) {
	paths := []string{root}
	err := filepath.WalkDir(root, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if path != root {
			paths = append(paths, path)
		}
		return nil
	})
	if err != nil {
		return treePolicy{}, err
	}
	sort.Slice(paths, func(i, j int) bool {
		left, _ := filepath.Rel(root, paths[i])
		right, _ := filepath.Rel(root, paths[j])
		return filepath.ToSlash(left) < filepath.ToSlash(right)
	})
	h := sha256.New()
	dirs, files, links := 0, 0, 0
	for _, path := range paths {
		relative, _ := filepath.Rel(root, path)
		relative = filepath.ToSlash(relative)
		info, err := os.Lstat(path)
		if err != nil {
			return treePolicy{}, err
		}
		st := info.Sys().(*syscall.Stat_t)
		switch st.Mode & syscall.S_IFMT {
		case syscall.S_IFDIR:
			dirs++
			recordLine(h, relative, "d", st)
		case syscall.S_IFREG:
			data, digest, err := readStable(path)
			if err != nil {
				return treePolicy{}, err
			}
			files++
			recordLine(h, relative, "f", st, strconv.Itoa(len(data)), digest)
		case syscall.S_IFLNK:
			target, err := os.Readlink(path)
			if err != nil {
				return treePolicy{}, err
			}
			links++
			recordLine(h, relative, "l", st, target)
		default:
			return treePolicy{}, fmt.Errorf("forbidden candidate type: %s", path)
		}
	}
	return treePolicy{hexDigest(h.Sum(nil)), dirs, files, links}, nil
}
func setSymlink(root, path, target string) error {
	destination := filepath.Join(root, strings.TrimPrefix(path, "/"))
	if err := os.MkdirAll(filepath.Dir(destination), 0755); err != nil {
		return err
	}
	if info, err := os.Lstat(destination); err == nil {
		if info.Mode()&os.ModeSymlink == 0 {
			return fmt.Errorf("candidate link collides with non-symlink: %s", path)
		}
		if err := os.Remove(destination); err != nil {
			return err
		}
	} else if !os.IsNotExist(err) {
		return err
	}
	return os.Symlink(target, destination)
}
func copySymlink(root, path, target string) error {
	destination := filepath.Join(root, strings.TrimPrefix(path, "/"))
	if err := os.MkdirAll(filepath.Dir(destination), 0755); err != nil {
		return err
	}
	return os.Symlink(target, destination)
}
func normalizeAndApplyCandidateNginx(root string) error {
	for path, target := range candidateLinks {
		if !strings.HasPrefix(path, "/etc/nginx/") {
			continue
		}
		destination := filepath.Join(root, strings.TrimPrefix(path, "/"))
		if info, err := os.Lstat(destination); err == nil {
			if info.Mode()&os.ModeSymlink == 0 {
				return fmt.Errorf("candidate nginx entry non-symlink: %s", path)
			}
			actual, _ := os.Readlink(destination)
			if actual != target {
				return fmt.Errorf("candidate nginx link target unexpected: %s", path)
			}
			if err := os.Remove(destination); err != nil {
				return err
			}
		} else if !os.IsNotExist(err) {
			return err
		}
	}
	defaultPath := filepath.Join(root, "etc/nginx/sites-enabled/default")
	if info, err := os.Lstat(defaultPath); err == nil {
		if info.Mode()&os.ModeSymlink == 0 {
			return errors.New("nginx default is not a symlink")
		}
		if err := os.Remove(defaultPath); err != nil {
			return err
		}
	} else if !os.IsNotExist(err) {
		return err
	}
	if err := os.Symlink("/etc/nginx/sites-available/default", defaultPath); err != nil {
		return err
	}
	identity, err := treeIdentity(filepath.Join(root, "etc/nginx"))
	if err != nil {
		return err
	}
	if identity != s1TreePolicies["/etc/nginx"] {
		return fmt.Errorf("normalized package nginx tree mismatch: %#v", identity)
	}
	if err := os.Remove(defaultPath); err != nil {
		return err
	}
	for path, target := range candidateLinks {
		if strings.HasPrefix(path, "/etc/nginx/") {
			if err := setSymlink(root, path, target); err != nil {
				return err
			}
		}
	}
	return nil
}
func candidatePathValid(path string) bool {
	clean := filepath.Clean(path)
	if clean != path || !filepath.IsAbs(path) || path == deploymentsRoot {
		return false
	}
	relative, err := filepath.Rel(deploymentsRoot, path)
	return err == nil && relative != "." && !strings.HasPrefix(relative, ".."+string(filepath.Separator)) && !strings.ContainsAny(relative, "\x00\n\r")
}
func strictJSONBytes(data []byte, target any) error {
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(target); err != nil {
		return err
	}
	var trailing any
	if err := decoder.Decode(&trailing); err != io.EOF {
		return errors.New("JSON trailing data")
	}
	return nil
}
func copyCandidateClosure(cp *copier, candidate, expectedLock string) (map[string]string, error) {
	if !candidatePathValid(candidate) || len(expectedLock) != 64 {
		return nil, errors.New("candidate selector invalid")
	}
	sourceRoot := hostPath(candidate)
	expectedFiles := append(append([]string{}, candidateBundleFiles...), "deployment.lock.json")
	sort.Strings(expectedFiles)
	actualFiles := []string{}
	actualDirs := []string{}
	err := filepath.WalkDir(sourceRoot, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if path == sourceRoot {
			return nil
		}
		relative, err := filepath.Rel(sourceRoot, path)
		if err != nil {
			return err
		}
		info, err := os.Lstat(path)
		if err != nil {
			return err
		}
		st := info.Sys().(*syscall.Stat_t)
		if st.Uid != 0 || st.Gid != 0 || info.Mode().Perm()&0022 != 0 {
			return fmt.Errorf("candidate metadata unsafe: %s", relative)
		}
		if entry.IsDir() {
			actualDirs = append(actualDirs, filepath.ToSlash(relative))
			return nil
		}
		if info.Mode().IsRegular() {
			actualFiles = append(actualFiles, filepath.ToSlash(relative))
			return nil
		}
		return fmt.Errorf("candidate object type forbidden: %s", relative)
	})
	if err != nil {
		return nil, err
	}
	sort.Strings(actualFiles)
	if strings.Join(actualFiles, "\x00") != strings.Join(expectedFiles, "\x00") {
		return nil, errors.New("candidate file inventory mismatch")
	}
	expectedDirs := []string{"firewall", "logrotate", "nginx", "systemd"}
	sort.Strings(actualDirs)
	if strings.Join(actualDirs, "\x00") != strings.Join(expectedDirs, "\x00") {
		return nil, errors.New("candidate directory inventory mismatch")
	}
	lockData, lockDigest, err := readStable(filepath.Join(sourceRoot, "deployment.lock.json"))
	if err != nil {
		return nil, err
	}
	if lockDigest != expectedLock {
		return nil, errors.New("candidate lock identity changed")
	}
	var lock deploymentLock
	if err := strictJSONBytes(lockData, &lock); err != nil {
		return nil, err
	}
	if lock.SchemaVersion != "thebitlab.pilot-deployment-lock.v1" || len(lock.DeploymentID) == 0 || len(lock.ReleaseCommit) != 40 || len(lock.Files) != len(candidateBundleFiles) {
		return nil, errors.New("candidate lock contract invalid")
	}
	for _, relative := range candidateBundleFiles {
		expected, ok := lock.Files[relative]
		if !ok || len(expected) != 64 {
			return nil, fmt.Errorf("candidate lock file invalid: %s", relative)
		}
		source := filepath.Join(sourceRoot, filepath.FromSlash(relative))
		lexical := filepath.Join(candidate, filepath.FromSlash(relative))
		destination := filepath.Join(cp.root, strings.TrimPrefix(lexical, "/"))
		digest, size, err := stableCopy(source, destination, expected, &cp.c)
		if err != nil {
			return nil, err
		}
		cp.objects[lexical] = objectIdentity{digest, size, cp.stage}
	}
	lockDestination := filepath.Join(cp.root, strings.TrimPrefix(filepath.Join(candidate, "deployment.lock.json"), "/"))
	digest, size, err := stableCopy(filepath.Join(sourceRoot, "deployment.lock.json"), lockDestination, expectedLock, &cp.c)
	if err != nil {
		return nil, err
	}
	cp.objects[filepath.Join(candidate, "deployment.lock.json")] = objectIdentity{digest, size, cp.stage}
	manifestData, _, err := readStable(filepath.Join(sourceRoot, "manifest.normalized.json"))
	if err != nil {
		return nil, err
	}
	var selected candidateManifest
	if err := json.Unmarshal(manifestData, &selected); err != nil {
		return nil, err
	}
	for _, lexical := range []string{selected.Origin.TLSCertificateFile, selected.Origin.TLSPrivateKeyFile} {
		if filepath.Clean(lexical) != lexical || !filepath.IsAbs(lexical) || lexical == "/" {
			return nil, errors.New("candidate TLS path invalid")
		}
		if _, exists := cp.objects[lexical]; exists {
			return nil, fmt.Errorf("candidate TLS path collision: %s", lexical)
		}
		digest, size, err := stableCopy(hostPath(lexical), filepath.Join(cp.root, strings.TrimPrefix(lexical, "/")), "", &cp.c)
		if err != nil {
			return nil, err
		}
		cp.objects[lexical] = objectIdentity{digest, size, cp.stage}
	}
	links := map[string]string{"/etc/thebitlab/current": candidate}
	if err := setSymlink(cp.root, "/etc/thebitlab/current", candidate); err != nil {
		return nil, err
	}
	for path, target := range candidateLinks {
		if err := setSymlink(cp.root, path, target); err != nil {
			return nil, err
		}
		links[path] = target
	}
	return links, nil
}
func readStable(path string) ([]byte, string, error) { return readStableMode(path, true) }
func readStableMode(path string, noFollow bool) ([]byte, string, error) {
	flags := syscall.O_RDONLY | syscall.O_CLOEXEC
	if noFollow {
		flags |= syscall.O_NOFOLLOW
	}
	fd, err := syscall.Open(path, flags, 0)
	if err != nil {
		return nil, "", err
	}
	f := os.NewFile(uintptr(fd), path)
	defer f.Close()
	var a, b syscall.Stat_t
	if err := syscall.Fstat(fd, &a); err != nil {
		return nil, "", err
	}
	if a.Mode&syscall.S_IFMT != syscall.S_IFREG {
		return nil, "", fmt.Errorf("stable source is not regular: %s", path)
	}
	data, err := io.ReadAll(f)
	if err != nil {
		return nil, "", err
	}
	if err := syscall.Fstat(fd, &b); err != nil {
		return nil, "", err
	}
	if a.Dev != b.Dev || a.Ino != b.Ino || a.Size != b.Size || a.Mtim != b.Mtim || a.Ctim != b.Ctim {
		return nil, "", fmt.Errorf("file unstable: %s", path)
	}
	sum := sha256.Sum256(data)
	return data, hexDigest(sum[:]), nil
}
func rejectHostHwcaps() error {
	for _, base := range []string{"/usr/lib/x86_64-linux-gnu", "/usr/lib/x86_64-linux-gnu/systemd", "/usr/lib"} {
		for _, level := range []string{"x86-64-v2", "x86-64-v3", "x86-64-v4"} {
			p := filepath.Join(base, "glibc-hwcaps", level)
			entries, err := os.ReadDir(p)
			if err == nil && len(entries) > 0 {
				return fmt.Errorf("EXPECTED_ABSENT hwcaps candidate present: %s", p)
			}
			if err != nil && !os.IsNotExist(err) {
				return err
			}
		}
	}
	return nil
}
func transactionSource(base, token string) string { return base + ":" + token }
func mountTmpfs(source, target, size string, rootMode fs.FileMode) error {
	if rootMode != 0700 && rootMode != 0755 {
		return errors.New("tmpfs root mode fuori policy")
	}
	if err := ensureDir(target, 0700); err != nil {
		return err
	}
	return syscall.Mount(
		source, target, "tmpfs", syscall.MS_NOSUID|syscall.MS_NODEV,
		fmt.Sprintf("mode=%04o,size=%s", rootMode.Perm(), size),
	)
}
func remountRO(target string) error {
	return syscall.Mount("", target, "", syscall.MS_REMOUNT|syscall.MS_RDONLY|syscall.MS_NOSUID|syscall.MS_NODEV, "")
}
func randomToken() string {
	data := make([]byte, 16)
	f, _ := os.Open("/dev/urandom")
	if f != nil {
		_, _ = io.ReadFull(f, data)
		_ = f.Close()
	}
	return fmt.Sprintf("%d-%s", os.Getpid(), hex.EncodeToString(data))
}
func mountHas(source, mountpoint string, ro bool) bool {
	identity, err := topMount(mountpoint)
	if err != nil || identity.Source != source {
		return false
	}
	return !ro || containsString(identity.Options, "ro")
}
func containsString(values []string, wanted string) bool {
	for _, value := range values {
		if value == wanted {
			return true
		}
	}
	return false
}
func topMount(mountpoint string) (mountIdentity, error) {
	data, err := os.ReadFile("/proc/self/mountinfo")
	if err != nil {
		return mountIdentity{}, err
	}
	var found *mountIdentity
	for _, line := range strings.Split(string(data), "\n") {
		parts := strings.SplitN(line, " - ", 2)
		if len(parts) != 2 {
			continue
		}
		left := strings.Fields(parts[0])
		right := strings.Fields(parts[1])
		if len(left) < 6 || len(right) < 3 || left[4] != mountpoint {
			continue
		}
		mountID, e1 := strconv.Atoi(left[0])
		parentID, e2 := strconv.Atoi(left[1])
		if e1 != nil || e2 != nil {
			return mountIdentity{}, errors.New("mountinfo identity invalid")
		}
		candidate := mountIdentity{mountID, parentID, left[2], left[3], left[4], strings.Split(left[5], ","), right[0], right[1], strings.Split(right[2], ",")}
		found = &candidate
	}
	if found == nil {
		return mountIdentity{}, fmt.Errorf("mount witness absent: %s", mountpoint)
	}
	return *found, nil
}
func sameMount(a, b mountIdentity) bool {
	return a.MountID == b.MountID && a.ParentID == b.ParentID && a.MajorMinor == b.MajorMinor && a.Root == b.Root && a.MountPoint == b.MountPoint && a.Filesystem == b.Filesystem && a.Source == b.Source && strings.Join(a.Options, "\x00") == strings.Join(b.Options, "\x00") && strings.Join(a.SuperOptions, "\x00") == strings.Join(b.SuperOptions, "\x00")
}
func strictJSON(path string, target any) ([]byte, error) {
	data, digest, err := readStable(path)
	if err != nil {
		return nil, err
	}
	_ = digest
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(target); err != nil {
		return nil, err
	}
	var trailing any
	if err := decoder.Decode(&trailing); err != io.EOF {
		return nil, errors.New("JSON trailing data")
	}
	return data, nil
}
func fileSHA(path string) (string, error) { _, digest, err := readStable(path); return digest, err }
func privateFault(point string) {
	if os.Getenv("THEBITLAB_EPHEMERAL_CRASH_TEST") != "1" || os.Getenv("THEBITLAB_PRIVATE_RUNTIME_CRASH_POINT") != point {
		return
	}
	data, err := os.ReadFile("/run/thebitlab-ephemeral-activation-test")
	if err == nil && string(data) == "ephemeral-only\n" {
		os.Exit(97)
	}
}
func validatePinAndCopyToolchain(cp *copier) (pinDocument, error) {
	var pin pinDocument
	pinData, pinDigest, err := readStable(pinHost)
	if err != nil {
		return pin, err
	}
	if err = json.Unmarshal(pinData, &pin); err != nil {
		return pin, err
	}
	if pin.SchemaVersion != "thebitlab.private-runtime-pin.v1" || len(pin.LauncherSHA256) != 64 || len(pin.ToolchainManifestSHA256) != 64 {
		return pin, errors.New("private POC pin invalid")
	}
	selfData, selfDigest, err := readStableMode("/proc/self/exe", false)
	if err != nil {
		return pin, err
	}
	if selfDigest != pin.LauncherSHA256 {
		return pin, errors.New("static POC binary differs from external pin")
	}
	if err := cp.bytesFile("/usr/lib/thebitlab/private-runtime-broker", selfData, selfDigest, 0755); err != nil {
		return pin, err
	}
	cp.objects[launcherHost] = objectIdentity{selfDigest, int64(len(selfData)), cp.stage}
	toolRoot := filepath.Join("/usr/lib/thebitlab/pilot-tools", pin.ToolchainID)
	manifestPath := filepath.Join(toolRoot, "pilot-toolchain-manifest.json")
	manifestData, manifestDigest, err := readStable(manifestPath)
	if err != nil {
		return pin, err
	}
	if manifestDigest != pin.ToolchainManifestSHA256 {
		return pin, errors.New("toolchain manifest differs from pin")
	}
	var document toolchainDocument
	if err := json.Unmarshal(manifestData, &document); err != nil {
		return pin, err
	}
	if document.SchemaVersion != "thebitlab.pilot-toolchain.v1" || document.ToolchainID != pin.ToolchainID || document.ReleaseCommit != pin.ReleaseCommit {
		return pin, errors.New("toolchain identity mismatch")
	}
	manifestLexical := filepath.Join("/usr/lib/thebitlab/pilot-tools", pin.ToolchainID, "pilot-toolchain-manifest.json")
	if err := cp.bytesFile(manifestLexical, manifestData, manifestDigest, 0644); err != nil {
		return pin, err
	}
	names := make([]string, 0, len(document.Files))
	for name := range document.Files {
		if filepath.IsAbs(name) || strings.Contains(name, "..") || strings.ContainsAny(name, "\x00\n\r") {
			return pin, errors.New("toolchain path invalid")
		}
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		if err := cp.file(filepath.Join(toolRoot, filepath.FromSlash(name)), document.Files[name]); err != nil {
			return pin, err
		}
	}
	if err := cp.bytesFile(pinHost, pinData, pinDigest, 0644); err != nil {
		return pin, err
	}
	return pin, nil
}
func makeSkeleton(root string) error {
	for _, p := range []string{"etc/ssl", "usr/bin", "usr/sbin", "usr/lib", "usr/local/lib", "usr/share", "var/log/nginx", "var/lib/nginx", "run/thebitlab/pilot-private-runtime/control", "proc", "sys", "dev", "tmp", ".oldroot"} {
		if err := os.MkdirAll(filepath.Join(root, p), 0755); err != nil {
			return err
		}
	}
	if err := os.WriteFile(filepath.Join(root, "dev/null"), nil, 0600); err != nil {
		return err
	}
	for path, target := range map[string]string{"bin": "usr/bin", "sbin": "usr/sbin", "lib": "usr/lib", "lib64": "usr/lib64"} {
		if err := os.Symlink(target, filepath.Join(root, path)); err != nil {
			return err
		}
	}
	return nil
}
func buildProductionS0() (token string, doc manifest, result error) {
	if os.Geteuid() != 0 {
		return "", doc, errors.New("private runtime requires root")
	}
	if filepath.Clean(os.Args[0]) != launcherHost {
		return "", doc, errors.New("private runtime requires canonical static launcher")
	}
	if _, err := os.Lstat(stateHost); err == nil {
		return "", doc, errors.New("private runtime state already exists")
	}
	if err := rejectHostHwcaps(); err != nil {
		return "", doc, err
	}
	start := time.Now()
	cpuStart := cpuSeconds()
	token = randomToken()
	if err := ensureDir(runtimeHost, 0700); err != nil {
		return "", doc, err
	}
	if err := ensureDir(controlHost, 0700); err != nil {
		return "", doc, err
	}
	if err := writeJSON(stateHost, map[string]any{"schema": stateSchema, "token": token, "phase": "planned"}); err != nil {
		return "", doc, err
	}
	source := transactionSource(s0Source, token)
	if err := mountTmpfs(source, s0Host, "256m", 0755); err != nil {
		return "", doc, err
	}
	defer func() {
		if result != nil {
			_ = syscall.Unmount(s0Host, 0)
		}
	}()
	witness, err := topMount(s0Host)
	if err != nil {
		return "", doc, err
	}
	if err := writeJSON(stateHost, map[string]any{"schema": stateSchema, "token": token, "phase": "building-s0", "mounts": map[string]mountIdentity{"s0": witness}}); err != nil {
		return "", doc, err
	}
	privateFault("s0_during_construction")
	cp := copier{s0Host, counters{}, map[string]objectIdentity{}, "S0"}
	if err := makeSkeleton(s0Host); err != nil {
		return "", doc, err
	}
	paths := make([]string, 0, len(treePolicies))
	for p := range treePolicies {
		paths = append(paths, p)
	}
	sort.Strings(paths)
	for _, p := range paths {
		if err := cp.tree(p, treePolicies[p]); err != nil {
			return "", doc, err
		}
	}
	files := make([]string, 0, len(s0Files))
	for p := range s0Files {
		files = append(files, p)
	}
	sort.Strings(files)
	for _, p := range files {
		if err := cp.file(p, s0Files[p]); err != nil {
			return "", doc, err
		}
	}
	if err := copySymlink(s0Host, "/usr/bin/python3", "python3.12"); err != nil {
		return "", doc, err
	}
	if err := os.MkdirAll(filepath.Join(s0Host, "usr/lib64"), 0755); err != nil {
		return "", doc, err
	}
	if err := os.Symlink("../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2", filepath.Join(s0Host, "usr/lib64/ld-linux-x86-64.so.2")); err != nil {
		return "", doc, err
	}
	pin, err := validatePinAndCopyToolchain(&cp)
	if err != nil {
		return "", doc, err
	}
	m := metrics{"S0", time.Since(start).Seconds(), cpuSeconds() - cpuStart, cp.c, len(cp.objects), 0, 0, 0, "/lib64/ld-linux-x86-64.so.2", "reviewed Noble stdlib + dist-packages + native tree", 0, 0}
	self := cp.objects[launcherHost].SHA256
	doc = manifest{Schema: manifestSchema, Token: token, MountSource: source, Root: s0Host, Objects: cp.objects, Metrics: m, SelfSHA256: self, ToolchainID: pin.ToolchainID, ToolchainManifestSHA256: pin.ToolchainManifestSHA256}
	if err := writeJSON(filepath.Join(s0Host, ".thebitlab-s0-manifest.json"), doc); err != nil {
		return "", doc, err
	}
	if err := writeJSON(stateHost, map[string]any{"schema": stateSchema, "token": token, "phase": "building-s0", "s0_manifest_sha256": hashJSON(doc), "mounts": map[string]mountIdentity{"s0": witness}}); err != nil {
		return "", doc, err
	}
	if err := remountRO(s0Host); err != nil {
		return "", doc, err
	}
	if !mountHas(source, s0Host, true) {
		return "", doc, errors.New("S0 mount is not kernel-witnessed RO tmpfs")
	}
	witness, err = topMount(s0Host)
	if err != nil {
		return "", doc, err
	}
	if err := writeJSON(stateHost, map[string]any{"schema": stateSchema, "token": token, "phase": "s0-sealed", "s0_manifest_sha256": hashJSON(doc), "mounts": map[string]mountIdentity{"s0": witness}}); err != nil {
		return "", doc, err
	}
	privateFault("s0_after_seal")
	return token, doc, nil
}

func stage0() (result error) {
	if os.Geteuid() != 0 {
		return errors.New("private runtime POC requires root")
	}
	if filepath.Clean(os.Args[0]) != launcherHost {
		return errors.New("private POC requires canonical static launcher")
	}
	probeMode := len(os.Args) > 1 && os.Args[1] == "poc-probe"
	if _, err := os.Lstat(stateHost); err == nil {
		return errors.New("private POC state already exists")
	}
	if err := rejectHostHwcaps(); err != nil {
		return err
	}
	start := time.Now()
	cpuStart := cpuSeconds()
	token := randomToken()
	if err := ensureDir(runtimeHost, 0700); err != nil {
		return err
	}
	if err := ensureDir(controlHost, 0700); err != nil {
		return err
	}
	if err := mountTmpfs(s0Source, s0Host, "256m", 0755); err != nil {
		return err
	}
	defer func() {
		if result != nil {
			_ = syscall.Unmount(s0Host, syscall.MNT_DETACH)
		}
	}()
	cp := copier{s0Host, counters{}, map[string]objectIdentity{}, "S0"}
	if err := makeSkeleton(s0Host); err != nil {
		return err
	}
	paths := make([]string, 0, len(treePolicies))
	for p := range treePolicies {
		paths = append(paths, p)
	}
	sort.Strings(paths)
	for _, p := range paths {
		if err := cp.tree(p, treePolicies[p]); err != nil {
			return err
		}
	}
	files := make([]string, 0, len(s0Files))
	for p := range s0Files {
		files = append(files, p)
	}
	sort.Strings(files)
	for _, p := range files {
		if err := cp.file(p, s0Files[p]); err != nil {
			return err
		}
	}
	if err := copySymlink(s0Host, "/usr/bin/python3", "python3.12"); err != nil {
		return err
	}
	// /lib64 -> usr/lib64 already exists; provide the reviewed PT_INTERP spelling below it.
	if err := os.MkdirAll(filepath.Join(s0Host, "usr/lib64"), 0755); err != nil {
		return err
	}
	if err := os.Symlink("../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2", filepath.Join(s0Host, "usr/lib64/ld-linux-x86-64.so.2")); err != nil {
		return err
	}
	pin, err := validatePinAndCopyToolchain(&cp)
	if err != nil {
		return err
	}
	wall := time.Since(start).Seconds()
	m := metrics{"S0", wall, cpuSeconds() - cpuStart, cp.c, len(cp.objects), 0, 0, 0, "/lib64/ld-linux-x86-64.so.2", "reviewed Noble stdlib + dist-packages + native tree", 0, 0}
	self := cp.objects[launcherHost].SHA256
	doc := manifest{Schema: manifestSchema, Token: token, MountSource: s0Source, Root: s0Host, Objects: cp.objects, Metrics: m, SelfSHA256: self, ToolchainID: pin.ToolchainID, ToolchainManifestSHA256: pin.ToolchainManifestSHA256}
	if err := writeJSON(filepath.Join(s0Host, ".thebitlab-s0-manifest.json"), doc); err != nil {
		return err
	}
	if err := writeJSON(stateHost, map[string]any{"schema": stateSchema, "token": token, "s0_source": s0Source, "s0_manifest_sha256": hashJSON(doc), "toolchain_id": pin.ToolchainID}); err != nil {
		return err
	}
	if err := remountRO(s0Host); err != nil {
		return err
	}
	if !mountHas(s0Source, s0Host, true) {
		return errors.New("S0 mount is not kernel-witnessed RO tmpfs")
	}
	if !probeMode {
		if _, err := syscall.ForkExec("/proc/self/exe", []string{launcherHost, "poc-stage1-server", token}, &syscall.ProcAttr{Dir: "/", Env: []string{}, Files: []uintptr{0, 1, 2}}); err != nil {
			return fmt.Errorf("static stage1 server start failed: %w", err)
		}
	}
	// stage0 is also a one-way helper: after a successful unshare it must stay
	// pinned until Exec or fail-closed process exit.
	runtime.LockOSThread()
	if err := syscall.Unshare(syscall.CLONE_NEWNS); err != nil {
		runtime.UnlockOSThread()
		return err
	}
	if err := syscall.Mount("", "/", "", syscall.MS_REC|syscall.MS_PRIVATE, ""); err != nil {
		return err
	}
	// Only proc, null and a data-only control mount cross into the private root.
	if err := syscall.Mount("proc", filepath.Join(s0Host, "proc"), "proc", syscall.MS_NOSUID|syscall.MS_NODEV|syscall.MS_NOEXEC, ""); err != nil {
		return err
	}
	if err := syscall.Mount(controlHost, filepath.Join(s0Host, "run/thebitlab-private-runtime-poc/control"), "", syscall.MS_BIND, ""); err != nil {
		return err
	}
	if err := syscall.Mount("/dev/null", filepath.Join(s0Host, "dev/null"), "", syscall.MS_BIND, ""); err != nil {
		return err
	}
	if err := syscall.Chdir(s0Host); err != nil {
		return err
	}
	if err := syscall.PivotRoot(".", ".oldroot"); err != nil {
		return err
	}
	if err := syscall.Chdir("/"); err != nil {
		return err
	}
	if err := syscall.Unmount("/.oldroot", syscall.MNT_DETACH); err != nil {
		return err
	}
	closeExtraFDs()
	toolRoot := filepath.Join("/usr/lib/thebitlab/pilot-tools", pin.ToolchainID)
	code := `import json,os,pathlib,subprocess,sys,time
control=pathlib.Path('/run/thebitlab-private-runtime-poc/control')
control.joinpath('s0-python-ready').write_text(json.dumps({'pid':os.getpid(),'exe':os.readlink('/proc/self/exe'),'maps':sorted({line.split(maxsplit=5)[-1] for line in pathlib.Path('/proc/self/maps').read_text().splitlines() if 'x' in line.split()[1] and len(line.split(maxsplit=5))==6 and line.split(maxsplit=5)[-1].startswith('/')})})+'\n')
if sys.argv[3]=='probe':
 import ssl,ctypes
 control.joinpath('probe-ok').write_text(json.dumps({'ssl':ssl.__file__})+'\n')
 raise SystemExit(0)
while not control.joinpath('attack-complete').exists(): time.sleep(.01)
import ssl,ctypes
sys.path.insert(0,sys.argv[1])
import scripts.nginx_config_ast
broker='/usr/lib/thebitlab/private-runtime-broker'
r=subprocess.run([broker,'poc-stage1'],env={'THEBITLAB_PRIVATE_POC_TOKEN':sys.argv[2]},text=True,capture_output=True)
control.joinpath('broker-result').write_text(json.dumps({'rc':r.returncode,'stdout':r.stdout,'stderr':r.stderr})+'\n')
if r.returncode: raise SystemExit(r.returncode)
control.joinpath('s0-late-import-ok').write_text(json.dumps({'ssl':ssl.__file__,'module':scripts.nginx_config_ast.__file__})+'\n')
while not control.joinpath('finish').exists(): time.sleep(.01)
`
	loader := "/lib64/ld-linux-x86-64.so.2"
	mode := "full"
	if probeMode {
		mode = "probe"
	}
	args := []string{loader, "--inhibit-cache", "--library-path", "/usr/lib/x86_64-linux-gnu", "/usr/bin/python3.12", "-I", "-B", "-c", code, toolRoot, token, mode}
	env := []string{"HOME=/root", "LANG=C", "LC_ALL=C", "PATH=/usr/sbin:/usr/bin:/sbin:/bin"}
	return syscall.Exec(loader, args, env)
}
func closeExtraFDs() {
	entries, _ := os.ReadDir("/proc/self/fd")
	for _, e := range entries {
		n, err := strconv.Atoi(e.Name())
		if err == nil && n > 2 {
			_ = syscall.Close(n)
		}
	}
}
func hashJSON(value any) string {
	data, _ := json.Marshal(value)
	sum := sha256.Sum256(data)
	return hexDigest(sum[:])
}
func hostPath(path string) string { return "/proc/1/root" + path }
func setnsPID1() error {
	fd, err := syscall.Open("/proc/1/ns/mnt", syscall.O_RDONLY|syscall.O_CLOEXEC, 0)
	if err != nil {
		return err
	}
	defer syscall.Close(fd)
	_, _, errno := syscall.Syscall(308, uintptr(fd), uintptr(syscall.CLONE_NEWNS), 0)
	if errno != 0 {
		return errno
	}
	return nil
}
func loadS0(token string) (manifest, error) {
	var doc manifest
	data, err := os.ReadFile(hostPath(s0Host + "/.thebitlab-s0-manifest.json"))
	if err != nil {
		return doc, err
	}
	if err := json.Unmarshal(data, &doc); err != nil {
		return doc, err
	}
	if doc.Token != token || doc.MountSource != transactionSource(s0Source, token) || doc.Root != s0Host {
		return doc, errors.New("S0 manifest identity mismatch")
	}
	if !mountHas(transactionSource(s0Source, token), s0Host, true) {
		return doc, errors.New("S0 kernel mount witness mismatch")
	}
	var state map[string]any
	raw, err := os.ReadFile(hostPath(stateHost))
	if err != nil {
		return doc, err
	}
	if json.Unmarshal(raw, &state) != nil || state["token"] != token || state["s0_manifest_sha256"] != hashJSON(doc) {
		return doc, errors.New("S0 state is not authority-bound")
	}
	return doc, nil
}
func n2UnitBytes() []byte {
	broker := s0Host + "/usr/lib/thebitlab/private-runtime-broker"
	return []byte("# Exact TheBitLab N2 private-runtime POC unit; issue 704\n[Unit]\nDescription=TheBitLab private runtime N2 nginx POC\nAfter=network.target\n[Service]\nType=forking\nPIDFile=" + runtimeHost + "/runtime/run/nginx.pid\nExecStartPre=" + broker + " poc-private-exec /usr/sbin/nginx -t -q -g 'daemon on; master_process on;'\nExecStartPre=" + broker + " poc-start-barrier\nExecStart=" + broker + " poc-private-exec /usr/sbin/nginx -g 'daemon on; master_process on;'\nExecReload=" + broker + " poc-private-exec /usr/sbin/nginx -g 'daemon on; master_process on;' -s reload\nExecStop=-" + broker + " poc-private-exec /usr/sbin/start-stop-daemon --quiet --stop --retry QUIT/5 --pidfile /run/nginx.pid\nTimeoutStopSec=5\nKillMode=mixed\n")
}
func stage1Build(token string) (result error) {
	if os.Geteuid() != 0 {
		return errors.New("stage1 broker requires root")
	}
	if token == "" {
		return errors.New("transaction selector absent")
	}
	s0, err := loadS0(token)
	if err != nil {
		return err
	}
	start := time.Now()
	cpuStart := cpuSeconds()
	s1Target := hostPath(s1Host)
	if err := mountTmpfs(s1Source, s1Target, "32m", 0755); err != nil {
		return err
	}
	defer func() {
		if result != nil {
			_ = syscall.Unmount(s1Target, syscall.MNT_DETACH)
		}
	}()
	cp := copier{s1Target, counters{}, map[string]objectIdentity{}, "S1"}
	for _, p := range []string{"etc", "usr/lib", "usr/share", "usr/sbin", "var/log/nginx", "var/lib/nginx", "run", "tmp"} {
		if err := os.MkdirAll(filepath.Join(s1Target, p), 0755); err != nil {
			return err
		}
	}
	overlap, overlapBytes := 0, int64(0)
	paths := make([]string, 0, len(s1TreePolicies))
	for p := range s1TreePolicies {
		paths = append(paths, p)
	}
	sort.Strings(paths)
	for _, p := range paths {
		if err := cp.treeFrom(hostPath(p), p, s1TreePolicies[p]); err != nil {
			return err
		}
	}
	for lex, id := range cp.objects {
		if existing, ok := s0.Objects[lex]; ok {
			overlap++
			overlapBytes += id.Size
			if existing.SHA256 != id.SHA256 {
				return fmt.Errorf("same path has different identity: %s", lex)
			}
			return fmt.Errorf("S1 policy duplicates S0 identity: %s", lex)
		}
	}
	filePaths := make([]string, 0, len(s1Files))
	for p := range s1Files {
		filePaths = append(filePaths, p)
	}
	sort.Strings(filePaths)
	for _, p := range filePaths {
		if existing, ok := s0.Objects[p]; ok {
			overlap++
			overlapBytes += existing.Size
			continue
		}
		digest, size, err := stableCopy(hostPath(p), filepath.Join(s1Target, strings.TrimPrefix(p, "/")), s1Files[p], &cp.c)
		if err != nil {
			return err
		}
		cp.objects[p] = objectIdentity{digest, size, "S1"}
	}
	n2Source := filepath.Join(s1Target, "manager/thebitlab-private-n2-poc.service")
	if err := os.MkdirAll(filepath.Dir(n2Source), 0700); err != nil {
		return err
	}
	if err := os.WriteFile(n2Source, n2UnitBytes(), 0644); err != nil {
		return err
	}
	m := metrics{"S1", time.Since(start).Seconds(), cpuSeconds() - cpuStart, cp.c, len(cp.objects), overlap, overlapBytes, 0, "", "", 0, 0}
	doc := manifest{Schema: manifestSchema, Token: token, MountSource: s1Source, Root: s1Host, Objects: cp.objects, Metrics: m, SelfSHA256: s0.SelfSHA256}
	if err := writeJSON(filepath.Join(s1Target, ".thebitlab-s1-manifest.json"), doc); err != nil {
		return err
	}
	if err := remountRO(s1Target); err != nil {
		return err
	}
	if !mountHas(s1Source, s1Host, true) {
		return errors.New("S1 mount is not kernel-witnessed RO tmpfs")
	}
	compositionStart := time.Now()
	merged := hostPath(mergedHost)
	if err := ensureDir(merged, 0700); err != nil {
		return err
	}
	options := "lowerdir=" + hostPath(s1Host) + ":" + hostPath(s0Host)
	if err := syscall.Mount("overlay", merged, "overlay", syscall.MS_RDONLY|syscall.MS_NOSUID|syscall.MS_NODEV, options); err != nil {
		return fmt.Errorf("read-only multi-lower overlay rejected: %w", err)
	}
	m.CompositionSeconds = time.Since(compositionStart).Seconds()
	managerStart := time.Now()
	runtime := hostPath(runtimeHost + "/runtime")
	for _, p := range []string{"run", "log/nginx", "cache/nginx"} {
		if err := os.MkdirAll(filepath.Join(runtime, p), 0755); err != nil {
			return err
		}
	}
	drop := hostPath(managerDrop)
	if entries, err := os.ReadDir(drop); err == nil && len(entries) != 0 {
		return errors.New("manager drop-in directory has unexpected siblings")
	}
	if err := mountTmpfs(managerSource, drop, "1m", 0700); err != nil {
		return err
	}
	content := []byte("# Exact TheBitLab private-runtime POC drop-in; issue 704\n[Service]\nRootDirectory=" + mergedHost + "\nPIDFile=" + runtimeHost + "/runtime/run/nginx.pid\nBindPaths=" + runtimeHost + "/runtime/run:/run\nBindPaths=" + runtimeHost + "/control:/run/thebitlab-private-runtime-poc/control\nBindPaths=" + runtimeHost + "/runtime/log/nginx:/var/log/nginx\nBindPaths=" + runtimeHost + "/runtime/cache/nginx:/var/lib/nginx\nExecStartPre=/usr/lib/thebitlab/private-runtime-broker poc-start-barrier\n")
	if err := os.WriteFile(filepath.Join(drop, "70-thebitlab-private-runtime.conf"), content, 0644); err != nil {
		return err
	}
	if err := remountRO(drop); err != nil {
		return err
	}
	n2Target := hostPath("/run/systemd/system/thebitlab-private-n2-poc.service")
	if err := os.WriteFile(n2Target, nil, 0644); err != nil {
		return err
	}
	if err := syscall.Mount(hostPath(s1Host+"/manager/thebitlab-private-n2-poc.service"), n2Target, "", syscall.MS_BIND, ""); err != nil {
		return err
	}
	if err := syscall.Mount("", n2Target, "", syscall.MS_BIND|syscall.MS_REMOUNT|syscall.MS_RDONLY, ""); err != nil {
		return err
	}
	m.ManagerFenceSeconds = time.Since(managerStart).Seconds()
	doc.Metrics = m
	if err := writeJSON(hostPath(controlHost+"/s1-metrics.json"), doc); err != nil {
		return err
	}
	return nil
}
func productionDropin(token string) []byte {
	broker := s0Host + "/usr/lib/thebitlab/private-runtime-broker"
	prefix := broker + " production-private-exec " + token + " "
	return []byte("# TheBitLab immutable private runtime; issue 704\n[Service]\nType=forking\nPIDFile=" + runtimeHost + "/runtime/run/nginx.pid\nRootDirectory=\nRootDirectoryStartOnly=no\nExecStartPre=\nExecStartPre=" + prefix + "/usr/sbin/nginx -t -q -g 'daemon on; master_process on;'\nExecStart=\nExecStart=" + prefix + "/usr/sbin/nginx -g 'daemon on; master_process on;'\nExecReload=\nExecReload=" + prefix + "/usr/sbin/nginx -g 'daemon on; master_process on;' -s reload\nExecStop=\nExecStop=-" + prefix + "/usr/sbin/start-stop-daemon --quiet --stop --retry QUIT/5 --pidfile /run/nginx.pid\nTimeoutStopSec=5\nKillMode=mixed\n")
}

func productionStage1Build(token string, s0 manifest, candidate, candidateLock string) (doc manifest, result error) {
	if os.Geteuid() != 0 {
		return doc, errors.New("S1 broker requires root")
	}
	if token == "" {
		return doc, errors.New("transaction selector absent")
	}
	loaded, err := loadS0(token)
	if err != nil {
		return doc, err
	}
	if hashJSON(loaded) != hashJSON(s0) {
		return doc, errors.New("S0 caller/server identity mismatch")
	}
	start := time.Now()
	cpuStart := cpuSeconds()
	s1Target := hostPath(s1Host)
	s1MountSource := transactionSource(s1Source, token)
	if err := mountTmpfs(s1MountSource, s1Target, "32m", 0755); err != nil {
		return doc, err
	}
	defer func() {
		if result != nil {
			_ = syscall.Unmount(s1Target, 0)
		}
	}()
	privateFault("s1_during_construction")
	cp := copier{s1Target, counters{}, map[string]objectIdentity{}, "S1"}
	for _, p := range []string{"etc/logrotate.d", "etc/systemd/system", "etc/thebitlab", "usr/lib", "usr/share", "usr/sbin", "var/log/nginx", "var/log/thebitlab", "var/lib/nginx", "run", "tmp", ".oldroot"} {
		if err := os.MkdirAll(filepath.Join(s1Target, p), 0755); err != nil {
			return doc, err
		}
	}
	overlap, overlapBytes := 0, int64(0)
	paths := make([]string, 0, len(s1TreePolicies))
	for p := range s1TreePolicies {
		paths = append(paths, p)
	}
	sort.Strings(paths)
	for _, p := range paths {
		policy := s1TreePolicies[p]
		if p == "/etc/nginx" {
			policy = treePolicy{}
		}
		if err := cp.treeFrom(hostPath(p), p, policy); err != nil {
			return doc, err
		}
	}
	if err := normalizeAndApplyCandidateNginx(s1Target); err != nil {
		return doc, err
	}
	links, err := copyCandidateClosure(&cp, candidate, candidateLock)
	if err != nil {
		return doc, err
	}
	for lexical, identity := range cp.objects {
		if existing, ok := s0.Objects[lexical]; ok {
			overlap++
			overlapBytes += identity.Size
			if existing.SHA256 != identity.SHA256 {
				return doc, fmt.Errorf("same path has different identity: %s", lexical)
			}
			return doc, fmt.Errorf("S1 policy duplicates S0 identity: %s", lexical)
		}
	}
	filePaths := make([]string, 0, len(s1Files))
	for p := range s1Files {
		filePaths = append(filePaths, p)
	}
	sort.Strings(filePaths)
	for _, p := range filePaths {
		if existing, ok := s0.Objects[p]; ok {
			overlap++
			overlapBytes += existing.Size
			continue
		}
		digest, size, err := stableCopy(hostPath(p), filepath.Join(s1Target, strings.TrimPrefix(p, "/")), s1Files[p], &cp.c)
		if err != nil {
			return doc, err
		}
		cp.objects[p] = objectIdentity{digest, size, "S1"}
	}
	m := metrics{"S1", time.Since(start).Seconds(), cpuSeconds() - cpuStart, cp.c, len(cp.objects), overlap, overlapBytes, 0, "", "", 0, 0}
	doc = manifest{Schema: manifestSchema, Token: token, MountSource: s1MountSource, Root: s1Host, Objects: cp.objects, Links: links, Metrics: m, SelfSHA256: s0.SelfSHA256, CandidateBundle: candidate, CandidateLockSHA256: candidateLock}
	if err := writeJSON(filepath.Join(s1Target, ".thebitlab-s1-manifest.json"), doc); err != nil {
		return doc, err
	}
	if err := remountRO(s1Target); err != nil {
		return doc, err
	}
	if !mountHas(s1MountSource, s1Host, true) {
		return doc, errors.New("S1 mount is not kernel-witnessed RO tmpfs")
	}
	s0Witness, err := topMount(s0Host)
	if err != nil {
		return doc, err
	}
	s1Witness, err := topMount(s1Host)
	if err != nil {
		return doc, err
	}
	if err := writeJSON(stateHost, map[string]any{"schema": stateSchema, "token": token, "phase": "s1-sealed", "mounts": map[string]mountIdentity{"s0": s0Witness, "s1": s1Witness}}); err != nil {
		return doc, err
	}
	privateFault("s1_after_seal")
	compositionStart := time.Now()
	merged := hostPath(mergedHost)
	if err := ensureDir(merged, 0700); err != nil {
		return doc, err
	}
	options := "lowerdir=" + hostPath(s1Host) + ":" + hostPath(s0Host)
	if err := syscall.Mount("overlay", merged, "overlay", syscall.MS_RDONLY|syscall.MS_NOSUID|syscall.MS_NODEV, options); err != nil {
		return doc, fmt.Errorf("read-only multi-lower overlay rejected: %w", err)
	}
	doc.Metrics.CompositionSeconds = time.Since(compositionStart).Seconds()
	mergedWitness, err := topMount(mergedHost)
	if err != nil {
		return doc, err
	}
	if err := writeJSON(stateHost, map[string]any{"schema": stateSchema, "token": token, "phase": "merged-sealed", "mounts": map[string]mountIdentity{"s0": s0Witness, "s1": s1Witness, "merged": mergedWitness}}); err != nil {
		return doc, err
	}
	privateFault("merged_after_creation")
	managerStart := time.Now()
	runtime := hostPath(runtimeHost + "/runtime")
	for _, p := range []string{"run", "log/nginx", "cache/nginx"} {
		if err := os.MkdirAll(filepath.Join(runtime, p), 0755); err != nil {
			return doc, err
		}
	}
	drop := hostPath(managerDrop)
	if err := ensureDir(drop, 0700); err != nil {
		return doc, err
	}
	if entries, err := os.ReadDir(drop); err != nil || len(entries) != 0 {
		return doc, errors.New("manager drop-in directory has unexpected siblings")
	}
	content := productionDropin(token)
	file, err := os.OpenFile(hostPath(managerDropFile), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	if err != nil {
		return doc, err
	}
	_, writeErr := file.Write(content)
	if writeErr == nil {
		writeErr = file.Sync()
	}
	closeErr := file.Close()
	if writeErr != nil {
		return doc, writeErr
	}
	if closeErr != nil {
		return doc, closeErr
	}
	doc.Metrics.ManagerFenceSeconds = time.Since(managerStart).Seconds()
	s0Digest, err := fileSHA(s0Host + "/.thebitlab-s0-manifest.json")
	if err != nil {
		return doc, err
	}
	s1Digest, err := fileSHA(s1Host + "/.thebitlab-s1-manifest.json")
	if err != nil {
		return doc, err
	}
	dropDigest, err := fileSHA(managerDropFile)
	if err != nil {
		return doc, err
	}
	mounts := map[string]mountIdentity{}
	for name, path := range map[string]string{"s0": s0Host, "s1": s1Host, "merged": mergedHost} {
		identity, err := topMount(path)
		if err != nil {
			return doc, err
		}
		mounts[name] = identity
	}
	if mounts["s0"].Filesystem != "tmpfs" || mounts["s0"].Source != transactionSource(s0Source, token) || !containsString(mounts["s0"].Options, "ro") || mounts["s1"].Filesystem != "tmpfs" || mounts["s1"].Source != s1MountSource || !containsString(mounts["s1"].Options, "ro") || mounts["merged"].Filesystem != "overlay" || !containsString(mounts["merged"].Options, "ro") {
		return doc, errors.New("private runtime final mount witness mismatch")
	}
	runtimeMetadata, err := os.Lstat(runtimeHost)
	if err != nil {
		return doc, err
	}
	runtimeStat := runtimeMetadata.Sys().(*syscall.Stat_t)
	state := runtimeState{Schema: stateSchema, Token: token, Phase: "sealed", S0ManifestSHA256: s0Digest, S1ManifestSHA256: s1Digest, ToolchainID: s0.ToolchainID, ToolchainManifestSHA256: s0.ToolchainManifestSHA256, BrokerSHA256: s0.SelfSHA256, DropinSHA256: dropDigest, CandidateBundle: candidate, CandidateLockSHA256: candidateLock, RuntimeDevice: uint64(runtimeStat.Dev), RuntimeInode: runtimeStat.Ino, Mounts: mounts}
	if err := writeJSON(stateHost, state); err != nil {
		return doc, err
	}
	if err := writeJSON(controlHost+"/s1-metrics.json", doc); err != nil {
		return doc, err
	}
	return doc, nil
}

func loadRuntimeState() (runtimeState, error) {
	var state runtimeState
	if err := attestRuntimeAuthorityDirectory(false); err != nil {
		return state, err
	}
	metadata, err := os.Lstat(stateHost)
	if err != nil {
		return state, err
	}
	raw := metadata.Sys().(*syscall.Stat_t)
	if !metadata.Mode().IsRegular() || raw.Uid != 0 || raw.Gid != 0 || metadata.Mode().Perm() != 0600 || raw.Nlink != 1 {
		return state, errors.New("runtime state metadata invalid")
	}
	if _, err := strictJSON(stateHost, &state); err != nil {
		return state, err
	}
	if state.Schema != stateSchema || state.Token == "" || state.Phase != "sealed" || !candidatePathValid(state.CandidateBundle) || len(state.CandidateLockSHA256) != 64 || state.RuntimeInode == 0 || len(state.Mounts) != 3 {
		return state, errors.New("runtime state identity invalid")
	}
	return state, nil
}

func validateProductionRuntime(token string) (runtimeState, manifest, manifest, error) {
	state, err := loadRuntimeState()
	if err != nil {
		return state, manifest{}, manifest{}, err
	}
	if token != "" && state.Token != token {
		return state, manifest{}, manifest{}, errors.New("runtime transaction token mismatch")
	}
	runtimeMetadata, err := os.Lstat(runtimeHost)
	if err != nil {
		return state, manifest{}, manifest{}, err
	}
	runtimeStat := runtimeMetadata.Sys().(*syscall.Stat_t)
	if uint64(runtimeStat.Dev) != state.RuntimeDevice || runtimeStat.Ino != state.RuntimeInode || !runtimeMetadata.IsDir() || runtimeMetadata.Mode().Perm() != 0700 {
		return state, manifest{}, manifest{}, errors.New("runtime root identity mismatch")
	}
	for name, path := range map[string]string{"s0": s0Host, "s1": s1Host, "merged": mergedHost} {
		record, err := topMount(path)
		if err != nil {
			return state, manifest{}, manifest{}, err
		}
		expected, ok := state.Mounts[name]
		if !ok || !sameMount(record, expected) {
			return state, manifest{}, manifest{}, fmt.Errorf("runtime mount witness stale: %s", name)
		}
	}
	if !containsString(state.Mounts["s0"].Options, "ro") || !containsString(state.Mounts["s1"].Options, "ro") || !containsString(state.Mounts["merged"].Options, "ro") {
		return state, manifest{}, manifest{}, errors.New("runtime mount no longer read-only")
	}
	var s0, s1 manifest
	s0Raw, err := strictJSON(s0Host+"/.thebitlab-s0-manifest.json", &s0)
	if err != nil {
		return state, s0, s1, err
	}
	s1Raw, err := strictJSON(s1Host+"/.thebitlab-s1-manifest.json", &s1)
	if err != nil {
		return state, s0, s1, err
	}
	s0Sum := sha256.Sum256(s0Raw)
	s1Sum := sha256.Sum256(s1Raw)
	if hexDigest(s0Sum[:]) != state.S0ManifestSHA256 || hexDigest(s1Sum[:]) != state.S1ManifestSHA256 || s0.Schema != manifestSchema || s1.Schema != manifestSchema || s0.Token != state.Token || s1.Token != state.Token || s0.MountSource != transactionSource(s0Source, state.Token) || s1.MountSource != transactionSource(s1Source, state.Token) || s0.Root != s0Host || s1.Root != s1Host || s0.SelfSHA256 != state.BrokerSHA256 || s1.SelfSHA256 != state.BrokerSHA256 || s1.CandidateBundle != state.CandidateBundle || s1.CandidateLockSHA256 != state.CandidateLockSHA256 {
		return state, s0, s1, errors.New("runtime sealed manifest identity mismatch")
	}
	for path, identity := range s1.Objects {
		if prior, ok := s0.Objects[path]; ok {
			return state, s0, s1, fmt.Errorf("S0/S1 duplicate identity: %s %s/%s", path, prior.SHA256, identity.SHA256)
		}
	}
	if s1.Metrics.DuplicateCopies != 0 {
		return state, s0, s1, errors.New("S0 to S1 duplicate copied bytes nonzero")
	}
	expectedLinks := map[string]string{"/etc/thebitlab/current": state.CandidateBundle}
	for path, target := range candidateLinks {
		expectedLinks[path] = target
	}
	if len(s1.Links) != len(expectedLinks) {
		return state, s0, s1, errors.New("candidate link closure incomplete")
	}
	for path, target := range expectedLinks {
		if s1.Links[path] != target {
			return state, s0, s1, fmt.Errorf("candidate link identity mismatch: %s", path)
		}
		actual, err := os.Readlink(filepath.Join(s1Host, strings.TrimPrefix(path, "/")))
		if err != nil || actual != target {
			return state, s0, s1, fmt.Errorf("sealed candidate link mismatch: %s", path)
		}
	}
	if _, err := os.Lstat(filepath.Join(s1Host, "etc/nginx/sites-enabled/default")); !os.IsNotExist(err) {
		return state, s0, s1, errors.New("sealed candidate retains distro default")
	}
	_, selfDigest, err := readStableMode("/proc/self/exe", false)
	if err != nil || selfDigest != state.BrokerSHA256 {
		return state, s0, s1, errors.New("executing broker identity differs from sealed authority")
	}
	dropDigest, err := fileSHA(managerDropFile)
	if err != nil || dropDigest != state.DropinSHA256 {
		return state, s0, s1, errors.New("manager drop-in identity mismatch")
	}
	return state, s0, s1, nil
}

func productionPrepare() error {
	if len(os.Args) != 4 {
		return errors.New("production prepare candidate selector absent")
	}
	candidate, candidateLock := os.Args[2], os.Args[3]
	privateFault("prepare_started")
	token, s0, err := buildProductionS0()
	if err != nil {
		return err
	}
	s1, err := productionStage1Build(token, s0, candidate, candidateLock)
	if err != nil {
		return err
	}
	state, _, _, err := validateProductionRuntime(token)
	if err != nil {
		return err
	}
	report := map[string]any{"schema": "thebitlab.private-runtime-report.v1", "token": token, "lifetime": "service", "candidate_bundle": candidate, "candidate_lock_sha256": candidateLock, "s0": s0.Metrics, "s1": s1.Metrics, "composition": "overlay-ro-lowerdir=S1:S0", "mounts": state.Mounts}
	data, _ := json.Marshal(report)
	fmt.Println(string(data))
	return nil
}

func stage1Client() error {
	token := os.Getenv("THEBITLAB_PRIVATE_POC_TOKEN")
	if token == "" {
		return errors.New("transaction selector absent")
	}
	control := filepath.Join(runtimeHost, "control")
	if err := os.WriteFile(filepath.Join(control, "broker-request"), []byte(token+"\n"), 0600); err != nil {
		return err
	}
	deadline := time.Now().Add(180 * time.Second)
	for time.Now().Before(deadline) {
		data, err := os.ReadFile(filepath.Join(control, "broker-server-result"))
		if err == nil {
			var result map[string]string
			if json.Unmarshal(data, &result) != nil || result["token"] != token {
				return errors.New("static broker result identity mismatch")
			}
			if result["error"] != "" {
				return errors.New(result["error"])
			}
			return nil
		}
		time.Sleep(5 * time.Millisecond)
	}
	return errors.New("timeout static stage1 server")
}
func stage1Server(token string) error {
	control := filepath.Join(runtimeHost, "control")
	deadline := time.Now().Add(180 * time.Second)
	for time.Now().Before(deadline) {
		data, err := os.ReadFile(filepath.Join(control, "broker-request"))
		if err == nil {
			info, statErr := os.Lstat(filepath.Join(control, "broker-request"))
			if statErr != nil || !info.Mode().IsRegular() || info.Mode().Perm() != 0600 {
				return errors.New("broker request metadata invalid")
			}
			if strings.TrimSpace(string(data)) != token {
				return errors.New("broker request selector mismatch")
			}
			buildErr := stage1Build(token)
			detail := ""
			if buildErr != nil {
				detail = buildErr.Error()
			}
			if err := writeJSON(filepath.Join(control, "broker-server-result"), map[string]string{"token": token, "error": detail}); err != nil {
				return err
			}
			return buildErr
		}
		time.Sleep(5 * time.Millisecond)
	}
	return errors.New("timeout waiting sealed stage1 client")
}
func startBarrier() error {
	control := filepath.Join(runtimeHost, "control")
	if err := os.WriteFile(filepath.Join(control, "start-barrier-ready"), []byte("ready\n"), 0600); err != nil {
		return err
	}
	deadline := time.Now().Add(30 * time.Second)
	for time.Now().Before(deadline) {
		if _, err := os.Lstat(filepath.Join(control, "start-continue")); err == nil {
			return nil
		}
		time.Sleep(5 * time.Millisecond)
	}
	return errors.New("timeout test-only nginx start barrier")
}
func privateExec() error {
	if len(os.Args) < 3 {
		return errors.New("private exec command absent")
	}
	evidence, err := os.OpenFile(
		filepath.Join(controlHost, fmt.Sprintf("private-exec-%d", os.Getpid())),
		os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600,
	)
	if err != nil {
		return err
	}

	// A mount namespace belongs to an OS thread, not a Go goroutine. Keep this
	// process's one-way namespace transition and target exec on the same thread.
	// If Unshare succeeds, every error returns directly to main, which exits the
	// single-purpose helper without ever unlocking the namespace-modified thread.
	runtime.LockOSThread()
	tid := syscall.Gettid()
	_, _ = fmt.Fprintf(evidence, "phase=before-unshare pid=%d tid=%d namespace=%s\n", os.Getpid(), tid, mustReadlink("/proc/thread-self/ns/mnt"))
	if err := syscall.Unshare(syscall.CLONE_NEWNS); err != nil {
		runtime.UnlockOSThread()
		_ = evidence.Close()
		return err
	}
	privateNamespace, err := os.Open("/proc/thread-self/ns/mnt")
	if err != nil {
		return err
	}
	privateNamespaceIdentity := namespaceFileIdentity(privateNamespace)
	_, _ = fmt.Fprintf(evidence, "phase=after-unshare pid=%d tid=%d namespace=%s namespace_fd=%s\n", os.Getpid(), syscall.Gettid(), mustReadlink("/proc/thread-self/ns/mnt"), privateNamespaceIdentity)
	privateFault("private_exec_after_unshare")
	if err := syscall.Mount("", "/", "", syscall.MS_REC|syscall.MS_PRIVATE, ""); err != nil {
		return err
	}
	for _, pair := range [][2]string{
		{runtimeHost + "/runtime/run", mergedHost + "/run"},
		{runtimeHost + "/runtime/log/nginx", mergedHost + "/var/log/nginx"},
		{"/var/log/thebitlab", mergedHost + "/var/log/thebitlab"},
		{runtimeHost + "/runtime/cache/nginx", mergedHost + "/var/lib/nginx"},
		{"/dev/null", mergedHost + "/dev/null"},
	} {
		if err := syscall.Mount(pair[0], pair[1], "", syscall.MS_BIND, ""); err != nil {
			return fmt.Errorf("private exec data bind %s: %w", pair[1], err)
		}
	}
	mergedMetadata, err := os.Stat(mergedHost)
	if err != nil {
		return err
	}
	mergedStat := mergedMetadata.Sys().(*syscall.Stat_t)
	if err := syscall.Chdir(mergedHost); err != nil {
		return err
	}
	if err := syscall.PivotRoot(".", ".oldroot"); err != nil {
		return err
	}
	if err := syscall.Chdir("/"); err != nil {
		return err
	}
	if err := syscall.Unmount("/.oldroot", syscall.MNT_DETACH); err != nil {
		return err
	}
	rootMetadata, err := os.Stat("/")
	if err != nil {
		return err
	}
	rootStat := rootMetadata.Sys().(*syscall.Stat_t)
	if !canonicalRuntimeDirectory(rootStat, 0755) {
		return errors.New("private synthetic root metadata mismatch")
	}
	if syscall.Gettid() != tid || namespaceFileIdentity(privateNamespace) != privateNamespaceIdentity {
		return errors.New("private exec thread/namespace identity changed after root setup")
	}
	_, _ = fmt.Fprintf(evidence, "phase=after-root pid=%d tid=%d namespace_fd=%s root_dev=%d root_inode=%d expected_root_dev=%d expected_root_inode=%d\n", os.Getpid(), syscall.Gettid(), privateNamespaceIdentity, rootStat.Dev, rootStat.Ino, mergedStat.Dev, mergedStat.Ino)
	_, rootCrypto, cryptoErr := readStable("/usr/lib/x86_64-linux-gnu/libcrypto.so.3")
	_, _ = fmt.Fprintf(evidence, "phase=before-exec pid=%d tid=%d namespace_fd=%s command=%s root_libcrypto=%s error=%v\n", os.Getpid(), syscall.Gettid(), privateNamespaceIdentity, os.Args[2], rootCrypto, cryptoErr)
	_ = privateNamespace.Close()
	_ = evidence.Close()
	closeExtraFDs()
	loader := "/lib64/ld-linux-x86-64.so.2"
	arguments := []string{loader, "--inhibit-cache", "--library-path", "/usr/lib/x86_64-linux-gnu", os.Args[2]}
	arguments = append(arguments, os.Args[3:]...)
	return syscall.Exec(loader, arguments, []string{"HOME=/root", "LANG=C", "LC_ALL=C", "PATH=/usr/sbin:/usr/bin:/sbin:/bin"})
}

func namespaceFileIdentity(file *os.File) string {
	var metadata syscall.Stat_t
	if err := syscall.Fstat(int(file.Fd()), &metadata); err != nil {
		return "ERROR:" + err.Error()
	}
	return fmt.Sprintf("mnt:[%d]", metadata.Ino)
}

func mustReadlink(path string) string {
	value, err := os.Readlink(path)
	if err != nil {
		return "ERROR:" + err.Error()
	}
	return value
}

func productionTestBarrier(token string) error {
	interlock, err := os.ReadFile("/run/thebitlab-ephemeral-activation-test")
	if err != nil || string(interlock) != "ephemeral-only\n" {
		return nil
	}
	pause := controlHost + "/test-handoff-pause"
	metadata, err := os.Lstat(pause)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	raw := metadata.Sys().(*syscall.Stat_t)
	if !metadata.Mode().IsRegular() || raw.Uid != 0 || raw.Gid != 0 || metadata.Mode().Perm() != 0600 {
		return errors.New("test handoff pause metadata invalid")
	}
	if err := os.WriteFile(controlHost+"/test-handoff-ready", []byte(token+"\n"), 0600); err != nil {
		return err
	}
	deadline := time.Now().Add(8 * time.Second)
	for time.Now().Before(deadline) {
		data, err := os.ReadFile(controlHost + "/test-handoff-continue")
		if err == nil && string(data) == token+"\n" {
			_ = os.Remove(pause)
			_ = os.Remove(controlHost + "/test-handoff-ready")
			_ = os.Remove(controlHost + "/test-handoff-continue")
			return nil
		}
		time.Sleep(5 * time.Millisecond)
	}
	return errors.New("timeout test-only handoff barrier")
}

func productionPrivateExec() error {
	if len(os.Args) < 4 {
		return errors.New("private exec token/command absent")
	}
	token := os.Args[2]
	privateFault("handoff_begins")
	if _, _, _, err := validateProductionRuntime(token); err != nil {
		return err
	}
	if err := productionTestBarrier(token); err != nil {
		return err
	}
	command := os.Args[3]
	if command == "/usr/sbin/nginx" {
		privateFault("before_nginx_exec")
	}
	os.Args = append([]string{os.Args[0], "private-exec"}, os.Args[3:]...)
	return privateExec()
}

func cgroupEmpty() (bool, error) {
	data, err := os.ReadFile("/sys/fs/cgroup/system.slice/nginx.service/cgroup.procs")
	if os.IsNotExist(err) {
		return true, nil
	}
	if err != nil {
		return false, err
	}
	return strings.TrimSpace(string(data)) == "", nil
}

func readRecoveryAuthority() (string, map[string]mountIdentity, error) {
	metadata, err := os.Lstat(stateHost)
	if err != nil {
		return "", nil, err
	}
	raw := metadata.Sys().(*syscall.Stat_t)
	if !metadata.Mode().IsRegular() || raw.Uid != 0 || raw.Gid != 0 || metadata.Mode().Perm() != 0600 || raw.Nlink != 1 {
		return "", nil, errors.New("recovery state metadata invalid")
	}
	data, _, err := readStable(stateHost)
	if err != nil {
		return "", nil, err
	}
	var value map[string]json.RawMessage
	if err := json.Unmarshal(data, &value); err != nil {
		return "", nil, err
	}
	var schema, token string
	if json.Unmarshal(value["schema"], &schema) != nil || json.Unmarshal(value["token"], &token) != nil || schema != stateSchema {
		return "", nil, errors.New("recovery state schema invalid")
	}
	parts := strings.Split(token, "-")
	if len(parts) != 2 || len(parts[1]) != 32 {
		return "", nil, errors.New("recovery token invalid")
	}
	if _, err := strconv.ParseUint(parts[0], 10, 64); err != nil {
		return "", nil, errors.New("recovery token pid invalid")
	}
	if _, err := hex.DecodeString(parts[1]); err != nil {
		return "", nil, errors.New("recovery token entropy invalid")
	}
	mounts := map[string]mountIdentity{}
	if rawMounts, ok := value["mounts"]; ok {
		if err := json.Unmarshal(rawMounts, &mounts); err != nil {
			return "", nil, err
		}
	}
	return token, mounts, nil
}

func currentMountIfAny(path string) (*mountIdentity, error) {
	identity, err := topMount(path)
	if err != nil {
		if strings.Contains(err.Error(), "witness absent") {
			return nil, nil
		}
		return nil, err
	}
	return &identity, nil
}

func exactRecoveryMount(name, path, token string, persisted map[string]mountIdentity) (*mountIdentity, error) {
	current, err := currentMountIfAny(path)
	if err != nil || current == nil {
		return current, err
	}
	if expected, ok := persisted[name]; ok {
		if !sameMount(*current, expected) {
			return nil, fmt.Errorf("foreign/ABA mount preserved: %s", name)
		}
		return current, nil
	}
	expectedSource := ""
	expectedFS := "tmpfs"
	switch name {
	case "s0":
		expectedSource = transactionSource(s0Source, token)
	case "s1":
		expectedSource = transactionSource(s1Source, token)
	case "manager":
		expectedSource = transactionSource(managerSource, token)
	case "merged":
		return nil, errors.New("ambiguous merged mount without persisted witness")
	}
	if current.Source != expectedSource || current.Filesystem != expectedFS || current.Root != "/" {
		return nil, fmt.Errorf("foreign mount preserved: %s", name)
	}
	return current, nil
}

func removeRuntimeTree(state *runtimeState) error {
	if state != nil {
		metadata, err := os.Lstat(runtimeHost)
		if err != nil {
			return err
		}
		raw := metadata.Sys().(*syscall.Stat_t)
		if uint64(raw.Dev) != state.RuntimeDevice || raw.Ino != state.RuntimeInode {
			return errors.New("runtime root changed before removal")
		}
	}
	for _, record := range []struct{ name, path string }{{"merged", mergedHost}, {"s1", s1Host}, {"s0", s0Host}} {
		if mounted, err := currentMountIfAny(record.path); err != nil {
			return err
		} else if mounted != nil {
			return fmt.Errorf("runtime mount remains before tree removal: %s", record.name)
		}
	}
	if err := os.RemoveAll(runtimeHost); err != nil {
		return err
	}
	return nil
}

func productionCleanup() error {
	if filepath.Clean(os.Args[0]) != launcherHost {
		return errors.New("cleanup requires canonical static launcher")
	}
	if len(os.Args) != 3 {
		return errors.New("cleanup transaction token absent")
	}
	token := os.Args[2]
	persisted := map[string]mountIdentity{}
	var sealed *runtimeState
	if finalState, loadErr := loadRuntimeState(); loadErr == nil {
		state, s0, s1, validateErr := validateProductionRuntime(token)
		if validateErr != nil {
			return validateErr
		}
		_ = s0
		_ = s1
		if finalState.Token != state.Token {
			return errors.New("sealed cleanup state changed")
		}
		persisted = state.Mounts
		sealed = &state
	} else {
		recoveryToken, recoveryMounts, recoveryErr := readRecoveryAuthority()
		if recoveryErr != nil {
			return fmt.Errorf("runtime partial recovery unavailable: %w", loadErr)
		}
		if recoveryToken != token {
			return errors.New("cleanup token differs from recovery authority")
		}
		persisted = recoveryMounts
		if _, err := os.Lstat(managerDropFile); err == nil {
			return errors.New("ambiguous partial manager drop-in preserved")
		} else if !os.IsNotExist(err) {
			return err
		}
	}
	empty, err := cgroupEmpty()
	if err != nil {
		return err
	}
	if !empty {
		return errors.New("runtime teardown refused while nginx cgroup is nonempty")
	}
	privateFault("runtime_teardown")
	if sealed != nil {
		digest, err := fileSHA(managerDropFile)
		if err != nil || digest != sealed.DropinSHA256 {
			return errors.New("drop-in changed before exact teardown")
		}
		if err := os.Remove(managerDropFile); err != nil {
			return err
		}
		entries, err := os.ReadDir(managerDrop)
		if err != nil || len(entries) != 0 {
			return errors.New("manager drop-in directory not empty at teardown")
		}
		if err := os.Remove(managerDrop); err != nil {
			return err
		}
		parent, err := os.Open(filepath.Dir(managerDrop))
		if err != nil {
			return err
		}
		if err := parent.Sync(); err != nil {
			_ = parent.Close()
			return err
		}
		if err := parent.Close(); err != nil {
			return err
		}
	}
	for _, record := range []struct{ name, path string }{{"merged", mergedHost}, {"s1", s1Host}, {"s0", s0Host}} {
		mounted, err := exactRecoveryMount(record.name, record.path, token, persisted)
		if err != nil {
			return err
		}
		if mounted == nil {
			continue
		}
		current, err := topMount(record.path)
		if err != nil || current.MountID != mounted.MountID {
			return fmt.Errorf("mount changed before teardown: %s", record.name)
		}
		if err := syscall.Unmount(record.path, 0); err != nil {
			return fmt.Errorf("exact unmount failed %s: %w", record.name, err)
		}
	}
	return removeRuntimeTree(sealed)
}

func productionAttest() error {
	if len(os.Args) != 3 {
		return errors.New("attest transaction token absent")
	}
	state, s0, s1, err := validateProductionRuntime(os.Args[2])
	if err != nil {
		return err
	}
	data, _ := json.Marshal(map[string]any{"schema": "thebitlab.private-runtime-attestation.v1", "token": state.Token, "phase": state.Phase, "s0": s0.Metrics, "s1": s1.Metrics, "mounts": state.Mounts})
	fmt.Println(string(data))
	return nil
}

func main() {
	var err error
	if len(os.Args) < 2 {
		err = errors.New("private runtime command absent")
	} else {
		switch os.Args[1] {
		case "production-prepare":
			err = productionPrepare()
		case "production-attest":
			err = productionAttest()
		case "production-cleanup":
			err = productionCleanup()
		case "production-private-exec":
			err = productionPrivateExec()
		default:
			err = errors.New("private runtime command unknown")
		}
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "PRIVATE-RUNTIME:", err)
		os.Exit(2)
	}
}

var _ = bytes.Equal
