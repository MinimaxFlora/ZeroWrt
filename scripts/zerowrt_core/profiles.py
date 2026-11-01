"""Device profiles and the upstream tree each one is built from.

ZeroWrt builds two different trees:

* ``ruijie_rg-x60-new`` -- the MT7986 board, built from the ImmortalWrt 24.10
  fork that carries the padavanonly MTK wireless driver.
* ``x86_64`` -- plain x86_64, still built from LEDE.

Both repositories are public, so the workflow needs no source token at all.
A profile name doubles as the release tag and as the ``device`` workflow
input, which is why the name never follows an upstream ``Device/`` rename.
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
    """A buildable device: target, source tree and the packages it adds."""

    name: str
    source: str
    board: str
    subtarget: str
    device: str
    packages: tuple[str, ...] = ()
    layout: str = ""
    has_wifi: bool = True


SOURCES: dict[str, Source] = {
    "immortalwrt": Source(
        key="immortalwrt",
        repo="Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly",
        ref="openwrt-24.10-6.6",
        label="ImmortalWrt 24.10 (MT798x, padavanonly)",
    ),
    "lede": Source(
        key="lede",
        repo="coolsnowwolf/lede",
        ref="master",
        label="LEDE",
    ),
}

PROFILES: dict[str, DeviceProfile] = {
    # The workflow name stays "ruijie_rg-x60-new" so the release tag and the
    # OTA index entry survive the move from LEDE to ImmortalWrt; the firmware
    # itself is the U-Boot layout (ubootmod) build.
    "ruijie_rg-x60-new": DeviceProfile(
        name="ruijie_rg-x60-new",
        source="immortalwrt",
        board="mediatek",
        subtarget="filogic",
        device="ruijie_rg-x60-new-ubootmod",
        layout="OpenWrt U-Boot layout (ubootmod)",
    ),
    "x86_64": DeviceProfile(
        name="x86_64",
        source="lede",
        board="x86",
        subtarget="64",
        device="generic",
        packages=("luci-app-mosdns",),
        layout="EFI and legacy BIOS",
        # No radio on the board: patching the mac80211 defaults is optional.
        has_wifi=False,
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


def base_for(name: str | None) -> str:
    """Upstream family for *name*.

    An unknown name falls back to LEDE, which is what the plain
    ``owner/name`` device lookups used by the tests and by ``find_device``
    assume.
    """
    profile = find(name)
    return profile.source if profile else "lede"
