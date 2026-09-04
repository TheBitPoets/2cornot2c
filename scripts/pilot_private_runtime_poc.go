//go:build linux

// pilot_private_runtime_poc is a security/performance experiment for issue #704.
// It is deliberately separate from the current production prototype.  The same
// CGO-free static artifact is both the private stage-0 launcher and stage-1
// broker.  It never executes a dynamic host helper while constructing roots.
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
	runtimeHost = "/run/thebitlab-private-runtime-poc"
	s0Host       = runtimeHost + "/s0"
	s1Host       = runtimeHost + "/s1"
	mergedHost   = runtimeHost + "/merged"
	controlHost  = runtimeHost + "/control"
	stateHost    = runtimeHost + "/state.json"
	managerDrop  = "/run/systemd/system/nginx.service.d"
	launcherHost = "/usr/sbin/thebitlab-private-runtime-poc"
	pinHost      = "/etc/thebitlab/trust/pilot-private-runtime-poc.json"
	s0Source     = "thebitlab-private-s0"
	s1Source     = "thebitlab-private-s1"
	managerSource = "thebitlab-private-manager"
)

var treePolicies = map[string]treePolicy{
	"/usr/lib/x86_64-linux-gnu": {"84e0e21402a88414b237e0e144d6b8901831e4412fe27b04ee468f5d69a7a7df", 115, 1033, 74},
	"/usr/lib/python3.12": {"94cce3010870569d66c0c1b6521761b1f6e73b385beda080b3b5884aaf4f5bec", 90, 1193, 2},
	"/usr/lib/python3/dist-packages": {"414c6baefe31cf63e443acfddd890f690f3b4350d7aca1ceeba27650d1bfff3b", 19, 158, 0},
}

var s1TreePolicies = map[string]treePolicy{
	"/etc/nginx": {"026a39869452bd2aec4be2036ff05a4d0c2729f8e89b6721ec90f16465413b6b", 7, 13, 3},
	"/usr/share/nginx": {"647df966b9c27faa03fe3cd07c0d8dbbcacd59370fbfd39f354a520d2db38457", 3, 3, 1},
	"/usr/lib/nginx/modules": {"51139bd9cf430b672599fb5c24af46318f7421d6c9f901439238ef4a818a876a", 1, 2, 0},
}

var s0Files = map[string]string{
	"/usr/bin/python3.12": "1643dacd9feaedc58f3cc581e4d22577dfe25c09b10282936186ccf0f2e61118",
	"/etc/nsswitch.conf": "eec30745bade42a3f3f792e4d4192e57d2bcfe8e472433b1de426fe39a39cddb",
	"/etc/ssl/openssl.cnf": "529815b0dd4bd6608bafeeb3d410b0683374e61aef792b3e3f38b3767d26f747",
	"/etc/passwd": "5dbc7ebdf180bd84f58372b8dbd071f5bb175799ea23e197ff1732975f2b3f3b",
	"/etc/group": "b5132aaf99e107c060b1f25cb3324e193dd83cb6bbf70f777b0d83a7638c49fe",
}

var s1Files = map[string]string{
	"/usr/sbin/nginx": "1f16b72bea2f44e5d04fe6cf9e3e4b0dec53a82c50c7c1533c302a8ecaeccacf",
	"/usr/sbin/start-stop-daemon": "81faf821fdfdf1dc2991b71dfbd6a21116085f931bfeb0fd7b2623911a4831b4",
}

type treePolicy struct { SHA256 string; Dirs, Files, Links int }
type counters struct {
	FilesRead int64 `json:"files_read"`
	BytesRead int64 `json:"bytes_read"`
	FilesCopied int64 `json:"files_copied"`
	BytesCopied int64 `json:"bytes_copied"`
	HashOperations int64 `json:"hash_operations"`
	BytesHashed int64 `json:"bytes_hashed"`
}
type metrics struct {
	Stage string `json:"stage"`
	WallSeconds float64 `json:"wall_seconds"`
	CPUSeconds float64 `json:"cpu_seconds"`
	Counters counters `json:"counters"`
	Identities int `json:"identities"`
	OverlapIdentities int `json:"overlap_identities,omitempty"`
	OverlapBytes int64 `json:"overlap_bytes,omitempty"`
	DuplicateCopies int64 `json:"duplicate_copies"`
	PTInterp string `json:"pt_interp,omitempty"`
	PythonPolicy string `json:"python_policy,omitempty"`
	CompositionSeconds float64 `json:"composition_seconds,omitempty"`
	ManagerFenceSeconds float64 `json:"manager_fence_seconds,omitempty"`
}
type objectIdentity struct { SHA256 string `json:"sha256"`; Size int64 `json:"size"`; Stage string `json:"stage"` }
type manifest struct {
	Schema string `json:"schema"`
	Token string `json:"token"`
	MountSource string `json:"mount_source"`
	Root string `json:"root"`
	Objects map[string]objectIdentity `json:"objects"`
	Metrics metrics `json:"metrics"`
	SelfSHA256 string `json:"self_sha256"`
	ToolchainID string `json:"toolchain_id,omitempty"`
	ToolchainManifestSHA256 string `json:"toolchain_manifest_sha256,omitempty"`
}
type pinDocument struct {
	SchemaVersion string `json:"schema_version"`
	ToolchainID string `json:"toolchain_id"`
	ToolchainManifestSHA256 string `json:"toolchain_manifest_sha256"`
	LauncherSHA256 string `json:"launcher_sha256"`
	ReleaseCommit string `json:"release_commit"`
}
type toolchainDocument struct {
	SchemaVersion string `json:"schema_version"`
	ToolchainID string `json:"toolchain_id"`
	ReleaseCommit string `json:"release_commit"`
	Files map[string]string `json:"files"`
}

