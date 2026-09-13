"""Linux container smoke: real micro PTY, save/reopen, then compile C.

Run in a disposable workspace with --write, then in a new container without it.
"""

from pathlib import Path
import fcntl
import os
import pty
import select
import struct
import subprocess
import sys
import termios
import time


SOURCE = '#include <stdio.h>\nint main(void){puts("MICRO_GATE_OK");return 0;}\n'
PATH = Path("micro-gate.c")


def acquire_terminal() -> None:
    os.setsid()
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)


def main() -> None:
    write = sys.argv[1:] == ["--write"]
    assert os.getuid() == 1000
    assert os.environ["EDITOR"] == os.environ["VISUAL"] == "micro"
    if write:
        assert not PATH.exists(), "Use a fresh, disposable workspace"
    else:
        assert PATH.read_text() == SOURCE
    subprocess.run(["micro", "--version"], check=True)
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 100, 0, 0))
    process = subprocess.Popen(
        ["micro", str(PATH)], stdin=slave, stdout=slave, stderr=slave,
        env={**os.environ, "TERM": "xterm-256color"}, preexec_fn=acquire_terminal,
    )
    os.close(slave)
    screen = bytearray()

    def wait_until(predicate, description: str) -> None:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if predicate():
                return
            if process.poll() is not None:
                break
            if select.select([master], [], [], 0.1)[0]:
                try:
                    screen.extend(os.read(master, 65536))
                except OSError:
                    process.wait(timeout=5)
                    break
        if predicate():
            return
        raise AssertionError(f"micro did not {description}: {screen[-2000:]!r}")

    try:
        wait_until(lambda: b"micro-gate.c" in screen, "open the file")
        if write:
            # Bracketed paste preserves C indentation/newlines regardless of defaults.
            os.write(master, b"\x1b[200~" + SOURCE.encode() + b"\x1b[201~")
            os.write(master, b"\x13")  # Ctrl+S
            wait_until(
                lambda: PATH.exists() and PATH.read_text() == SOURCE, "save the source"
            )
        else:
            wait_until(lambda: b"MICRO_GATE_OK" in screen, "display the saved source")
        os.write(master, b"\x11")  # Ctrl+Q
        wait_until(lambda: process.poll() is not None, "exit")
        assert process.wait(timeout=5) == 0
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        os.close(master)
    assert PATH.read_text() == SOURCE
    subprocess.run(
        ["gcc", "-Wall", "-Wextra", "-Werror", str(PATH), "-o", "micro-gate"], check=True
    )
    output = subprocess.check_output(["./micro-gate"], text=True).strip()
    assert output == "MICRO_GATE_OK", output
    print(f"PASS micro {'save' if write else 'reopen'} and C execution")


if __name__ == "__main__":
    main()
