#!/usr/bin/env python3
"""Reviewed Noble amd64 loader lookup-set policy.

The tree identities are explicit release data from the pinned Ubuntu 24.04 image.
They cover every entry beneath the loader and Python lookup roots, so freezing an
unknown file never promotes it to trust.  The supported glibc 2.39 x86-64 graph
has the portable built-in levels v2/v3/v4; no reviewed hwcaps override exists.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final, NamedTuple


class ReviewedTreeIdentity(NamedTuple):
    sha256: str
    directories: int
    regular_files: int
    symlinks: int


REVIEWED_BOOTSTRAP_LOOKUP_TREES: Final[dict[Path, ReviewedTreeIdentity]] = {
    Path("/usr/lib/x86_64-linux-gnu"): ReviewedTreeIdentity(
        "84e0e21402a88414b237e0e144d6b8901831e4412fe27b04ee468f5d69a7a7df",
        115,
        1033,
        74,
    ),
    Path("/usr/lib/python3.12"): ReviewedTreeIdentity(
        "94cce3010870569d66c0c1b6521761b1f6e73b385beda080b3b5884aaf4f5bec",
        90,
        1193,
        2,
    ),
    Path("/usr/lib/python3/dist-packages"): ReviewedTreeIdentity(
        "414c6baefe31cf63e443acfddd890f690f3b4350d7aca1ceeba27650d1bfff3b",
        19,
        158,
        0,
    ),
    Path("/usr/local/lib"): ReviewedTreeIdentity(
        "d015c7c7f7c12500a9f3d7e1520ec39813e3bf728dd1e971568d5abf51ecde37",
        3,
        0,
        0,
    ),
    Path("/usr/lib64"): ReviewedTreeIdentity(
        "ef218388b1c4e9377d8b38d22e8ea0dc6460826a3f2a6db3409f36f6b42345e0",
        1,
        0,
        1,
    ),
    Path("/etc/ld.so.conf.d"): ReviewedTreeIdentity(
        "a45437fec9ac83840168e8bc2ba519d759b5a75c912a573def950c29db095da3",
        1,
        2,
        0,
    ),
}

BOOTSTRAP_REVIEWED_FILES: Final[dict[Path, str]] = {
    Path("/usr/bin/python3.12"): "1643dacd9feaedc58f3cc581e4d22577dfe25c09b10282936186ccf0f2e61118",
    Path("/etc/ld.so.cache"): "cce0b33c762f0c8de876998628011571c731267320958a596784d53e8d21af1b",
    Path("/etc/ld.so.conf"): "d4b198c463418b493208485def26a6f4c57279467b9dfa491b70433cedb602e8",
    Path("/etc/nsswitch.conf"): "eec30745bade42a3f3f792e4d4192e57d2bcfe8e472433b1de426fe39a39cddb",
    Path("/etc/ssl/openssl.cnf"): "529815b0dd4bd6608bafeeb3d410b0683374e61aef792b3e3f38b3767d26f747",
}

GLIBC_HWCAPS_LEVELS: Final[tuple[str, ...]] = (
    "x86-64-v2",
    "x86-64-v3",
    "x86-64-v4",
)

# Canonical usrmerge spellings for every configured/default search directory.
DEFAULT_LOADER_LOOKUP_DIRECTORIES: Final[tuple[Path, ...]] = (
    Path("/usr/local/lib"),
    Path("/usr/local/lib/x86_64-linux-gnu"),
    Path("/usr/lib/x86_64-linux-gnu"),
    Path("/usr/lib"),
)

# Noble's reviewed cache contains 101 entries and no hwcap-tagged cache entry.
LD_SO_CACHE_REVIEWED_ENTRY_COUNT: Final[int] = 101
LD_SO_CACHE_REVIEWED_HWCAP_ENTRIES: Final[tuple[tuple[str, str, int], ...]] = ()

# glibc 2.39 x86-64 reports only the glibc-hwcaps subdirectory mechanism for
# this platform. dl_platform="haswell" can affect an explicit $PLATFORM token,
# but no reviewed RPATH/RUNPATH contains that token. $ORIGIN is expanded and
# modeled by the native closure.
GLIBC_LEGACY_HWCAPS_APPLICABLE: Final[bool] = False
SUPPORTED_LOADER_PLATFORM: Final[str] = "x86_64"
