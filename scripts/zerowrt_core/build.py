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


def build_toolchain(tree: Path, jobs: int) -> None:
    """Build the toolchain once so it can be cached between workflow runs."""
    tree = Path(tree)
    util.header(f"Building toolchain (make -j{jobs} toolchain/compile)")
    util.run(
        ["make", f"-j{jobs}", "toolchain/compile"],
        cwd=tree,
        log_path=tree / "toolchain.log",
        check=True,
    )
    util.log("toolchain compiled")


def touch_toolchain(tree: Path) -> None:
    """Refresh timestamps of restored toolchain files so make does not rebuild."""
    tree = Path(tree)
    patterns = (
        "staging_dir/host",
        "staging_dir/toolchain-*",
        "build_dir/host",
        "build_dir/toolchain-*",
    )
    touched = 0
    for pattern in patterns:
        for base in tree.glob(pattern):
            if not base.exists():
                continue
            for root, dirs, files in os.walk(base):
                for name in [*dirs, *files]:
                    try:
                        os.utime(Path(root) / name, None)
                        touched += 1
                    except OSError:
                        continue
    util.log(f"refreshed {touched} toolchain path(s) from cache")


def _sanitize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")


def _artifact_suffix(filename: str, device: str) -> str:
    """Return the part of a build artifact name after the device name."""
    device_pattern = re.compile(rf"-{re.escape(device).replace('_', '[-_]')}[-.]", re.I)
    match = device_pattern.search(filename)
    if match:
        return filename[match.end() :]
    return filename


def _version_from_tree(tree: Path, info: dict) -> str:
    version = info.get("version") or ""
    if version:
        return version
    version_mk = Path(tree) / "include" / "version.mk"
    if version_mk.exists():
        match = re.search(
            r"VERSION_NUMBER:=\$\(if \$\(VERSION_NUMBER\),\$\(VERSION_NUMBER\),([^)\s]+)\)",
            util.read_text(version_mk),
        )
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
    artifact = info.get("artifact") or device
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
        has_device = bool(device) and re.search(rf"-{re.escape(device).replace('_', '[-_]')}[-.]", path.name, re.I)
        if path.suffix in {".bin", ".itb", ".gz", ".iso", ".efi", ".vmdk", ".vhdx", ".qcow2", ".tar"} and has_device:
            suffix = _artifact_suffix(path.name, device)
            stem = _sanitize(f"ZeroWrt-{version}-{artifact}-{suffix}")
            new_name = stem
        else:
            new_name = path.name
        destination = out_dir / new_name
        if destination.exists():
            destination.unlink()
        shutil.copy2(path, destination)
        collected.append(destination)
        util.log(f"{path.name} -> {destination.name}")

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
