"""Build metadata shared by the workflow steps.

``.zerowrt-info.json`` lives at the root of the source tree.  It is written
after the clone and completed after ``config apply``; the OTA embed, artifact
collection and release/OTA steps all read the same record.  One file means the
image, the release and the update index cannot disagree about the device,
version or build date.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from . import util

INFO_FILE = ".zerowrt-info.json"

BUILD_ZONE: ZoneInfo | None
try:  # Python 3.9+; ZoneInfo may still fail when tzdata is missing.
    BUILD_ZONE = ZoneInfo("Asia/Shanghai")
except Exception:  # pragma: no cover - Windows without tzdata
    BUILD_ZONE = None


def path(tree: Path) -> Path:
    return Path(tree) / INFO_FILE


def read(tree: Path) -> dict:
    data = util.read_json(path(tree), default={})
    if not isinstance(data, dict):
        raise util.BuildError(f"{path(tree)} does not contain a JSON object")
    return data


def write(tree: Path, data: dict) -> dict:
    util.write_json(path(tree), data)
    return data


def update(tree: Path, **values) -> dict:
    data = read(tree)
    data.update({key: value for key, value in values.items() if value is not None})
    return write(tree, data)


def build_date(data: dict) -> int:
    try:
        return int(data.get("build_date") or 0)
    except (TypeError, ValueError):
        return 0


def version_for(build_date_value: int) -> str:
    """Build-date version, formatted in the workflow's Asia/Shanghai day."""
    if build_date_value <= 0:
        build_date_value = int(time.time())
    if BUILD_ZONE is not None:
        return datetime.fromtimestamp(build_date_value, BUILD_ZONE).strftime("%Y%m%d")
    return time.strftime("%Y%m%d", time.localtime(build_date_value))


def iso_for(timestamp: int) -> str:
    if BUILD_ZONE is not None:
        return datetime.fromtimestamp(int(timestamp), BUILD_ZONE).strftime("%Y-%m-%d %H:%M:%S %z")
    return datetime.fromtimestamp(int(timestamp), UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def fingerprint(data: dict) -> str:
    """Short, log-safe identity of a build for cache and release notes."""
    parts = [
        str(data.get("profile", "")),
        str(data.get("version", "")),
        str(data.get("source_commit", ""))[:12],
    ]
    return "/".join(part for part in parts if part)
