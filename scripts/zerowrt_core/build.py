"""Downloading, compiling and collecting the firmware.

Only firmware images are collected.  The release must not receive
``config.buildinfo``, ``feeds.buildinfo``, ``profiles.json``, manifests,
``SHA256SUMS`` or the DDR bl2 blobs.
"""

from __future__ import annotations

import fnmatch
import os
import shutil
from pathlib import Path

from . import state, util

GIB = 1024**3

FIRMWARE_PATTERNS = (
    "*-initramfs-kernel.bin",
    "*-squashfs-sysupgrade.bin",
    "*-squashfs-sysupgrade.itb",
    "*-initramfs-recovery.itb",
    "*-bl31-uboot.fip",
    "*-preloader.bin",
)
SYSUPGRADE_PATTERNS = ("*-squashfs-sysupgrade.bin", "*-squashfs-sysupgrade.itb")


def _available_memory_gb() -> float:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return 0.0
    for line in util.read_text(meminfo).splitlines():
        if line.startswith("MemAvailable:"):
            try:
                return int(line.split()[1]) / (1024**2)
            except (IndexError, ValueError):
                return 0.0
    return 0.0


def compile_jobs(requested: int | None = None) -> int:
    """Parallelism for ``make``: ``nproc + 1``, capped at 1.5 GiB per job."""
    base = max(1, int(requested or os.cpu_count() or 2))
    jobs = base + 1
    memory = _available_memory_gb()
    if memory > 0:
        jobs = min(jobs, max(1, int(memory // 1.5)))
    return max(1, jobs)


def download_sources(tree: Path, jobs: int | None = None) -> None:
    tree = Path(tree)
    jobs = max(1, int(jobs or os.cpu_count() or 2))
    util.header("Downloading source archives")
    log = tree / "download.log"
    code, _ = util.run(["make", f"-j{jobs}", "download"], cwd=tree, log_path=log, check=False)
    if code != 0:
        util.warn("parallel download failed; retrying serially")
        util.run(["make", "-j1", "download"], cwd=tree, log_path=log, check=True)


def compile_firmware(tree: Path, jobs: int | None = None) -> None:
    tree = Path(tree)
    cores = compile_jobs(jobs)
    log = tree / "build.log"

    util.header(f'Compiling ZeroWrt (make -j{cores} IGNORE_ERRORS="n m")')
    code, _ = util.run(
        ["make", f"-j{cores}", "IGNORE_ERRORS=n m"],
        cwd=tree,
        log_path=log,
        check=False,
    )
    if code == 0:
        util.log("firmware compiled")
        return

    # A parallel build only reports "failed to build"; rebuild serially with
    # V=s so the log carries the failing command and its output.
    util.warn(f"make exited with {code}; retrying serially with V=s")
    util.run(
        ["make", "-j1", "IGNORE_ERRORS=n m", "V=s"],
        cwd=tree,
        log_path=log,
        check=True,
    )
    util.log("firmware compiled after the verbose retry")


def _target_dir(tree: Path, info: dict) -> Path:
    targets = tree / "bin" / "targets"
    board = info.get("board", "")
    subtarget = info.get("subtarget", "")
    if board and subtarget and (targets / board / subtarget).is_dir():
        return targets / board / subtarget
    candidates = sorted(path for path in targets.glob("*/*") if path.is_dir())
    if not candidates:
        raise util.BuildError(f"no build output found under {targets}")
    if len(candidates) > 1:
        util.warn(f"several target directories found; using {candidates[0]}")
    return candidates[0]


def is_firmware(name: str) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in FIRMWARE_PATTERNS)


def _collect_files(source_dir: Path, out_dir: Path) -> list[Path]:
    files = [path for path in sorted(source_dir.iterdir()) if path.is_file() and is_firmware(path.name)]
    if not files:
        raise util.BuildError(f"no firmware images matched {FIRMWARE_PATTERNS} under {source_dir}")

    collected: list[Path] = []
    for path in files:
        if not path.name.startswith("zerowrt-"):
            raise util.BuildError(
                f"firmware {path.name!r} does not start with 'zerowrt-'; check VERSION_DIST in include/version.mk"
            )
        destination = out_dir / path.name
        if destination.exists():
            destination.unlink()
        shutil.copy2(path, destination)
        collected.append(destination)
        util.log(f"collected {destination.name} ({destination.stat().st_size // (1024**2)} MiB)")
    return collected


def _has_sysupgrade(files: list[Path]) -> bool:
    return any(any(fnmatch.fnmatch(path.name, pattern) for pattern in SYSUPGRADE_PATTERNS) for path in files)


def collect(tree: Path, out_dir: Path) -> list[Path]:
    tree = Path(tree)
    out_dir = Path(out_dir)
    info = state.read(tree)
    source_dir = _target_dir(tree, info)

    util.header(f"Collecting firmware from {source_dir.relative_to(tree)}")
    out_dir.mkdir(parents=True, exist_ok=True)
    collected = _collect_files(source_dir, out_dir)
    if not _has_sysupgrade(collected):
        raise util.BuildError("no sysupgrade image was produced; refusing to publish only initramfs/loader files")
    util.log(f"collected {len(collected)} firmware file(s) in {out_dir}")
    return collected
