"""Apply the device ``.config`` and verify what defconfig kept.

The package selection lives in ``configs/ruijie-rg-x60-new.config`` exactly as
maintained by the MediaTek builder. This module only adds the few selections
the rewritten pipeline requires (OTA app) and checks that defconfig did not
silently drop the target or the applications the image is supposed to carry.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from . import profiles, state, util

EXTRA_SELECTIONS = {
    "CONFIG_PACKAGE_luci-app-ota": "y",
    "CONFIG_PACKAGE_luci-i18n-ota-zh-cn": "y",
    # openwrt_package's sing-box currently declares an optional libcronet
    # dependency, but no libcronet package exists in the tree. Keep the
    # NaiveProxy outbound off so the image neither warns nor links -lcronet.
    "CONFIG_SING_BOX_BUILD_NAIVE_OUTBOUND": None,
    "CONFIG_SING_BOX_TINY_BUILD_NAIVE_OUTBOUND": None,
}

REQUIRED_SELECTIONS = [
    "CONFIG_GCC_USE_VERSION_16=y",
    "CONFIG_PACKAGE_luci-app-ota=y",
    "CONFIG_PACKAGE_luci-theme-argon=y",
    "CONFIG_PACKAGE_luci-app-passwall=y",
    "CONFIG_PACKAGE_luci-app-openclash=y",
    "CONFIG_PACKAGE_bash=y",
    "CONFIG_PACKAGE_ttyd=y",
]

FORBIDDEN_SELECTIONS = [
    "CONFIG_SING_BOX_BUILD_NAIVE_OUTBOUND=y",
    "CONFIG_SING_BOX_TINY_BUILD_NAIVE_OUTBOUND=y",
]

DEVICE_BLOCK_RE = re.compile(r"^define\s+Device/(?P<name>\S+)\s*$", re.M)


def target_symbol(profile: profiles.DeviceProfile) -> str:
    return f"CONFIG_TARGET_{profile.board}_{profile.subtarget}_DEVICE_{profile.device}"


def set_option(text: str, name: str, value: str | None) -> str:
    """Set a Kconfig symbol, replacing an existing assignment or ``not set``."""
    pattern = re.compile(rf"^(?:# )?{re.escape(name)}(?:=.*| is not set)\s*$", re.M)
    text = pattern.sub("", text)
    text = text.rstrip("\n") + "\n"
    if value is None:
        text += f"# {name} is not set\n"
    else:
        text += f"{name}={value}\n"
    return text


def _read_config(path: Path) -> str:
    if not path.is_file():
        raise util.BuildError(f"device config not found: {path}")
    return util.read_text(path)


def _device_block(text: str, name: str) -> str | None:
    match = DEVICE_BLOCK_RE.search(text)
    while match:
        if match.group("name") == name:
            end = text.find("\nendef", match.end())
            return text[match.end() : end if end != -1 else len(text)]
        match = DEVICE_BLOCK_RE.search(text, match.end())
    return None


def resolve_device(tree: Path, profile: profiles.DeviceProfile) -> dict:
    """Read vendor/model/DTS for the profile from the target image Makefiles."""
    tree = Path(tree)
    board = tree / "target" / "linux" / profile.board
    files = sorted(board.glob("image/*.mk")) + sorted((board / profile.subtarget).glob("image/*.mk"))
    for makefile in files:
        text = util.read_text(makefile)
        block = _device_block(text, profile.device)
        if block is None:
            continue
        values = {}
        for key in ("DEVICE_VENDOR", "DEVICE_MODEL", "DEVICE_VARIANT", "DEVICE_DTS"):
            match = re.search(rf"^\s*{key}\s*:?=\s*(.+?)\s*$", block, re.M)
            if match:
                values[key] = match.group(1).strip()
        return {
            "device_vendor": values.get("DEVICE_VENDOR", profile.vendor),
            "device_model": values.get("DEVICE_MODEL", profile.model),
            "device_variant": values.get("DEVICE_VARIANT", ""),
            "device_dts": values.get("DEVICE_DTS", ""),
            "device_source": str(makefile.relative_to(tree)),
        }
    util.warn(
        f"device {profile.device!r} was not found in {board}; "
        "using the profile vendor/model for the OTA label"
    )
    return {
        "device_vendor": profile.vendor,
        "device_model": profile.model,
        "device_variant": "",
        "device_dts": "",
        "device_source": "",
    }


def render_config(
    text: str,
    profile: profiles.DeviceProfile,
    *,
    extra: dict[str, str | None] | None = None,
) -> str:
    """Return the device config with the pipeline's mandatory selections."""
    target = target_symbol(profile)
    if f"{target}=y" not in text:
        raise util.BuildError(f"device config is missing {target}=y; wrong config for {profile.name}")
    selections = dict(EXTRA_SELECTIONS)
    if extra:
        selections.update(extra)
    for name, value in selections.items():
        text = set_option(text, name, value)
    return text


