"""Device profile and the upstream tree it is built from.

ZeroWrt builds one device: the Ruijie RG-X60 New (MT7986), from the ImmortalWrt
24.10 fork that carries the padavanonly MTK wireless driver. The repository is
public, so the workflow needs no source token.

The profile indirection stays so the upstream branch and the ``Device/`` name
are resolved in one place and the profile name (which doubles as the release
tag) never follows an upstream rename.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import util


@dataclass(frozen=True)
class Source:
    """An upstream build tree."""

    key: str
    repo: str
    ref: str
    label: str


@dataclass(frozen=True)
class DeviceProfile:
    """A buildable device: target and the source tree it comes from."""

    name: str
    source: str
    board: str
    subtarget: str
    device: str
    layout: str = ""


SOURCES: dict[str, Source] = {
    "immortalwrt": Source(
        key="immortalwrt",
        repo="Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly",
        ref="openwrt-24.10-6.6",
        label="ImmortalWrt 24.10 (MT798x, padavanonly)",
    ),
}

PROFILES: dict[str, DeviceProfile] = {
    # The profile name stays "ruijie_rg-x60-new" so the release tag and the OTA
    # index entry survive upstream renames; the firmware itself is the U-Boot
    # layout (ubootmod) build.
    "ruijie_rg-x60-new": DeviceProfile(
        name="ruijie_rg-x60-new",
        source="immortalwrt",
        board="mediatek",
        subtarget="filogic",
        device="ruijie_rg-x60-new-ubootmod",
        layout="OpenWrt U-Boot layout (ubootmod)",
    ),
}

DEFAULT_DEVICE = "ruijie_rg-x60-new"


def names() -> list[str]:
    return list(PROFILES)


def find(name: str | None) -> DeviceProfile | None:
    """Return the profile for *name*, or None when it is not a profile."""
    return PROFILES.get(name or "")


def require(name: str) -> DeviceProfile:
    profile = find(name)
    if profile is None:
        raise util.BuildError(f"unknown device profile {name!r}; expected one of: {', '.join(names())}")
    return profile


def source(profile: DeviceProfile) -> Source:
    """Upstream tree for *profile*."""
    return SOURCES[profile.source]
