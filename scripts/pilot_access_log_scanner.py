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


def scan_stream(stream: BinaryIO) -> tuple[ScanFinding, ...]:
    """Return metadata-only findings while keeping each materialized record bounded."""

    findings: list[ScanFinding] = []
    line_number = 0
    while True:
        line = stream.readline(MAX_LOG_LINE_BYTES + 1)
        if not line:
            break
        line_number += 1
        if len(line) > MAX_LOG_LINE_BYTES:
            findings.append(ScanFinding(line_number, "line_too_long"))
            while line and not line.endswith(b"\n"):
                line = stream.readline(MAX_LOG_LINE_BYTES + 1)
            continue
        request = _REQUEST_TARGET.search(line)
        if request is not None and b"?" in request.group(1):
            findings.append(ScanFinding(line_number, "query_bearing_request_target"))
        if _SENSITIVE_ASSIGNMENT.search(line):
            findings.append(ScanFinding(line_number, "sensitive_field"))
        if _BEARER.search(line):
            findings.append(ScanFinding(line_number, "bearer_credential"))
    return tuple(findings)


def scan_path(path: Path) -> tuple[ScanFinding, ...]:
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
            total += len(findings)
            if findings:
                summary = ", ".join(
                    f"linea {finding.line_number}: {finding.rule}" for finding in findings[:20]
                )
                omitted = len(findings) - 20
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
