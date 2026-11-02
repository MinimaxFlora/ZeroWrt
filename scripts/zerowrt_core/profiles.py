"""Device profiles and the upstream tree they are built from.

The firmware is built from a public MT798x tree. One profile is shipped, the
Ruijie RG-X60 New in the MTK U-Boot (mtkuboot) layout; the configuration file
under ``configs/`` is the authoritative package selection.

The profile name doubles as the GitHub release tag and is deliberately kept
independent from the upstream ``Device/`` name: upstream may rename the device
without changing the update-index key our users already have.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import util

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Source:
    """An upstream build tree."""

    key: str
    repo: str
    ref: str
    label: str


@dataclass(frozen=True)
class DeviceProfile:
    """A buildable device: config file, target and the source tree it comes from."""

    name: str
    config: str
    source: str
    board: str
    subtarget: str
    device: str
    dt_model: str
    vendor: str
    model: str
    layout: str = ""

    @property
    def release_tag(self) -> str:
        return self.name


SOURCES: dict[str, Source] = {
    "immortalwrt-mtk": Source(
        key="immortalwrt-mtk",
        repo="chasey-dev/immortalwrt-mt798x-rebase",
        ref="25.12",
        label="ImmortalWrt 25.12 (MT798x rebase, MTK wireless)",
    ),
}

PROFILES: dict[str, DeviceProfile] = {
    "ruijie_rg-x60-new": DeviceProfile(
        name="ruijie_rg-x60-new",
        config="configs/ruijie-rg-x60-new.config",
        source="immortalwrt-mtk",
        board="mediatek",
        subtarget="filogic",
        device="ruijie_rg-x60-new-mtkuboot",
        dt_model="ruijie,rg-x60-new-mtkuboot",
        vendor="Ruijie",
        model="RG-X60 New",
        layout="MTK U-Boot layout (mtkuboot)",
    ),
}

DEFAULT_DEVICE = "ruijie_rg-x60-new"


def names() -> list[str]:
    return list(PROFILES)


def find(name: str | None) -> DeviceProfile | None:
    return PROFILES.get(name or "")


def require(name: str) -> DeviceProfile:
    profile = find(name)
    if profile is None:
        raise util.BuildError(f"unknown device profile {name!r}; expected one of: {', '.join(names())}")
    return profile


def source(profile: DeviceProfile) -> Source:
    return SOURCES[profile.source]


def config_path(profile: DeviceProfile, root: Path | None = None) -> Path:
    base = Path(root) if root is not None else PROJECT_ROOT
    return base / profile.config