def apply(
    tree: Path,
    *,
    device: str,
    config_path: Path | None = None,
    extra: dict[str, str | None] | None = None,
    dist_name: str = "ZeroWrt",
) -> dict:
    tree = Path(tree)
    profile = profiles.require(device)
    source = Path(config_path) if config_path else profiles.config_path(profile)
    text = _read_config(source)

    target = target_symbol(profile)
    util.header("Writing .config")
    text = render_config(text, profile, extra=extra)
    util.write_text(tree / ".config", text)
    util.log(f"{source} -> {tree / '.config'} (+{len(EXTRA_SELECTIONS)} pipeline selection(s))")

    util.header("Resolving configuration (make defconfig)")
    log_path = tree / "defconfig.log"
    util.run(["make", "defconfig"], cwd=tree, log_path=log_path, check=True)

    resolved = util.read_text(tree / ".config")
    missing = [item for item in [f"{target}=y", *REQUIRED_SELECTIONS] if item not in resolved]
    if missing:
        tail = "\n".join(util.read_text(log_path).splitlines()[-60:]) if log_path.exists() else ""
        raise util.BuildError(
            "the following selections were dropped by defconfig "
            "(missing dependencies or a package name changed upstream):\n  - "
            + "\n  - ".join(missing)
            + "\n\nLast defconfig output:\n"
            + tail
        )

    stale = [item for item in FORBIDDEN_SELECTIONS if item in resolved]
    if stale:
        raise util.BuildError(
            "the optional sing-box NaiveProxy outbound needs a libcronet package, "
            "which this tree does not provide:\n  - " + "\n  - ".join(stale)
        )

    info = state.read(tree)
    build_date = state.build_date(info) or int(time.time())
    version = info.get("version") or state.version_for(build_date)
    resolved_version = re.search(r'^CONFIG_VERSION_NUMBER="?([^"\n]+)"?$', resolved, re.M)
    if resolved_version and resolved_version.group(1) != version:
        util.warn(
            f"CONFIG_VERSION_NUMBER is {resolved_version.group(1)!r}, "
            f"but include/version.mk is forced to {version!r}; the image name uses {version}"
        )

    device_info = resolve_device(tree, profile)
    info.update(
        {
            "dist": dist_name,
            "profile": profile.name,
            "board": profile.board,
            "subtarget": profile.subtarget,
            "target": f"{profile.board}/{profile.subtarget}",
            "device": profile.device,
            "dt_model": profile.dt_model,
            "device_vendor": device_info["device_vendor"],
            "device_model": device_info["device_model"],
            "device_variant": device_info.get("device_variant", ""),
            "device_dts": device_info.get("device_dts", ""),
            "layout": profile.layout,
            "artifact": profile.name,
            "config": str(source),
            "build_date": build_date,
            "version": version,
        }
    )
    state.write(tree, info)
    util.log(
        f"configuration ready: {profile.board}/{profile.subtarget} "
        f"device={profile.device} version={version}"
    )
    return info
