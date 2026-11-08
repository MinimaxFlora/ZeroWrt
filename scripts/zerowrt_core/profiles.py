"""Supported devices and the upstream source they are built from.

All profiles in this repository come from the same MT798x tree and the same
``mediatek/filogic`` target.  Keeping the device name equal to the upstream
``Device/`` name means a profile can be resolved directly against
``target/linux/mediatek/image/filogic.mk`` instead of maintaining a second,
easily-stale copy of the vendor/model strings.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import util

SOURCE_REPO = "Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly"
# Pinned commit on openwrt-24.10-6.6; use ZEROWRT_SOURCE_REF to advance it.
SOURCE_REF = "6e1f514b99156ca05921defcb0d1f31df3157c4d"
SOURCE_LABEL = "ImmortalWrt MT798x 6.6 (PadavanOnly)"
BOARD = "mediatek"
SUBTARGET = "filogic"
RELEASE_TAG = "mediatek_filogic"

DEFAULT_LAN_IP = "10.0.0.1"


@dataclass(frozen=True)
class Source:
    """The upstream build tree."""

    key: str
    repo: str
    ref: str
    label: str


@dataclass(frozen=True)
class DeviceProfile:
    """A buildable device on ``mediatek/filogic``."""

    name: str
    device: str
    vendor: str
    model: str
    variant: str = ""
    layout: str = "Standard"
    source: str = "immortalwrt-mt798x"

    @property
    def board(self) -> str:
        return BOARD

    @property
    def subtarget(self) -> str:
        return SUBTARGET

    @property
    def target(self) -> str:
        return f"{BOARD}/{SUBTARGET}"

    @property
    def lan_ip(self) -> str:
        """Unified default LAN address for every profile."""
        return DEFAULT_LAN_IP

    @property
    def label(self) -> str:
        text = f"{self.vendor} {self.model}".strip()
        if self.variant:
            text = f"{text} {self.variant}"
        return text


SOURCES: dict[str, Source] = {
    "immortalwrt-mt798x": Source(
        key="immortalwrt-mt798x",
        repo=SOURCE_REPO,
        ref=SOURCE_REF,
        label=SOURCE_LABEL,
    ),
}


def _profile(
    name: str,
    vendor: str,
    model: str,
    *,
    variant: str = "",
    layout: str = "Standard",
) -> DeviceProfile:
    return DeviceProfile(
        name=name,
        device=name,
        vendor=vendor,
        model=model,
        variant=variant,
        layout=layout,
    )


# The order here is the order shown by the workflow choice input.
PROFILES: dict[str, DeviceProfile] = {
    "netcore_n60-pro": _profile("netcore_n60-pro", "Netcore", "N60 Pro"),
    "ruijie_ew-6000gx-pro-expand": _profile(
        "ruijie_ew-6000gx-pro-expand",
        "Ruijie",
        "EW-6000GX Pro",
        variant="(Expand)",
        layout="Expand",
    ),
    "ruijie_ew-6000gx-pro": _profile("ruijie_ew-6000gx-pro", "Ruijie", "EW-6000GX Pro"),
    "ruijie_ew-6000gx-pro-stock": _profile(
        "ruijie_ew-6000gx-pro-stock",
        "Ruijie",
        "EW-6000GX Pro",
        variant="(Stock)",
        layout="Stock",
    ),
    "ruijie_ew-6000gx-pro-ubootmod": _profile(
        "ruijie_ew-6000gx-pro-ubootmod",
        "Ruijie",
        "EW-6000GX Pro",
        variant="(OpenWrt U-Boot layout)",
        layout="U-Boot Mod",
    ),
    "ruijie_rg-x60-new-expand": _profile(
        "ruijie_rg-x60-new-expand",
        "Ruijie",
        "RG-X60 New",
        variant="(Expand)",
        layout="Expand",
    ),
    "ruijie_rg-x60-new": _profile("ruijie_rg-x60-new", "Ruijie", "RG-X60 New"),
    "ruijie_rg-x60-new-stock": _profile(
        "ruijie_rg-x60-new-stock",
        "Ruijie",
        "RG-X60 New",
        variant="(Stock)",
        layout="Stock",
    ),
    "ruijie_rg-x60-new-ubootmod": _profile(
        "ruijie_rg-x60-new-ubootmod",
        "Ruijie",
        "RG-X60 New",
        variant="(OpenWrt U-Boot layout)",
        layout="U-Boot Mod",
    ),
    "supergateway_s20l": _profile("supergateway_s20l", "Super Gateway", "S20L"),
    "supergateway_s20m": _profile("supergateway_s20m", "Super Gateway", "S20M"),
    "supergateway_s20p": _profile("supergateway_s20p", "Super Gateway", "S20P"),
}

DEFAULT_DEVICE = "netcore_n60-pro"


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
