// thebitlab-systemd-generator-orchestrator is the sole systemd generator
// selected on the reviewed Ubuntu Noble pilot host. It reproduces the closed
// stock generator set in parallel, writing only to coordinator-owned staging.
package main

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"
)

const (
	controlSocket = "\x00thebitlab-pilot-generator-v1"
	runtimeRoot   = "/run/thebitlab/pilot-generator-orchestrator/transactions"
)

var tokenPattern = regexp.MustCompile(`^[1-9][0-9]{0,19}-[0-9a-f]{32}$`)

type reviewedGenerator struct {
	path   string
	sha256 string
}

var reviewedGenerators = []reviewedGenerator{
	{"/usr/lib/systemd/system-generators/systemd-cryptsetup-generator", "f15c109b8f2989b52d4b9fbe0616c34f1d6fc447b2df50972489befffdcdeeb9"},
	{"/usr/lib/systemd/system-generators/systemd-debug-generator", "1c4134dfba90289c3f27c4dad93122ad65acba58f0271f9a81f3c70a7d22b0a1"},
	{"/usr/lib/systemd/system-generators/systemd-fstab-generator", "15c4d4502f06b8f6d6dafca932edbaafc1dbdb8d7a0edc324f34000a49ba4d08"},
	{"/usr/lib/systemd/system-generators/systemd-getty-generator", "b25bbe3184dfdc205ca1f226c6829f21b39c132aed726d64deafe1007e45f5b6"},
	{"/usr/lib/systemd/system-generators/systemd-hibernate-resume-generator", "b4f4a82855044c085d8b0f11fa2a04623097922894bd92924badcf2b9900ecfb"},
	{"/usr/lib/systemd/system-generators/systemd-integritysetup-generator", "e1eeff5894aa94f0bafa9618a2df290bdc7e57a44b0bf5c83c8e0a72b91260d2"},
	{"/usr/lib/systemd/system-generators/systemd-rc-local-generator", "1940b17c163d9c1b5b98db9be3fe07204a33f3f4a23572934d731d7f0336ef80"},
	{"/usr/lib/systemd/system-generators/systemd-run-generator", "d0e4b0d8470530116b9b6919d2cd8455d97eaad89ace11d7a3b7387a41831302"},
	{"/usr/lib/systemd/system-generators/systemd-system-update-generator", "ed7791c0a28a4404065e863e703a469f3b3213a291a05baa960c83877de1d994"},
	{"/usr/lib/systemd/system-generators/systemd-sysv-generator", "e4557b5fc18adad8b41da15bf5297c121a9f8445bb4c9c9d34a83b262c6507b4"},
	{"/usr/lib/systemd/system-generators/systemd-veritysetup-generator", "75385259d93f97d88c26d36d1d904600707e551388d1558b98259307c9b45f7e"},
}

func hashRegular(path, expected string) error {
	info, err := os.Lstat(path)
	if err != nil {
		return err
	}
	if !info.Mode().IsRegular() || info.Mode().Perm()&0022 != 0 {
		return fmt.Errorf("unsafe reviewed generator metadata: %s", path)
	}
	if stat, ok := info.Sys().(*syscall.Stat_t); !ok || stat.Uid != 0 || stat.Gid != 0 || stat.Nlink != 1 {
		return fmt.Errorf("unsafe reviewed generator identity: %s", path)
	}
	payload, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	actual := sha256.Sum256(payload)
	if hex.EncodeToString(actual[:]) != expected {
		return fmt.Errorf("reviewed generator digest mismatch: %s", path)
	}
	return nil
}

