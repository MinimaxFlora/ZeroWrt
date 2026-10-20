"""Building and collecting the firmware."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

from . import util


def download_sources(tree: Path, jobs: int) -> None:
    tree = Path(tree)
    util.header("Downloading source archives")
    log = tree / "download.log"
    code, _ = util.run(["make", f"-j{jobs}", "download"], cwd=tree, log_path=log, check=False)
    if code != 0:
        util.warn("parallel download failed; retrying serially")
        util.run(["make", "-j1", "download"], cwd=tree, log_path=log, check=True)


def compile_firmware(tree: Path, jobs: int) -> None:
    tree = Path(tree)
    util.header(f"Compiling ZeroWrt (make -j{jobs})")
    util.run(["make", f"-j{jobs}", "V=s"], cwd=tree, log_path=tree / "build.log", check=True)
    util.log("firmware compiled")


def _version_from_tree(tree: Path, info: dict) -> str:
    version = info.get("version") or ""
    if version:
        return version
    version_mk = Path(tree) / "include" / "version.mk"
    if version_mk.exists():
        text = util.read_text(version_mk)
        match = re.search(
            r"VERSION_NUMBER:=\$\(if \$\(VERSION_NUMBER\),\$\(VERSION_NUMBER\),([^)\s]+)\)",
            text,
        )
        if match:
            return match.group(1)
        match = re.search(r"^VERSION_NUMBER:=([0-9]{8})\s*$", text, re.M)
        if match:
            return match.group(1)
    return "unknown"


def collect(tree: Path, out_dir: Path) -> list[Path]:
    tree = Path(tree)
    out_dir = Path(out_dir)
    info = {}
    info_path = tree / ".zerowrt-info.json"
    if info_path.exists():
        info = json.loads(util.read_text(info_path))

    board = info.get("board", "")
    subtarget = info.get("subtarget", "")
    device = info.get("device", "")
    version = _version_from_tree(tree, info)

    targets = tree / "bin" / "targets"
    candidates = []
    if board and subtarget:
        candidates.append(targets / board / subtarget)
    candidates.extend(sorted(p for p in targets.glob("*/*") if p.is_dir()))

    source_dir = next((p for p in candidates if p.exists()), None)
    if source_dir is None:
        raise util.BuildError(f"no build output found under {targets}")

    util.header(f"Collecting artifacts from {source_dir.relative_to(tree)}")
    out_dir.mkdir(parents=True, exist_ok=True)
    collected: list[Path] = []

    patterns = [
        "*.bin",
        "*.itb",
        "*.img",
        "*.img.gz",
        "*.iso",
        "*.efi",
        "*.vmdk",
        "*.vhdx",
        "*.qcow2",
        "*.tar",
        "*.manifest",
        "*.buildinfo",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(source_dir.glob(pattern)))
    # Keep only real files (ignore symlinks to nowhere).
    files = [p for p in files if p.is_file()]

    for path in files:
        destination = out_dir / path.name
        if destination.exists():
            destination.unlink()
        shutil.copy2(path, destination)
        collected.append(destination)
        util.log(f"collected {destination.name}")

    checksum_file = out_dir / "SHA256SUMS"
    lines = []
    for path in sorted(collected):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}")
    util.write_text(checksum_file, "\n".join(lines) + "\n")
    collected.append(checksum_file)

    build_info = out_dir / "BUILD_INFO.txt"
    ref = os.environ.get("LEDE_REF", "")
    commit = os.environ.get("LEDE_COMMIT", "")
    lines = [
        "ZeroWrt firmware",
        f"built: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"tree: {board}/{subtarget}",
        f"device: {device} ({info.get('device_vendor', '')} {info.get('device_model', '')})".strip(),
        f"version: {version}",
    ]
    if ref:
        lines.append(f"source ref: {ref}")
    if commit:
        lines.append(f"source commit: {commit}")
    lines.append(f"workflow run: {os.environ.get('GITHUB_RUN_ID', '')}")
    util.write_text(build_info, "\n".join(lines) + "\n")
    collected.append(build_info)

    if not any(p.suffix in {".bin", ".itb", ".tar", ".gz"} for p in collected):
        raise util.BuildError("no firmware image was produced")
    util.log(f"collected {len(collected)} file(s) in {out_dir}")
    return collected
