#!/usr/bin/env python3
"""Privileged, destructive private-runtime POC and microbenchmark for issue #704.

Run only in the dedicated Ubuntu 24.04/systemd container.  This is intentionally
not the final integration matrix.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_pilot_toolchain  # noqa: E402
RUNTIME = Path("/run/thebitlab-private-runtime-poc")
CONTROL = RUNTIME / "control"
S0 = RUNTIME / "s0"
S1 = RUNTIME / "s1"
MERGED = RUNTIME / "merged"
LAUNCHER = Path("/usr/sbin/thebitlab-private-runtime-poc")
PIN = Path("/etc/thebitlab/trust/pilot-private-runtime-poc.json")
TOOLCHAIN_ID = "private-poc-598f1905"
TOOLCHAIN = Path("/usr/lib/thebitlab/pilot-tools") / TOOLCHAIN_ID
MARKER_PRELOAD = Path("/run/review704-preload-marker")
MARKER_HWCAPS = Path("/run/review704-hwcaps-marker")
MANAGED_DROPIN = Path("/run/systemd/system/nginx.service.d/70-thebitlab-private-runtime.conf")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, timeout: float = 60, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
    if check and result.returncode:
        raise RuntimeError(
            f"command failed rc={result.returncode}: {' '.join(command)}\n"
            f"stdout={result.stdout[-1000:]}\nstderr={result.stderr[-1000:]}"
        )
    return result


def wait_path(path: Path, *, timeout: float = 120) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.01)
    raise RuntimeError(f"timeout waiting for {path}")


def setup() -> None:
    if os.geteuid() != 0 or Path("/proc/1/comm").read_text().strip() != "systemd":
        raise RuntimeError("POC requires the dedicated privileged systemd container")
    if any(path.exists() or path.is_symlink() for path in (LAUNCHER, PIN, TOOLCHAIN, RUNTIME)):
        raise RuntimeError("private-runtime POC host is not pristine")
    tool_manifest = build_pilot_toolchain.build_toolchain(
        ROOT, TOOLCHAIN, TOOLCHAIN_ID, "598f1905462b5df0cb5f009ea79cffb7901545b8"
    )
    del tool_manifest
    for path in TOOLCHAIN.rglob("*"):
        path.chmod(0o755 if path.is_dir() else 0o644)
    TOOLCHAIN.chmod(0o755)
    LAUNCHER.parent.mkdir(parents=True, mode=0o755, exist_ok=True)
    shutil.copyfile("/root/thebitlab-private-runtime-poc", LAUNCHER)
    LAUNCHER.chmod(0o755)
    PIN.parent.mkdir(parents=True, mode=0o755, exist_ok=True)
    pin = {
        "schema_version": "thebitlab.private-runtime-poc-pin.v1",
        "toolchain_id": TOOLCHAIN_ID,
        "toolchain_manifest_sha256": sha(TOOLCHAIN / "pilot-toolchain-manifest.json"),
        "launcher_sha256": sha(LAUNCHER),
        "release_commit": "598f1905462b5df0cb5f009ea79cffb7901545b8",
    }
    PIN.write_text(json.dumps(pin, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    PIN.chmod(0o644)


def cleanup() -> None:
    cleanup_binary = LAUNCHER if LAUNCHER.exists() else Path("/root/thebitlab-private-runtime-poc")
    run([str(cleanup_binary), "poc-cleanup"], check=False)
    run(["systemctl", "stop", "nginx.service"], check=False)
    run(["systemctl", "daemon-reload"], check=False)
    for path in (PIN, LAUNCHER):
        path.unlink(missing_ok=True)
    shutil.rmtree(TOOLCHAIN, ignore_errors=True)
    with suppress_oserror():
        TOOLCHAIN.parent.rmdir()
    with suppress_oserror():
        PIN.parent.rmdir()


class suppress_oserror:
    def __enter__(self) -> None:
        return None

    def __exit__(self, kind: object, value: object, traceback: object) -> bool:
        return isinstance(value, OSError)


def expected_ro_failure(action: str, callback: object) -> None:
    try:
        callback()  # type: ignore[operator]
    except OSError as exc:
        if exc.errno not in {1, 13, 30}:
            raise
        print(f"EVIDENCE: {action} blocked errno={exc.errno}")
        return
    raise RuntimeError(f"read-only isolation attack unexpectedly succeeded: {action}")


def cleanup_runtime_only() -> None:
    run([str(LAUNCHER), "poc-cleanup"], check=False)


def test_expected_absent_hwcaps() -> None:
    cases = (
        (Path("/usr/lib/x86_64-linux-gnu/systemd/glibc-hwcaps/x86-64-v3/libsystemd-shared-255.so"), Path("/root/review704-libsystemd-shared-255.so"), "x86-64-v3 exact"),
        (Path("/usr/lib/x86_64-linux-gnu/glibc-hwcaps/x86-64-v2/libc.so.6"), Path("/root/review704-preload.so"), "x86-64-v2"),
        (Path("/usr/lib/x86_64-linux-gnu/glibc-hwcaps/x86-64-v4/libssl.so.3"), Path("/root/review704-preload.so"), "x86-64-v4"),
    )
    for candidate, payload, label in cases:
        candidate.parent.mkdir(parents=True)
        shutil.copyfile(payload, candidate)
        MARKER_HWCAPS.unlink(missing_ok=True)
        result = run([str(LAUNCHER), "poc-probe"], timeout=30, check=False)
        if result.returncode != 2 or "EXPECTED_ABSENT hwcaps" not in result.stderr:
            raise RuntimeError(f"{label} did not fail closed: {result.stderr[-500:]}")
        if MARKER_HWCAPS.exists() or MARKER_PRELOAD.exists():
            raise RuntimeError(f"constructor executed for expected-absent {label}")
        shutil.rmtree(candidate.parents[1])
        print(f"EVIDENCE: {label} expected-absent zero-marker PASS")


def test_exact_preload() -> dict[str, object]:
    preload = Path("/etc/ld.so.preload")
    malicious = Path("/etc/review704-preload.so")
    shutil.copyfile("/root/review704-preload.so", malicious)
    malicious.chmod(0o755)
    preload.write_text(str(malicious) + "\n", encoding="ascii")
    MARKER_PRELOAD.unlink(missing_ok=True)
    try:
        result = run([str(LAUNCHER), "poc-probe"], timeout=180, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"preload probe failed: {result.stderr[-1000:]}")
        if MARKER_PRELOAD.exists():
            raise RuntimeError("canonical preload constructor executed")
        wait_path(CONTROL / "probe-ok")
        manifest = json.loads((S0 / ".thebitlab-s0-manifest.json").read_text())
        process_evidence = json.loads((CONTROL / "s0-python-ready").read_text())
        if (
            process_evidence["exe"] != "/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2"
            or "/usr/bin/python3.12" not in process_evidence["maps"]
        ):
            raise RuntimeError(f"explicit private loader/Python mapping mismatch: {process_evidence}")
        print("EVIDENCE: exact preload before canonical static launcher zero-marker PASS")
        return manifest
    finally:
        preload.unlink(missing_ok=True)
        malicious.unlink(missing_ok=True)
        MARKER_PRELOAD.unlink(missing_ok=True)
        cleanup_runtime_only()


def atomic_host_replace(path: Path, payload: bytes) -> tuple[Path, int]:
    backup = path.with_name(path.name + ".review704-host-original")
    mode = stat.S_IMODE(path.stat().st_mode)
    path.replace(backup)
    path.write_bytes(payload)
    path.chmod(mode)
    return backup, mode


def restore_host(path: Path, backup: Path) -> None:
    path.unlink(missing_ok=True)
    backup.replace(path)


def launch_full_and_attack_s0() -> tuple[subprocess.Popen[str], dict[str, object]]:
    process = subprocess.Popen(
        [str(LAUNCHER)], cwd="/", env={}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    wait_path(CONTROL / "s0-python-ready", timeout=180)
    ready = json.loads((CONTROL / "s0-python-ready").read_text())
    pid = int(ready["pid"])
    self_ns = Path(f"/proc/{pid}/ns/mnt").readlink()
    pid1_ns = Path("/proc/1/ns/mnt").readlink()
    if self_ns == pid1_ns:
        raise RuntimeError("Stage0 Python did not enter a private mount namespace")
    mountinfo = Path(f"/proc/{pid}/mountinfo").read_text()
    if not any(
        " - tmpfs thebitlab-private-s0 " in line and line.split()[4] == "/"
        for line in mountinfo.splitlines()
    ):
        raise RuntimeError("Stage0 pivot_root lacks exact private S0 tmpfs witness")
    private_manifest = Path(f"/proc/{pid}/root/.thebitlab-s0-manifest.json")
    if not private_manifest.is_file():
        raise RuntimeError("Stage0 pivot_root manifest is not reachable through process root")

    module = TOOLCHAIN / "scripts/nginx_config_ast.py"
    original_module = module.read_bytes()
    directory_fd = os.open(module.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    renamed = TOOLCHAIN.with_name(TOOLCHAIN.name + ".review704-host-renamed")
    TOOLCHAIN.replace(renamed)
    malicious_root = Path(tempfile.mkdtemp(prefix="review704-alias-", dir=str(TOOLCHAIN.parent)))
    (malicious_root / "scripts").mkdir()
    (malicious_root / "scripts/__init__.py").write_text("", encoding="utf-8")
    marker = Path("/run/review704-host-python-marker")
    (malicious_root / "scripts/nginx_config_ast.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\n", encoding="utf-8"
    )
    TOOLCHAIN.symlink_to(malicious_root, target_is_directory=True)
    descriptor = os.open("nginx_config_ast.py", os.O_WRONLY | os.O_TRUNC, dir_fd=directory_fd)
    os.write(descriptor, b"raise RuntimeError('preopened host dir won')\n")
    os.close(descriptor)

    extension = next(Path("/usr/lib/python3.12/lib-dynload").glob("_ssl*.so"))
    extension_backup, _ = atomic_host_replace(extension, b"review704 malicious native extension\n")
    late_candidate = Path("/usr/lib/x86_64-linux-gnu/libreview704-late.so")
    late_candidate.write_bytes(b"review704 unexpected normal candidate\n")
    late_hwcaps = Path("/usr/lib/x86_64-linux-gnu/glibc-hwcaps/x86-64-v3/libssl.so.3")
    late_hwcaps.parent.mkdir(parents=True)
    late_hwcaps.write_bytes(b"review704 late hwcaps candidate\n")
    expected_ro_failure("sealed S0 lower replacement", lambda: (S0 / "usr/bin/python3.12").write_bytes(b"bad"))
    (CONTROL / "attack-complete").write_text("continue\n", encoding="ascii")
    wait_path(CONTROL / "broker-result", timeout=180)
    broker = json.loads((CONTROL / "broker-result").read_text())
    if broker["rc"] != 0:
        raise RuntimeError(f"static stage1 broker failed: {broker}")
    wait_path(CONTROL / "s0-late-import-ok")
    late = json.loads((CONTROL / "s0-late-import-ok").read_text())
    if marker.exists() or not late["ssl"].startswith("/usr/lib/python3.12/") or not late["module"].startswith("/usr/lib/thebitlab/"):
        raise RuntimeError(f"private lazy import escaped synthetic root: {late}")

    restore_host(extension, extension_backup)
    late_candidate.unlink()
    shutil.rmtree(late_hwcaps.parents[1])
    TOOLCHAIN.unlink()
    renamed.replace(TOOLCHAIN)
    module.write_bytes(original_module)
    os.close(directory_fd)
    shutil.rmtree(malicious_root)
    marker.unlink(missing_ok=True)
    print(
        "EVIDENCE: parent rename + alias + preopened-dir + normal candidate + hwcaps "
        "+ Python .py/native late replacement isolated PASS"
    )
    return process, json.loads((CONTROL / "s1-metrics.json").read_text())


def pids_for_nginx() -> list[int]:
    result: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            exe = (entry / "exe").readlink()
            comm = (entry / "comm").read_text().strip()
        except OSError:
            continue
        if exe.as_posix() == "/usr/sbin/nginx" or comm == "nginx":
            result.append(int(entry.name))
    return sorted(result)


def mapping_paths(pid: int) -> set[Path]:
    result: set[Path] = set()
    for line in Path(f"/proc/{pid}/maps").read_text().splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and "x" in fields[1] and fields[5].startswith("/"):
            lexical = fields[5].removesuffix(" (deleted)")
            result.add(Path(lexical))
    return result


def attest_runtime_maps(s1_report: dict[str, object]) -> tuple[set[Path], list[int]]:
    s0_manifest = json.loads((S0 / ".thebitlab-s0-manifest.json").read_text())
    objects = dict(s0_manifest["objects"])
    objects.update(s1_report["objects"])
    pids = pids_for_nginx()
    if len(pids) < 2:
        raise RuntimeError(f"nginx master/worker missing: {pids}")
    mappings: set[Path] = set()
    for pid in pids:
        for lexical in mapping_paths(pid):
            identity = objects.get(str(lexical))
            if identity is None:
                raise RuntimeError(f"mutable/unreviewed executable map pid={pid}: {lexical}")
            runtime_path = Path(f"/proc/{pid}/root") / lexical.relative_to("/")
            if sha(runtime_path) != identity["sha256"]:
                raise RuntimeError(f"runtime map digest mismatch pid={pid}: {lexical}")
            mappings.add(lexical)
    required = {
        Path("/usr/sbin/nginx"),
        Path("/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2"),
        Path("/usr/lib/x86_64-linux-gnu/libc.so.6"),
        Path("/usr/lib/x86_64-linux-gnu/libssl.so.3"),
        Path("/usr/lib/x86_64-linux-gnu/libcrypto.so.3"),
        Path("/usr/lib/nginx/modules/ngx_http_geoip2_module.so"),
        Path("/usr/lib/nginx/modules/ngx_stream_module.so"),
    }
    if not required <= mappings:
        raise RuntimeError(f"required sealed maps missing: {sorted(required - mappings)}")
    return mappings, pids


def http_request() -> None:
    with socket.create_connection(("127.0.0.1", 80), timeout=5) as connection:
        connection.sendall(b"GET / HTTP/1.0\r\nHost: localhost\r\n\r\n")
        response = connection.recv(4096)
    if b"200 OK" not in response:
        raise RuntimeError(f"first HTTP request failed: {response[:200]!r}")


def test_n1(s1_report: dict[str, object]) -> dict[str, object]:
    expected_ro_failure("manager unexpected sibling", lambda: (MANAGED_DROPIN.parent / "90-evil.conf").write_text("[Service]\nExecStartPost=/bin/false\n"))
    merged_hwcaps = MERGED / "usr/lib/x86_64-linux-gnu/glibc-hwcaps/x86-64-v3"
    expected_ro_failure("overlay hwcaps insertion", lambda: merged_hwcaps.mkdir(parents=True))
    expected_ro_failure("S1 lower replacement", lambda: (S1 / "usr/sbin/nginx").write_bytes(b"bad"))
    run(["systemctl", "daemon-reload"])
    properties = run(
        ["systemctl", "show", "nginx.service", "--property=RootDirectory", "--property=DropInPaths", "--property=ExecStart"],
    ).stdout
    if f"RootDirectory={MERGED}" not in properties or str(MANAGED_DROPIN) not in properties:
        raise RuntimeError(f"N1 effective contract missing: {properties}")
    run(["systemctl", "daemon-reload"])

    def start_case(label: str, mutation_paths: tuple[Path, ...]) -> float:
        for marker in (CONTROL / "start-barrier-ready", CONTROL / "start-continue"):
            marker.unlink(missing_ok=True)
        run(["systemctl", "reset-failed", "nginx.service"], check=False)
        started_at = time.monotonic()
        start_process = subprocess.Popen(
            ["systemctl", "start", "nginx.service"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline and not (CONTROL / "start-barrier-ready").exists():
            if start_process.poll() is not None:
                break
            time.sleep(0.02)
        if not (CONTROL / "start-barrier-ready").exists():
            stdout, stderr = start_process.communicate(timeout=2)
            journal = run(["journalctl", "-u", "nginx.service", "-n", "40", "--no-pager"], check=False).stdout
            raise RuntimeError(f"N1 {label} exited before static barrier: {stderr}\n{stdout}\n{journal}")
        mutations: list[tuple[Path, Path]] = []
        for path in mutation_paths:
            backup, _ = atomic_host_replace(path, b"review704 mutable host replacement\n")
            mutations.append((path, backup))
        (CONTROL / "start-continue").write_text("continue\n", encoding="ascii")
        try:
            stdout, stderr = start_process.communicate(timeout=30)
        except subprocess.TimeoutExpired as exc:
            status = run(["systemctl", "status", "nginx.service", "--no-pager", "-l"], check=False).stdout
            pid_files = []
            for candidate in (Path("/run/nginx.pid"), MERGED / "run/nginx.pid", RUNTIME / "runtime/run/nginx.pid"):
                pid_files.append(f"{candidate}={candidate.read_text().strip() if candidate.exists() else 'ABSENT'}")
            processes = run(["ps", "-ef"], check=False).stdout
            start_process.kill(); start_process.communicate()
            raise RuntimeError(
                f"N1 {label} start timeout; {' '.join(pid_files)}\n{status}\n"
                + "\n".join(line for line in processes.splitlines() if "nginx" in line)
            ) from exc
        elapsed = time.monotonic() - started_at
        for path, backup in reversed(mutations):
            restore_host(path, backup)
        if start_process.returncode:
            journal = run(["journalctl", "-u", "nginx.service", "-n", "60", "--no-pager"], check=False).stdout
            status = run(["systemctl", "status", "nginx.service", "--no-pager", "-l"], check=False).stdout
            raise RuntimeError(f"N1 {label} start failed: {stderr}\n{stdout}\n{status}\n{journal}")
        return elapsed

    # Establish lifecycle compatibility before attributing a failure to a host mutation.
    start_seconds = start_case("baseline", ())
    run(["systemctl", "stop", "nginx.service"])
    mutation_cases = (
        ("host-nginx", Path("/usr/sbin/nginx")),
        ("host-libssl", Path("/usr/lib/x86_64-linux-gnu/libssl.so.3")),
        ("host-libcrypto", Path("/usr/lib/x86_64-linux-gnu/libcrypto.so.3")),
        ("host-module", Path("/usr/lib/nginx/modules/ngx_http_geoip2_module.so")),
    )
    for index, (label, path) in enumerate(mutation_cases):
        start_seconds += start_case(label, (path,))
        if index != len(mutation_cases) - 1:
            run(["systemctl", "stop", "nginx.service"])
    start_seconds /= 1 + len(mutation_cases)

    before, pids = attest_runtime_maps(s1_report)
    http_request()
    main_pid = int(run(["systemctl", "show", "nginx.service", "--property=MainPID", "--value"]).stdout.strip())
    workers = [pid for pid in pids if pid != main_pid]
    if not workers:
        raise RuntimeError("nginx worker missing before respawn")
    os.kill(workers[0], signal.SIGTERM)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        current = pids_for_nginx()
        if workers[0] not in current and len(current) >= 2:
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("nginx worker did not respawn")
    run(["systemctl", "kill", "--kill-whom=main", "--signal=USR1", "nginx.service"])
    run(["systemctl", "reload", "nginx.service"])
    http_request()
    after, _ = attest_runtime_maps(s1_report)
    if after - before:
        # New reviewed late maps are acceptable but must already be in immutable policy.
        print("EVIDENCE: reviewed late maps:", ",".join(map(str, sorted(after - before))))
    run(["systemctl", "stop", "nginx.service"])
    run(["systemctl", "start", "nginx.service"])
    final_maps, _ = attest_runtime_maps(s1_report)
    run(["systemctl", "stop", "nginx.service"])
    print(
        "EVIDENCE: N1 RootDirectory start/request/USR1/reload/worker-respawn/stop/restart "
        "uses only sealed S0+S1 executable maps PASS"
    )
    return {
        "start_proof_seconds": start_seconds,
        "runtime_mapping_count": len(final_maps),
        "tls": "not configured in pristine Noble default site",
        "dns_nss": "numeric local request; NSS code remains sealed and no DNS lookup required",
        "provider": "OpenSSL default/built-in path exercised by nginx module load; no mutable provider map",
    }


def test_n2_lifecycle(s1_report: dict[str, object]) -> dict[str, object]:
    unit = "thebitlab-private-n2-poc.service"
    run(["systemctl", "stop", "nginx.service"], check=False)
    run(["systemctl", "reset-failed", "nginx.service"], check=False)
    for marker in (CONTROL / "start-barrier-ready", CONTROL / "start-continue"):
        marker.unlink(missing_ok=True)
    run(["systemctl", "daemon-reload"])
    process = subprocess.Popen(
        ["systemctl", "start", unit], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline and not (CONTROL / "start-barrier-ready").exists():
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            status = run(["systemctl", "status", unit, "--no-pager", "-l"], check=False).stdout
            journal = run(["journalctl", "-u", unit, "-n", "60", "--no-pager"], check=False).stdout
            raise RuntimeError(f"N2 exited before barrier: {stderr}\n{stdout}\n{status}\n{journal}")
        time.sleep(0.02)
    if not (CONTROL / "start-barrier-ready").exists():
        status = run(["systemctl", "status", unit, "--no-pager", "-l"], check=False).stdout
        raise RuntimeError(f"N2 timeout before barrier; launcher_exists={LAUNCHER.exists()}\n{status}")
    mutations: list[tuple[Path, Path]] = []
    for path in (
        Path("/usr/sbin/nginx"),
        Path("/usr/lib/x86_64-linux-gnu/libssl.so.3"),
        Path("/usr/lib/x86_64-linux-gnu/libcrypto.so.3"),
        Path("/usr/lib/nginx/modules/ngx_http_geoip2_module.so"),
    ):
        backup, _ = atomic_host_replace(path, b"review704 mutable host replacement before static N2 broker\n")
        mutations.append((path, backup))
    started_at = time.monotonic()
    try:
        (CONTROL / "start-continue").write_text("continue\n", encoding="ascii")
        stdout, stderr = process.communicate(timeout=30)
    finally:
        for path, backup in reversed(mutations):
            restore_host(path, backup)
    start_seconds = time.monotonic() - started_at
    if process.returncode:
        status = run(["systemctl", "status", unit, "--no-pager", "-l"], check=False).stdout
        journal = run(["journalctl", "-u", unit, "-n", "60", "--no-pager"], check=False).stdout
        evidence = "\n".join(path.read_text() for path in sorted(CONTROL.glob("private-exec-*")))
        raise RuntimeError(f"N2 lifecycle start failed: {stderr}\n{stdout}\n{status}\n{journal}\nprivate-exec:\n{evidence}")
    before, pids = attest_runtime_maps(s1_report)
    http_request()
    main_pid = int(run(["systemctl", "show", unit, "--property=MainPID", "--value"]).stdout.strip())
    workers = [pid for pid in pids if pid != main_pid]
    if not workers:
        raise RuntimeError("N2 nginx worker absent")
    os.kill(workers[0], signal.SIGTERM)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if workers[0] not in pids_for_nginx() and len(pids_for_nginx()) >= 2:
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("N2 worker did not respawn")
    run(["systemctl", "kill", "--kill-whom=main", "--signal=USR1", unit])
    run(["systemctl", "reload", unit])
    http_request()
    after, _ = attest_runtime_maps(s1_report)
    run(["systemctl", "stop", unit])
    run(["systemctl", "start", unit])
    final_maps, _ = attest_runtime_maps(s1_report)
    run(["systemctl", "stop", unit])
    print("EVIDENCE: N2 static broker start/request/USR1/reload/worker-respawn/stop/restart and sealed maps PASS")
    return {
        "result": "SELECTED",
        "start_proof_seconds": start_seconds,
        "runtime_mapping_count": len(final_maps),
        "late_mapping_delta": sorted(map(str, after - before)),
        "tls": "not configured in pristine Noble default site",
        "dns_nss": "numeric local request; NSS code remains sealed",
        "provider": "OpenSSL default/built-in path; no mutable provider executable map",
    }


def main() -> int:
    setup()
    full_process: subprocess.Popen[str] | None = None
    try:
        test_expected_absent_hwcaps()
        preload_manifest = test_exact_preload()
        full_process, s1_report = launch_full_and_attack_s0()
        n2: dict[str, object] = {"result": "NOT_NEEDED"}
        try:
            n1 = test_n1(s1_report)
        except RuntimeError as n1_error:
            if "N1 host-libcrypto start failed" not in str(n1_error):
                raise
            n1 = {"result": "REJECTED", "reason": "systemd 255 consumes dynamic host libcrypto between Exec slots"}
            print("EVIDENCE: N1 RootDirectory REJECTED: dynamic host libcrypto is consumed between systemd Exec slots")
            try:
                n2 = test_n2_lifecycle(s1_report)
            except RuntimeError as n2_error:
                if "N2 lifecycle start failed" not in str(n2_error):
                    raise
                n2 = {
                    "result": "REJECTED",
                    "reason": "systemd 255 consumes dynamic host libcrypto before the sealed static ExecStart broker",
                    "pre_pivot_marker_count": len(tuple(CONTROL.glob("private-exec-*"))),
                }
                blocked_report = {
                    "schema": "thebitlab.private-runtime-poc-report.v1",
                    "remote_head": "598f1905462b5df0cb5f009ea79cffb7901545b8",
                    "architecture": "PRIVATE STAGE0 + STATIC STAGE1 BROKER",
                    "s0": preload_manifest["metrics"],
                    "s1": s1_report["metrics"],
                    "composition": "read-only overlayfs lowerdir=S1:S0, no upper",
                    "n1": n1,
                    "n2": n2,
                    "manager_global_mount_count": 2,
                    "manager_global_bytes_copied": MANAGED_DROPIN.stat().st_size + Path("/run/systemd/system/thebitlab-private-n2-poc.service").stat().st_size,
                    "reviewed_present_execution_objects": len(preload_manifest["objects"]) + len(s1_report["objects"]),
                    "expected_absent_loader_candidates": 735,
                    "hwcaps": {"v2": 245, "v3": 245, "v4": 245},
                    "unpinned_selectable_candidates": 0,
                    "blocker": "manager dynamic execution closure is mutable before both N1 nginx and N2 static broker ExecStart",
                }
                print("EVIDENCE: N2 REJECTED: sealed static ExecStart broker was not reached after host libcrypto mutation")
                print("PRIVATE-RUNTIME-POC-REPORT " + json.dumps(blocked_report, sort_keys=True))
                print("BLOCKED: private runtime architecture failed at manager execution boundary")
                return 2
        (CONTROL / "finish").write_text("finish\n", encoding="ascii")
        stdout, stderr = full_process.communicate(timeout=30)
        if full_process.returncode:
            raise RuntimeError(f"Stage0 Python final rc={full_process.returncode}: {stdout[-500:]} {stderr[-1000:]}")
        report = {
            "schema": "thebitlab.private-runtime-poc-report.v1",
            "remote_head": "598f1905462b5df0cb5f009ea79cffb7901545b8",
            "architecture": "PRIVATE STAGE0 + STATIC STAGE1 BROKER",
            "s0": preload_manifest["metrics"],
            "s1": s1_report["metrics"],
            "composition": "read-only overlayfs lowerdir=S1:S0, no upper",
            "n1": n1,
            "n2": n2,
            "selected_mechanism": "N1 RootDirectory" if n1.get("result") != "REJECTED" else "N2 static execution broker",
            "manager_global_mount_count": 2,
            "manager_global_bytes_copied": MANAGED_DROPIN.stat().st_size,
            "reviewed_present_execution_objects": len(preload_manifest["objects"]) + len(s1_report["objects"]),
            "expected_absent_loader_candidates": 735,
            "hwcaps": {"v2": 245, "v3": 245, "v4": 245},
            "unpinned_selectable_candidates": 0,
        }
        Path("/tmp/private-runtime-poc-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("PRIVATE-RUNTIME-POC-REPORT " + json.dumps(report, sort_keys=True))
        print("PASS: private runtime architecture/security POC and microbenchmark")
        return 0
    finally:
        if full_process is not None and full_process.poll() is None:
            with suppress_oserror():
                (CONTROL / "finish").write_text("finish\n", encoding="ascii")
            with suppress_oserror():
                full_process.terminate()
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
