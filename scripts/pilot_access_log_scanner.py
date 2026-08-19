#!/usr/bin/env python3
"""Scan proxy logs for query targets or authentication material without echoing it."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


MAX_LOG_LINE_BYTES = 256 * 1024
MAX_STORED_FINDINGS = 100
_REQUEST_TARGET = re.compile(rb'"[A-Z]{1,16}\s+([^\s"]+)\s+HTTP/[0-9.]+"', re.IGNORECASE)
_SENSITIVE_ASSIGNMENT = re.compile(
    rb"(?:^|[?&;\s\"'])"
    rb"(?:authorization|cookie|set-cookie|code|state|nonce|access_token|id_token|"
    rb"refresh_token|client_secret|token|proof)\s*[:=]",
    re.IGNORECASE,
)
_BEARER = re.compile(rb"(?:^|\s)bearer\s+[A-Za-z0-9._~+/-]+", re.IGNORECASE)


@dataclass(frozen=True)
class ScanFinding:
    line_number: int
    rule: str


@dataclass(frozen=True)
class ScanResult:
    findings: tuple[ScanFinding, ...]
    total_count: int

    @property
    def omitted_count(self) -> int:
        return self.total_count - len(self.findings)

    def __iter__(self):
        return iter(self.findings)

    def __len__(self) -> int:
        return len(self.findings)


def scan_stream(stream: BinaryIO) -> ScanResult:
    """Scan every record while retaining only a bounded metadata sample."""

    findings: list[ScanFinding] = []
    total_count = 0

    def record(line_number: int, rule: str) -> None:
        nonlocal total_count
        total_count += 1
        if len(findings) < MAX_STORED_FINDINGS:
            findings.append(ScanFinding(line_number, rule))

    line_number = 0
    while True:
        line = stream.readline(MAX_LOG_LINE_BYTES + 1)
        if not line:
            break
        line_number += 1
        if len(line) > MAX_LOG_LINE_BYTES:
            record(line_number, "line_too_long")
            while line and not line.endswith(b"\n"):
                line = stream.readline(MAX_LOG_LINE_BYTES + 1)
            continue
        request = _REQUEST_TARGET.search(line)
        if request is not None and b"?" in request.group(1):
            record(line_number, "query_bearing_request_target")
        if _SENSITIVE_ASSIGNMENT.search(line):
            record(line_number, "sensitive_field")
        if _BEARER.search(line):
            record(line_number, "bearer_credential")
    return ScanResult(tuple(findings), total_count)


def scan_path(path: Path) -> ScanResult:
    with path.open("rb") as stream:
        return scan_stream(stream)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+", type=Path, help="Log locali da analizzare in sola lettura.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    total = 0
    try:
        for path in args.logs:
            findings = scan_path(path)
            total += findings.total_count
            if findings.total_count:
                summary = ", ".join(
                    f"linea {finding.line_number}: {finding.rule}"
                    for finding in findings.findings[:20]
                )
                omitted = findings.total_count - min(20, len(findings.findings))
                if omitted:
                    summary += f", altri {omitted} finding omessi"
                print(f"ERRORE: possibili dati sensibili nel log ({summary})", file=sys.stderr)
    except OSError:
        print("ERRORE: log assente o non leggibile", file=sys.stderr)
        return 2
    if total:
        return 1
    print("PASS: log path-only privo di indicatori di credenziali")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