func closedEnvironment() ([]string, error) {
	allowed := map[string]bool{
		"HOME": true, "HOSTNAME": true, "LANG": true, "PATH": true,
		"SYSTEMD_ARCHITECTURE": true, "SYSTEMD_EXEC_PID": true,
		"SYSTEMD_FIRST_BOOT": true, "SYSTEMD_IN_INITRD": true,
		"SYSTEMD_SCOPE": true, "SYSTEMD_VIRTUALIZATION": true,
		"THEBITLAB_UBUNTU_SNAPSHOT": true, "container": true,
	}
	values := make(map[string]string, len(allowed))
	for _, entry := range os.Environ() {
		key, value, found := strings.Cut(entry, "=")
		if !found || !allowed[key] {
			return nil, fmt.Errorf("unexpected generator environment key: %s", key)
		}
		if _, duplicate := values[key]; duplicate {
			return nil, fmt.Errorf("duplicate generator environment key: %s", key)
		}
		values[key] = value
	}
	if len(values) != len(allowed) {
		return nil, errors.New("incomplete stock generator environment")
	}
	keys := make([]string, 0, len(values))
	for key := range values {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	result := make([]string, 0, len(keys))
	for _, key := range keys {
		result = append(result, key+"="+values[key])
	}
	return result, nil
}

func replaceExecPID(environment []string, pid int) []string {
	result := make([]string, 0, len(environment)+1)
	for _, entry := range environment {
		if !strings.HasPrefix(entry, "SYSTEMD_EXEC_PID=") {
			result = append(result, entry)
		}
	}
	result = append(result, "SYSTEMD_EXEC_PID="+strconv.Itoa(pid))
	sort.Strings(result)
	return result
}

func validateOutputs(fields []string) ([3]string, error) {
	var outputs [3]string
	if len(fields) != 3 {
		return outputs, errors.New("wrong output path count")
	}
	stage := filepath.Dir(fields[0])
	token := filepath.Base(filepath.Dir(stage))
	if !tokenPattern.MatchString(token) || stage != filepath.Join(runtimeRoot, token, "stage") {
		return outputs, errors.New("non-canonical staging root")
	}
	expected := [3]string{filepath.Join(stage, "normal"), filepath.Join(stage, "early"), filepath.Join(stage, "late")}
	for index := range expected {
		if fields[index] != expected[index] {
			return outputs, errors.New("staging output mismatch")
		}
		outputs[index] = expected[index]
	}
	return outputs, nil
}

func parsePrepared(line string) (string, [3]string, error) {
	var outputs [3]string
	fields := strings.Split(strings.TrimSuffix(line, "\n"), "\t")
	if len(fields) != 5 || fields[0] != "PREPARED" || !tokenPattern.MatchString(fields[1]) {
		return "", outputs, errors.New("non-canonical coordinator response")
	}
	stage := filepath.Join(runtimeRoot, fields[1], "stage")
	expected := [3]string{filepath.Join(stage, "normal"), filepath.Join(stage, "early"), filepath.Join(stage, "late")}
	for index := range expected {
		if fields[index+2] != expected[index] {
			return "", outputs, errors.New("coordinator staging path mismatch")
		}
		outputs[index] = expected[index]
	}
	return fields[1], outputs, nil
}

func runChildren(outputs [3]string, environment []string) error {
	commands := make([]*exec.Cmd, 0, len(reviewedGenerators))
	executable, err := os.Executable()
	if err != nil {
		return err
	}
	for index, generator := range reviewedGenerators {
		if err := hashRegular(generator.path, generator.sha256); err != nil {
			return err
		}
		// The tiny inner mode sets SYSTEMD_EXEC_PID to its own post-fork PID and
		// execs the reviewed generator in-place, preserving stock lineage.
		command := exec.Command(executable, "--inner", strconv.Itoa(index), outputs[0], outputs[1], outputs[2])
		command.Dir = "/"
		command.Env = environment
		command.Stdin = os.Stdin
		command.Stdout = os.Stdout
		command.Stderr = os.Stderr
		command.SysProcAttr = &syscall.SysProcAttr{Pdeathsig: syscall.SIGTERM}
		if err := command.Start(); err != nil {
			// Deliberate fail-closed difference from EXEC_DIR_IGNORE_ERRORS: an
			// inventory-verified executable that cannot be launched aborts adoption.
			return fmt.Errorf("cannot launch reviewed generator %s: %w", generator.path, err)
		}
		commands = append(commands, command)
	}
	// All children have been launched before the first wait. Exit status is
	// intentionally ignored, matching EXEC_DIR_IGNORE_ERRORS.
	for _, command := range commands {
		_ = command.Wait()
	}
	return nil
}

func main() {
	if err := os.Chdir("/"); err != nil {
		os.Exit(2)
	}
	syscall.Umask(0022)
	if len(os.Args) == 6 && os.Args[1] == "--inner" {
		index, err := strconv.Atoi(os.Args[2])
		outputs, outputErr := validateOutputs(os.Args[3:])
		if err != nil || outputErr != nil || index < 0 || index >= len(reviewedGenerators) {
			os.Exit(126)
		}
		if err := hashRegular(reviewedGenerators[index].path, reviewedGenerators[index].sha256); err != nil {
			os.Exit(126)
		}
		environment, err := closedEnvironment()
		if err != nil {
			os.Exit(126)
		}
		environment = replaceExecPID(environment, os.Getpid())
		if err := syscall.Exec(reviewedGenerators[index].path, []string{reviewedGenerators[index].path, outputs[0], outputs[1], outputs[2]}, environment); err != nil {
			os.Exit(127)
		}
	}
	if len(os.Args) != 4 || os.Args[1] != "/run/systemd/generator" || os.Args[2] != "/run/systemd/generator.early" || os.Args[3] != "/run/systemd/generator.late" {
		os.Exit(2)
	}
	var limit syscall.Rlimit
	if syscall.Getrlimit(syscall.RLIMIT_NOFILE, &limit) == nil && limit.Cur > 1024 {
		limit.Cur = 1024
		if err := syscall.Setrlimit(syscall.RLIMIT_NOFILE, &limit); err != nil {
			os.Exit(2)
		}
	}
	environment, err := closedEnvironment()
	if err != nil {
		os.Exit(2)
	}
	connection, err := net.DialTimeout("unix", controlSocket, 2*time.Second)
	if err != nil {
		// No PREPARED trusted transaction: retain the already validated roots.
		os.Exit(1)
	}
	defer connection.Close()
	_ = connection.SetDeadline(time.Now().Add(30 * time.Second))
	reader := bufio.NewReader(connection)
	line, err := reader.ReadString('\n')
	if err != nil {
		os.Exit(1)
	}
	token, outputs, err := parsePrepared(line)
	if err != nil {
		os.Exit(1)
	}
	if err := runChildren(outputs, environment); err != nil {
		_, _ = fmt.Fprintf(connection, "FAILED\t%s\n", token)
		os.Exit(1)
	}
	if _, err := fmt.Fprintf(connection, "GENERATED\t%s\n", token); err != nil {
		os.Exit(1)
	}
	ack, err := reader.ReadString('\n')
	if err != nil || !strings.HasPrefix(ack, "PASS\t") {
		os.Exit(1)
	}
	os.Exit(0)
}