type copier struct { root string; c counters; objects map[string]objectIdentity; stage string }

func cpuSeconds() float64 {
	var usage syscall.Rusage
	_ = syscall.Getrusage(syscall.RUSAGE_SELF, &usage)
	return float64(usage.Utime.Sec+usage.Stime.Sec) + float64(usage.Utime.Usec+usage.Stime.Usec)/1e6
}
func hexDigest(sum []byte) string { return hex.EncodeToString(sum) }
func ensureDir(path string, mode fs.FileMode) error {
	if err := os.MkdirAll(path, mode); err != nil { return err }
	info, err := os.Lstat(path); if err != nil { return err }
	st, ok := info.Sys().(*syscall.Stat_t)
	if !ok || !info.IsDir() || info.Mode()&os.ModeSymlink != 0 || st.Uid != 0 || info.Mode().Perm()&0022 != 0 { return fmt.Errorf("directory unsafe: %s", path) }
	return nil
}
func writeJSON(path string, value any) error {
	data, err := json.MarshalIndent(value, "", "  "); if err != nil { return err }
	data = append(data, '\n')
	if err := os.WriteFile(path, data, 0600); err != nil { return err }
	return nil
}
func stableCopy(source, destination string, expected string, c *counters) (string, int64, error) {
	fd, err := syscall.Open(source, syscall.O_RDONLY|syscall.O_CLOEXEC|syscall.O_NOFOLLOW, 0)
	if err != nil { return "", 0, err }
	in := os.NewFile(uintptr(fd), source); defer in.Close()
	var before, after syscall.Stat_t
	if err := syscall.Fstat(fd, &before); err != nil { return "", 0, err }
	if before.Mode&syscall.S_IFMT != syscall.S_IFREG || before.Uid != 0 || before.Mode&0022 != 0 { return "", 0, fmt.Errorf("source file unsafe: %s", source) }
	if err := os.MkdirAll(filepath.Dir(destination), 0755); err != nil { return "", 0, err }
	out, err := os.OpenFile(destination, os.O_WRONLY|os.O_CREATE|os.O_EXCL, fs.FileMode(before.Mode&07777)); if err != nil { return "", 0, err }
	h := sha256.New(); n, copyErr := io.Copy(io.MultiWriter(out, h), in)
	closeErr := out.Close()
	if copyErr != nil { return "", 0, copyErr }; if closeErr != nil { return "", 0, closeErr }
	if err := syscall.Fstat(fd, &after); err != nil { return "", 0, err }
	if before.Dev != after.Dev || before.Ino != after.Ino || before.Size != after.Size || before.Mtim != after.Mtim || before.Ctim != after.Ctim || n != before.Size { return "", 0, fmt.Errorf("source changed during one-pass copy: %s", source) }
	if err := os.Chown(destination, int(before.Uid), int(before.Gid)); err != nil { return "", 0, err }
	if err := syscall.Chmod(destination, before.Mode&07777); err != nil { return "", 0, err }
	digest := hexDigest(h.Sum(nil))
	c.FilesRead++; c.FilesCopied++; c.HashOperations++; c.BytesRead += n; c.BytesCopied += n; c.BytesHashed += n
	if expected != "" && digest != expected { return digest, n, fmt.Errorf("reviewed digest mismatch: %s actual=%s", source, digest) }
	return digest, n, nil
}
func (cp *copier) file(path, expected string) error {
	digest, size, err := stableCopy(path, filepath.Join(cp.root, strings.TrimPrefix(path, "/")), expected, &cp.c)
	if err != nil { return err }
	cp.objects[path] = objectIdentity{digest, size, cp.stage}; return nil
}
func (cp *copier) bytesFile(path string, data []byte, expected string, mode fs.FileMode) error {
	digestRaw := sha256.Sum256(data); digest := hexDigest(digestRaw[:])
	if digest != expected { return fmt.Errorf("reviewed in-memory digest mismatch: %s", path) }
	destination := filepath.Join(cp.root, strings.TrimPrefix(path, "/")); if err := os.MkdirAll(filepath.Dir(destination), 0755); err != nil { return err }
	if err := os.WriteFile(destination, data, mode); err != nil { return err }
	n := int64(len(data)); cp.c.FilesRead++; cp.c.FilesCopied++; cp.c.HashOperations++; cp.c.BytesRead += n; cp.c.BytesCopied += n; cp.c.BytesHashed += n
	cp.objects[path] = objectIdentity{digest, n, cp.stage}; return nil
}
func recordLine(hash io.Writer, relative, kind string, st *syscall.Stat_t, extra ...string) {
	fields := []string{relative, kind, strconv.FormatUint(uint64(st.Mode), 10), strconv.Itoa(int(st.Uid)), strconv.Itoa(int(st.Gid))}
	fields = append(fields, extra...); _, _ = hash.Write([]byte(strings.Join(fields, "\x00")+"\n"))
}
func (cp *copier) tree(source string, policy treePolicy) error { return cp.treeFrom(source, source, policy) }
func (cp *copier) treeFrom(source, lexicalRoot string, policy treePolicy) error {
	destination := filepath.Join(cp.root, strings.TrimPrefix(lexicalRoot, "/"))
	paths := []string{source}
	err := filepath.WalkDir(source, func(path string, entry fs.DirEntry, walkErr error) error { if walkErr != nil{return walkErr}; if path != source { paths=append(paths,path) }; return nil })
	if err != nil { return err }
	sort.Slice(paths, func(i,j int) bool { li, _:=filepath.Rel(source,paths[i]); lj,_:=filepath.Rel(source,paths[j]); if li=="."{li="."}; if lj=="."{lj="."}; return filepath.ToSlash(li)<filepath.ToSlash(lj) })
	h := sha256.New(); dirs, files, links := 0,0,0
	for _, path := range paths {
		rel, _ := filepath.Rel(source,path); rel=filepath.ToSlash(rel); if rel==""{rel="."}
		info, err := os.Lstat(path); if err != nil{return err}; st:=info.Sys().(*syscall.Stat_t)
		target:=destination; if rel!="."{target=filepath.Join(destination,filepath.FromSlash(rel))}
		switch st.Mode&syscall.S_IFMT {
		case syscall.S_IFDIR:
			dirs++; if err:=os.MkdirAll(target,info.Mode().Perm());err!=nil{return err}; if err:=os.Chown(target,int(st.Uid),int(st.Gid));err!=nil{return err}; if err:=syscall.Chmod(target,st.Mode&07777);err!=nil{return err}; recordLine(h,rel,"d",st)
		case syscall.S_IFREG:
			files++; digest,size,err:=stableCopy(path,target,"",&cp.c);if err!=nil{return err}; recordLine(h,rel,"f",st,strconv.FormatInt(size,10),digest); lexical:=lexicalRoot;if rel!="."{lexical=filepath.Join(lexicalRoot,filepath.FromSlash(rel))};cp.objects[lexical]=objectIdentity{digest,size,cp.stage}
		case syscall.S_IFLNK:
			links++; value,err:=os.Readlink(path);if err!=nil{return err}; if err:=os.MkdirAll(filepath.Dir(target),0755);err!=nil{return err};if err:=os.Symlink(value,target);err!=nil{return err};if err:=os.Lchown(target,int(st.Uid),int(st.Gid));err!=nil{return err};recordLine(h,rel,"l",st,value)
		default: return fmt.Errorf("forbidden source type: %s",path)
		}
	}
	digest:=hexDigest(h.Sum(nil)); if digest!=policy.SHA256||dirs!=policy.Dirs||files!=policy.Files||links!=policy.Links{return fmt.Errorf("reviewed tree mismatch: %s digest=%s counts=%d/%d/%d",source,digest,dirs,files,links)}
	return nil
}
func copySymlink(root,path,target string) error { destination:=filepath.Join(root,strings.TrimPrefix(path,"/"));if err:=os.MkdirAll(filepath.Dir(destination),0755);err!=nil{return err};return os.Symlink(target,destination) }
func readStable(path string) ([]byte,string,error) { return readStableMode(path,true) }
func readStableMode(path string, noFollow bool) ([]byte,string,error) {
	flags:=syscall.O_RDONLY|syscall.O_CLOEXEC;if noFollow{flags|=syscall.O_NOFOLLOW};fd,err:=syscall.Open(path,flags,0);if err!=nil{return nil,"",err};f:=os.NewFile(uintptr(fd),path);defer f.Close();var a,b syscall.Stat_t
	if err:=syscall.Fstat(fd,&a);err!=nil{return nil,"",err};if a.Mode&syscall.S_IFMT!=syscall.S_IFREG{return nil,"",fmt.Errorf("stable source is not regular: %s",path)};data,err:=io.ReadAll(f);if err!=nil{return nil,"",err};if err:=syscall.Fstat(fd,&b);err!=nil{return nil,"",err};if a.Dev!=b.Dev||a.Ino!=b.Ino||a.Size!=b.Size||a.Mtim!=b.Mtim||a.Ctim!=b.Ctim{return nil,"",fmt.Errorf("file unstable: %s",path)};sum:=sha256.Sum256(data);return data,hexDigest(sum[:]),nil
}
func rejectHostHwcaps() error {
	for _, base:=range []string{"/usr/lib/x86_64-linux-gnu","/usr/lib/x86_64-linux-gnu/systemd","/usr/lib"} {
		for _, level:=range []string{"x86-64-v2","x86-64-v3","x86-64-v4"} { p:=filepath.Join(base,"glibc-hwcaps",level); entries,err:=os.ReadDir(p);if err==nil&&len(entries)>0{return fmt.Errorf("EXPECTED_ABSENT hwcaps candidate present: %s",p)};if err!=nil&&!os.IsNotExist(err){return err} }
	}
	return nil
}
func mountTmpfs(source,target,size string) error { if err:=ensureDir(target,0700);err!=nil{return err};return syscall.Mount(source,target,"tmpfs",syscall.MS_NOSUID|syscall.MS_NODEV,"mode=0700,size="+size) }
func remountRO(target string) error { return syscall.Mount("",target,"",syscall.MS_REMOUNT|syscall.MS_RDONLY|syscall.MS_NOSUID|syscall.MS_NODEV,"") }
func randomToken() string { data:=make([]byte,16);f,_:=os.Open("/dev/urandom");if f!=nil{_,_=io.ReadFull(f,data);_ = f.Close()};return fmt.Sprintf("%d-%s",os.Getpid(),hex.EncodeToString(data)) }
func mountHas(source,mountpoint string, ro bool) bool {
	data,err:=os.ReadFile("/proc/self/mountinfo");if err!=nil{return false}
	for _,line:=range strings.Split(string(data),"\n") { parts:=strings.SplitN(line," - ",2);if len(parts)!=2{continue};left:=strings.Fields(parts[0]);right:=strings.Fields(parts[1]);if len(left)<6||len(right)<2{continue};if left[4]==mountpoint&&right[1]==source { hasRO:=false;for _,o:=range strings.Split(left[5],","){if o=="ro"{hasRO=true}};return !ro||hasRO } }
	return false
}
func validatePinAndCopyToolchain(cp *copier) (pinDocument,error) {
	var pin pinDocument; pinData,pinDigest,err:=readStable(pinHost);if err!=nil{return pin,err};if err=json.Unmarshal(pinData,&pin);err!=nil{return pin,err}
	if pin.SchemaVersion!="thebitlab.private-runtime-poc-pin.v1"||len(pin.LauncherSHA256)!=64||len(pin.ToolchainManifestSHA256)!=64{return pin,errors.New("private POC pin invalid")}
	selfData,selfDigest,err:=readStableMode("/proc/self/exe",false);if err!=nil{return pin,err};if selfDigest!=pin.LauncherSHA256{return pin,errors.New("static POC binary differs from external pin")}
	if err:=cp.bytesFile("/usr/lib/thebitlab/private-runtime-broker",selfData,selfDigest,0755);err!=nil{return pin,err}
	cp.objects["/usr/sbin/thebitlab-private-runtime-poc"]=objectIdentity{selfDigest,int64(len(selfData)),cp.stage}
	toolRoot:=filepath.Join("/usr/lib/thebitlab/pilot-tools",pin.ToolchainID);manifestPath:=filepath.Join(toolRoot,"pilot-toolchain-manifest.json")
	manifestData,manifestDigest,err:=readStable(manifestPath);if err!=nil{return pin,err};if manifestDigest!=pin.ToolchainManifestSHA256{return pin,errors.New("toolchain manifest differs from pin")}
	var document toolchainDocument;if err:=json.Unmarshal(manifestData,&document);err!=nil{return pin,err};if document.SchemaVersion!="thebitlab.pilot-toolchain.v1"||document.ToolchainID!=pin.ToolchainID||document.ReleaseCommit!=pin.ReleaseCommit{return pin,errors.New("toolchain identity mismatch")}
	manifestLexical:=filepath.Join("/usr/lib/thebitlab/pilot-tools",pin.ToolchainID,"pilot-toolchain-manifest.json");if err:=cp.bytesFile(manifestLexical,manifestData,manifestDigest,0644);err!=nil{return pin,err}
	names:=make([]string,0,len(document.Files));for name:=range document.Files{if filepath.IsAbs(name)||strings.Contains(name,"..")||strings.ContainsAny(name,"\x00\n\r"){return pin,errors.New("toolchain path invalid")};names=append(names,name)};sort.Strings(names)
	for _,name:=range names{if err:=cp.file(filepath.Join(toolRoot,filepath.FromSlash(name)),document.Files[name]);err!=nil{return pin,err}}
	if err:=cp.bytesFile(pinHost,pinData,pinDigest,0644);err!=nil{return pin,err}
	return pin,nil
}
func makeSkeleton(root string) error {
	for _,p:=range []string{"etc/ssl","usr/bin","usr/sbin","usr/lib","usr/local/lib","usr/share","var/log/nginx","var/lib/nginx","run/thebitlab-private-runtime-poc/control","proc","sys","dev","tmp",".oldroot"}{if err:=os.MkdirAll(filepath.Join(root,p),0755);err!=nil{return err}}
	if err:=os.WriteFile(filepath.Join(root,"dev/null"),nil,0600);err!=nil{return err}
	for path,target:=range map[string]string{"bin":"usr/bin","sbin":"usr/sbin","lib":"usr/lib","lib64":"usr/lib64"}{if err:=os.Symlink(target,filepath.Join(root,path));err!=nil{return err}}
	return nil
}
func stage0() (result error) {
	if os.Geteuid()!=0{return errors.New("private runtime POC requires root")};if filepath.Clean(os.Args[0])!=launcherHost{return errors.New("private POC requires canonical static launcher")};probeMode:=len(os.Args)>1&&os.Args[1]=="poc-probe"
	if _,err:=os.Lstat(stateHost);err==nil{return errors.New("private POC state already exists")};if err:=rejectHostHwcaps();err!=nil{return err}
	start:=time.Now();cpuStart:=cpuSeconds();token:=randomToken();if err:=ensureDir(runtimeHost,0700);err!=nil{return err};if err:=ensureDir(controlHost,0700);err!=nil{return err}
	if err:=mountTmpfs(s0Source,s0Host,"256m");err!=nil{return err};defer func(){if result!=nil{_ = syscall.Unmount(s0Host,syscall.MNT_DETACH)}}()
	cp:=copier{s0Host,counters{},map[string]objectIdentity{},"S0"};if err:=makeSkeleton(s0Host);err!=nil{return err}
	paths:=make([]string,0,len(treePolicies));for p:=range treePolicies{paths=append(paths,p)};sort.Strings(paths);for _,p:=range paths{if err:=cp.tree(p,treePolicies[p]);err!=nil{return err}}
	files:=make([]string,0,len(s0Files));for p:=range s0Files{files=append(files,p)};sort.Strings(files);for _,p:=range files{if err:=cp.file(p,s0Files[p]);err!=nil{return err}}
	if err:=copySymlink(s0Host,"/usr/bin/python3","python3.12");err!=nil{return err}
	// /lib64 -> usr/lib64 already exists; provide the reviewed PT_INTERP spelling below it.
	if err:=os.MkdirAll(filepath.Join(s0Host,"usr/lib64"),0755);err!=nil{return err};if err:=os.Symlink("../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2",filepath.Join(s0Host,"usr/lib64/ld-linux-x86-64.so.2"));err!=nil{return err}
	pin,err:=validatePinAndCopyToolchain(&cp);if err!=nil{return err}
	wall:=time.Since(start).Seconds();m:=metrics{"S0",wall,cpuSeconds()-cpuStart,cp.c,len(cp.objects),0,0,0,"/lib64/ld-linux-x86-64.so.2","reviewed Noble stdlib + dist-packages + native tree",0,0}
	self:=cp.objects["/usr/sbin/thebitlab-private-runtime-poc"].SHA256;doc:=manifest{"thebitlab.private-runtime-poc.v1",token,s0Source,s0Host,cp.objects,m,self,pin.ToolchainID,pin.ToolchainManifestSHA256}
	if err:=writeJSON(filepath.Join(s0Host,".thebitlab-s0-manifest.json"),doc);err!=nil{return err};if err:=writeJSON(stateHost,map[string]any{"schema":"thebitlab.private-runtime-poc-state.v1","token":token,"s0_source":s0Source,"s0_manifest_sha256":hashJSON(doc),"toolchain_id":pin.ToolchainID});err!=nil{return err}
	if err:=remountRO(s0Host);err!=nil{return err};if !mountHas(s0Source,s0Host,true){return errors.New("S0 mount is not kernel-witnessed RO tmpfs")}
	if !probeMode { if _,err:=syscall.ForkExec("/proc/self/exe",[]string{launcherHost,"poc-stage1-server",token},&syscall.ProcAttr{Dir:"/",Env:[]string{},Files:[]uintptr{0,1,2}});err!=nil{return fmt.Errorf("static stage1 server start failed: %w",err)} }
	// The POC stage0 has the same one-way namespace contract as production.
	runtime.LockOSThread()
	if err:=syscall.Unshare(syscall.CLONE_NEWNS);err!=nil{runtime.UnlockOSThread();return err};if err:=syscall.Mount("","/","",syscall.MS_REC|syscall.MS_PRIVATE,"");err!=nil{return err}
	// Only proc, null and a data-only control mount cross into the private root.
	if err:=syscall.Mount("proc",filepath.Join(s0Host,"proc"),"proc",syscall.MS_NOSUID|syscall.MS_NODEV|syscall.MS_NOEXEC,"");err!=nil{return err}
	if err:=syscall.Mount(controlHost,filepath.Join(s0Host,"run/thebitlab-private-runtime-poc/control"),"",syscall.MS_BIND,"");err!=nil{return err}
	if err:=syscall.Mount("/dev/null",filepath.Join(s0Host,"dev/null"),"",syscall.MS_BIND,"");err!=nil{return err}
	if err:=syscall.Chdir(s0Host);err!=nil{return err};if err:=syscall.PivotRoot(".",".oldroot");err!=nil{return err};if err:=syscall.Chdir("/");err!=nil{return err};if err:=syscall.Unmount("/.oldroot",syscall.MNT_DETACH);err!=nil{return err}
	closeExtraFDs()
	toolRoot:=filepath.Join("/usr/lib/thebitlab/pilot-tools",pin.ToolchainID)
	code:=`import json,os,pathlib,subprocess,sys,time
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
	loader:="/lib64/ld-linux-x86-64.so.2";mode:="full";if probeMode{mode="probe"};args:=[]string{loader,"--inhibit-cache","--library-path","/usr/lib/x86_64-linux-gnu","/usr/bin/python3.12","-I","-B","-c",code,toolRoot,token,mode}
	env:=[]string{"HOME=/root","LANG=C","LC_ALL=C","PATH=/usr/sbin:/usr/bin:/sbin:/bin"}
	return syscall.Exec(loader,args,env)
}
func closeExtraFDs(){entries,_:=os.ReadDir("/proc/self/fd");for _,e:=range entries{n,err:=strconv.Atoi(e.Name());if err==nil&&n>2{_ = syscall.Close(n)}}}
func hashJSON(value any) string {data,_:=json.Marshal(value);sum:=sha256.Sum256(data);return hexDigest(sum[:])}
func hostPath(path string) string { return "/proc/1/root"+path }
func setnsPID1() error { fd,err:=syscall.Open("/proc/1/ns/mnt",syscall.O_RDONLY|syscall.O_CLOEXEC,0);if err!=nil{return err};defer syscall.Close(fd);_,_,errno:=syscall.Syscall(308,uintptr(fd),uintptr(syscall.CLONE_NEWNS),0);if errno!=0{return errno};return nil }
func loadS0(token string)(manifest,error){var doc manifest;data,err:=os.ReadFile(hostPath(s0Host+"/.thebitlab-s0-manifest.json"));if err!=nil{return doc,err};if err:=json.Unmarshal(data,&doc);err!=nil{return doc,err};if doc.Token!=token||doc.MountSource!=s0Source||doc.Root!=s0Host{return doc,errors.New("S0 manifest identity mismatch")};if !mountHas(s0Source,s0Host,true){return doc,errors.New("S0 kernel mount witness mismatch")};var state map[string]any;raw,err:=os.ReadFile(hostPath(stateHost));if err!=nil{return doc,err};if json.Unmarshal(raw,&state)!=nil||state["token"]!=token||state["s0_manifest_sha256"]!=hashJSON(doc){return doc,errors.New("S0 state is not authority-bound")};return doc,nil}
func n2UnitBytes() []byte {
	broker:=s0Host+"/usr/lib/thebitlab/private-runtime-broker"
	return []byte("# Exact TheBitLab N2 private-runtime POC unit; issue 704\n[Unit]\nDescription=TheBitLab private runtime N2 nginx POC\nAfter=network.target\n[Service]\nType=forking\nPIDFile="+runtimeHost+"/runtime/run/nginx.pid\nExecStartPre="+broker+" poc-private-exec /usr/sbin/nginx -t -q -g 'daemon on; master_process on;'\nExecStartPre="+broker+" poc-start-barrier\nExecStart="+broker+" poc-private-exec /usr/sbin/nginx -g 'daemon on; master_process on;'\nExecReload="+broker+" poc-private-exec /usr/sbin/nginx -g 'daemon on; master_process on;' -s reload\nExecStop=-"+broker+" poc-private-exec /usr/sbin/start-stop-daemon --quiet --stop --retry QUIT/5 --pidfile /run/nginx.pid\nTimeoutStopSec=5\nKillMode=mixed\n")
}
func stage1Build(token string) (result error) {
	if os.Geteuid()!=0{return errors.New("stage1 broker requires root")};if token==""{return errors.New("transaction selector absent")};s0,err:=loadS0(token);if err!=nil{return err}
	start:=time.Now();cpuStart:=cpuSeconds();s1Target:=hostPath(s1Host);if err:=mountTmpfs(s1Source,s1Target,"32m");err!=nil{return err};defer func(){if result!=nil{_ = syscall.Unmount(s1Target,syscall.MNT_DETACH)}}()
	cp:=copier{s1Target,counters{},map[string]objectIdentity{},"S1"};for _,p:=range []string{"etc","usr/lib","usr/share","usr/sbin","var/log/nginx","var/lib/nginx","run","tmp"}{if err:=os.MkdirAll(filepath.Join(s1Target,p),0755);err!=nil{return err}}
	overlap,overlapBytes:=0,int64(0);paths:=make([]string,0,len(s1TreePolicies));for p:=range s1TreePolicies{paths=append(paths,p)};sort.Strings(paths);for _,p:=range paths{if err:=cp.treeFrom(hostPath(p),p,s1TreePolicies[p]);err!=nil{return err}}
	for lex,id:=range cp.objects{if existing,ok:=s0.Objects[lex];ok {overlap++;overlapBytes+=id.Size;if existing.SHA256!=id.SHA256{return fmt.Errorf("same path has different identity: %s",lex)};return fmt.Errorf("S1 policy duplicates S0 identity: %s",lex)}}
	filePaths:=make([]string,0,len(s1Files));for p:=range s1Files{filePaths=append(filePaths,p)};sort.Strings(filePaths);for _,p:=range filePaths{if existing,ok:=s0.Objects[p];ok{overlap++;overlapBytes+=existing.Size;continue};digest,size,err:=stableCopy(hostPath(p),filepath.Join(s1Target,strings.TrimPrefix(p,"/")),s1Files[p],&cp.c);if err!=nil{return err};cp.objects[p]=objectIdentity{digest,size,"S1"}}
	n2Source:=filepath.Join(s1Target,"manager/thebitlab-private-n2-poc.service");if err:=os.MkdirAll(filepath.Dir(n2Source),0700);err!=nil{return err};if err:=os.WriteFile(n2Source,n2UnitBytes(),0644);err!=nil{return err}
	m:=metrics{"S1",time.Since(start).Seconds(),cpuSeconds()-cpuStart,cp.c,len(cp.objects),overlap,overlapBytes,0,"","",0,0};doc:=manifest{"thebitlab.private-runtime-poc.v1",token,s1Source,s1Host,cp.objects,m,s0.SelfSHA256,"",""};if err:=writeJSON(filepath.Join(s1Target,".thebitlab-s1-manifest.json"),doc);err!=nil{return err};if err:=remountRO(s1Target);err!=nil{return err};if !mountHas(s1Source,s1Host,true){return errors.New("S1 mount is not kernel-witnessed RO tmpfs")}
	compositionStart:=time.Now();merged:=hostPath(mergedHost);if err:=ensureDir(merged,0700);err!=nil{return err};options:="lowerdir="+hostPath(s1Host)+":"+hostPath(s0Host);if err:=syscall.Mount("overlay",merged,"overlay",syscall.MS_RDONLY|syscall.MS_NOSUID|syscall.MS_NODEV,options);err!=nil{return fmt.Errorf("read-only multi-lower overlay rejected: %w",err)};m.CompositionSeconds=time.Since(compositionStart).Seconds()
	managerStart:=time.Now();runtime:=hostPath(runtimeHost+"/runtime");for _,p:=range []string{"run","log/nginx","cache/nginx"}{if err:=os.MkdirAll(filepath.Join(runtime,p),0755);err!=nil{return err}}
	drop:=hostPath(managerDrop);if entries,err:=os.ReadDir(drop);err==nil&&len(entries)!=0{return errors.New("manager drop-in directory has unexpected siblings")};if err:=mountTmpfs(managerSource,drop,"1m");err!=nil{return err}
	content:=[]byte("# Exact TheBitLab private-runtime POC drop-in; issue 704\n[Service]\nRootDirectory="+mergedHost+"\nPIDFile="+runtimeHost+"/runtime/run/nginx.pid\nBindPaths="+runtimeHost+"/runtime/run:/run\nBindPaths="+runtimeHost+"/control:/run/thebitlab-private-runtime-poc/control\nBindPaths="+runtimeHost+"/runtime/log/nginx:/var/log/nginx\nBindPaths="+runtimeHost+"/runtime/cache/nginx:/var/lib/nginx\nExecStartPre=/usr/lib/thebitlab/private-runtime-broker poc-start-barrier\n")
	if err:=os.WriteFile(filepath.Join(drop,"70-thebitlab-private-runtime.conf"),content,0644);err!=nil{return err};if err:=remountRO(drop);err!=nil{return err}
	n2Target:=hostPath("/run/systemd/system/thebitlab-private-n2-poc.service");if err:=os.WriteFile(n2Target,nil,0644);err!=nil{return err};if err:=syscall.Mount(hostPath(s1Host+"/manager/thebitlab-private-n2-poc.service"),n2Target,"",syscall.MS_BIND,"");err!=nil{return err};if err:=syscall.Mount("",n2Target,"",syscall.MS_BIND|syscall.MS_REMOUNT|syscall.MS_RDONLY,"");err!=nil{return err};m.ManagerFenceSeconds=time.Since(managerStart).Seconds();doc.Metrics=m;if err:=writeJSON(hostPath(controlHost+"/s1-metrics.json"),doc);err!=nil{return err};return nil
}
func stage1Client() error {
	token:=os.Getenv("THEBITLAB_PRIVATE_POC_TOKEN");if token==""{return errors.New("transaction selector absent")};control:=filepath.Join(runtimeHost,"control");if err:=os.WriteFile(filepath.Join(control,"broker-request"),[]byte(token+"\n"),0600);err!=nil{return err};deadline:=time.Now().Add(180*time.Second);for time.Now().Before(deadline){data,err:=os.ReadFile(filepath.Join(control,"broker-server-result"));if err==nil{var result map[string]string;if json.Unmarshal(data,&result)!=nil||result["token"]!=token{return errors.New("static broker result identity mismatch")};if result["error"]!=""{return errors.New(result["error"])};return nil};time.Sleep(5*time.Millisecond)};return errors.New("timeout static stage1 server")
}
func stage1Server(token string) error {
	control:=filepath.Join(runtimeHost,"control");deadline:=time.Now().Add(180*time.Second);for time.Now().Before(deadline){data,err:=os.ReadFile(filepath.Join(control,"broker-request"));if err==nil{info,statErr:=os.Lstat(filepath.Join(control,"broker-request"));if statErr!=nil||!info.Mode().IsRegular()||info.Mode().Perm()!=0600{return errors.New("broker request metadata invalid")};if strings.TrimSpace(string(data))!=token{return errors.New("broker request selector mismatch")};buildErr:=stage1Build(token);detail:="";if buildErr!=nil{detail=buildErr.Error()};if err:=writeJSON(filepath.Join(control,"broker-server-result"),map[string]string{"token":token,"error":detail});err!=nil{return err};return buildErr};time.Sleep(5*time.Millisecond)};return errors.New("timeout waiting sealed stage1 client")
}
func startBarrier() error {
	control:=filepath.Join(runtimeHost,"control");if err:=os.WriteFile(filepath.Join(control,"start-barrier-ready"),[]byte("ready\n"),0600);err!=nil{return err};deadline:=time.Now().Add(30*time.Second);for time.Now().Before(deadline){if _,err:=os.Lstat(filepath.Join(control,"start-continue"));err==nil{return nil};time.Sleep(5*time.Millisecond)};return errors.New("timeout test-only nginx start barrier")
}
func privateExec() error {
	if len(os.Args)<3{return errors.New("private exec command absent")};evidence,err:=os.OpenFile(filepath.Join(controlHost,fmt.Sprintf("private-exec-%d",os.Getpid())),os.O_WRONLY|os.O_CREATE|os.O_EXCL,0600);if err!=nil{return err}
	// A successful mount unshare is one-way. Keep this helper on the same OS
	// thread until target Exec or fail-closed process termination.
	runtime.LockOSThread()
	if err:=syscall.Unshare(syscall.CLONE_NEWNS);err!=nil{runtime.UnlockOSThread();_ = evidence.Close();return err};if err:=syscall.Mount("","/","",syscall.MS_REC|syscall.MS_PRIVATE,"");err!=nil{return err};for _,pair:=range [][2]string{{runtimeHost+"/runtime/run",mergedHost+"/run"},{runtimeHost+"/runtime/log/nginx",mergedHost+"/var/log/nginx"},{runtimeHost+"/runtime/cache/nginx",mergedHost+"/var/lib/nginx"},{"/dev/null",mergedHost+"/dev/null"}}{if err:=syscall.Mount(pair[0],pair[1],"",syscall.MS_BIND,"");err!=nil{return fmt.Errorf("private exec data bind %s: %w",pair[1],err)}};if err:=syscall.Chdir(mergedHost);err!=nil{return err};if err:=syscall.PivotRoot(".",".oldroot");err!=nil{return err};if err:=syscall.Chdir("/");err!=nil{return err};if err:=syscall.Unmount("/.oldroot",syscall.MNT_DETACH);err!=nil{return err};_,rootCrypto,cryptoErr:=readStable("/usr/lib/x86_64-linux-gnu/libcrypto.so.3");_,_=fmt.Fprintf(evidence,"command=%s root_libcrypto=%s error=%v root=%s\n",os.Args[2],rootCrypto,cryptoErr,mustReadlink("/proc/self/root"));_ = evidence.Close();closeExtraFDs();loader:="/lib64/ld-linux-x86-64.so.2";arguments:=[]string{loader,"--inhibit-cache","--library-path","/usr/lib/x86_64-linux-gnu",os.Args[2]};arguments=append(arguments,os.Args[3:]...);return syscall.Exec(loader,arguments,[]string{"HOME=/root","LANG=C","LC_ALL=C","PATH=/usr/sbin:/usr/bin:/sbin:/bin"})
}
func mustReadlink(path string) string { value,err:=os.Readlink(path);if err!=nil{return "ERROR:"+err.Error()};return value }
func cleanup() error {
	for _,p:=range []string{"/run/systemd/system/thebitlab-private-n2-poc.service",managerDrop,mergedHost,s1Host,s0Host}{_ = syscall.Unmount(p,syscall.MNT_DETACH)}
	_ = os.Remove("/run/systemd/system/thebitlab-private-n2-poc.service");_ = os.RemoveAll(runtimeHost);return nil
}
func main(){var err error;if len(os.Args)>1&&os.Args[1]=="poc-stage1"{err=stage1Client()}else if len(os.Args)>2&&os.Args[1]=="poc-stage1-server"{err=stage1Server(os.Args[2])}else if len(os.Args)>1&&os.Args[1]=="poc-start-barrier"{err=startBarrier()}else if len(os.Args)>1&&os.Args[1]=="poc-private-exec"{err=privateExec()}else if len(os.Args)>1&&os.Args[1]=="poc-cleanup"{err=cleanup()}else{err=stage0()};if err!=nil{fmt.Fprintln(os.Stderr,"PRIVATE-RUNTIME-POC:",err);os.Exit(2)}}

// Keep the compiler from silently accepting accidental dependence on bytes semantics changes.
var _ = bytes.Equal
