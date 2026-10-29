"""Generate the OpenWrt ``.config`` for the selected ZeroWrt device.

The device profile is supplied by the workflow (``--device``) and looked up in
the LEDE tree. Package selections live here, in one place, instead of a
separate config file.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from . import util

# Packages added to the image. Dependencies (luci-compat, lyaml, ...) are
# resolved by OpenWrt itself and must not be listed here.
PACKAGES = [
    "CONFIG_PACKAGE_luci-theme-argon",
    "CONFIG_PACKAGE_luci-app-argon-config",
    "CONFIG_PACKAGE_luci-app-passwall",
    "CONFIG_PACKAGE_luci-app-openclash",
    "CONFIG_PACKAGE_luci-app-ota",
    "CONFIG_PACKAGE_luci-i18n-ota-zh-cn",
    "CONFIG_PACKAGE_luci-app-ttyd",
    "CONFIG_PACKAGE_luci-i18n-ttyd-zh-cn",
    "CONFIG_PACKAGE_luci-app-ramfree",
]

# Selected only for the devices listed here. Dependencies (mosdns itself,
# uclient-fetch, geo2txt, ...) are resolved by OpenWrt.
DEVICE_PACKAGES = {
    "x86_64": [
        "CONFIG_PACKAGE_luci-app-mosdns",
    ],
}

# Workflow device names that do not match a Device/ definition one to one:
# x86 has no per-board profile, so both points at "Device/generic" inside a
# different subtarget. The Device name is resolved from the source tree, and
# these entries only pin the board/subtarget it lives in ("generic" exists in
# target/linux/x86/image/{64,generic}.mk alike).
DEVICE_ALIASES = {
    "x86_64": {"board": "x86", "subtarget": "64", "device": "generic"},
    "x86_generic": {"board": "x86", "subtarget": "generic", "device": "generic"},
}


def profile_symbol(target: dict) -> str:
    """Kconfig symbol that selects this target's device or profile."""
    if target.get("kind") == "profile":
        return f"CONFIG_TARGET_{target['board']}_{target['subtarget']}_{target['name']}"
    return f"CONFIG_TARGET_{target['board']}_{target['subtarget']}_DEVICE_{target['name']}"


def build_date() -> str:
    """Firmware version shown on the login page and in image names."""
    return datetime.now().strftime("%Y%m%d")


def resolve_target(tree: Path, name: str) -> dict:
    """Resolve a workflow device selection to target information."""
    alias = DEVICE_ALIASES.get(name)
    if alias is None:
        return find_device(tree, name)

    # Resolve the real Device/ name from the tree: an alias such as "x86_64"
    # cannot be looked up directly, and a name that is guessed instead of
    # read from the tree silently disappears from defconfig when upstream
    # renames the device.
    board_dir = Path(tree) / "target" / "linux" / alias["board"]
    if not board_dir.exists():
        raise util.BuildError(
            f"target {name!r} is built from {board_dir}, which does not exist.\n"
            f"Check that {tree} is the LEDE source tree and that 'source clone' succeeded."
        )
    return find_device(tree, alias["device"], board=alias["board"], subtarget=alias["subtarget"])


def _board_subtargets(board_dir: Path) -> list[str]:
    subtargets: list[str] = []
    makefile = board_dir / "Makefile"
    if makefile.exists():
        match = re.search(r"^SUBTARGETS\s*:?=\s*(.+)$", util.read_text(makefile), re.M)
        if match:
            subtargets = match.group(1).split()
    if not subtargets:
        subtargets = [path.name for path in board_dir.iterdir() if path.is_dir() and (path / "target.mk").exists()]
    return subtargets


def _image_makefiles(board_dir: Path):
    for path in sorted(board_dir.glob("image/*.mk")):
        yield path
    for subtarget_dir in sorted(board_dir.iterdir()):
        if not subtarget_dir.is_dir():
            continue
        for path in sorted(subtarget_dir.glob("image/*.mk")):
            yield path


def _device_blocks(image_mk: Path):
    text = util.read_text(image_mk)
    for match in re.finditer(r"^define\s+Device/(\S+)\s*$", text, re.M):
        end = text.find("\nendef", match.end())
        block = text[match.end() : end if end != -1 else len(text)]
        model = re.search(r"^\s*DEVICE_MODEL\s*:?=\s*(.+?)\s*$", block, re.M)
        dts = re.search(r"^\s*DEVICE_DTS\s*:?=\s*(.+?)\s*$", block, re.M)
        vendor = re.search(r"^\s*DEVICE_VENDOR\s*:?=\s*(.+?)\s*$", block, re.M)
        yield {
            "name": match.group(1).strip(),
            "model": model.group(1).strip() if model else "",
            "dts": dts.group(1).strip() if dts else "",
            "vendor": vendor.group(1).strip() if vendor else "",
        }


def _resolve_subtarget(board_dir: Path, image_mk: Path, subtargets: list[str]) -> str | None:
    if image_mk.parent.name != "image":
        return None
    owner = image_mk.parent.parent
    if owner == board_dir:
        stem = image_mk.stem
        if stem in subtargets:
            return stem
        return subtargets[0] if len(subtargets) == 1 else None
    return owner.name if owner.name in subtargets else None


def _all_devices(tree: Path, board_filter: str | None = None) -> list[str]:
    names: list[str] = []
    linux = Path(tree) / "target" / "linux"
    for board_dir in sorted(path for path in linux.iterdir() if path.is_dir()):
        if board_filter and board_dir.name != board_filter:
            continue
        for image_mk in _image_makefiles(board_dir):
            names.extend(device["name"] for device in _device_blocks(image_mk))
    return sorted(set(names))


def find_device(
    tree: Path,
    name: str,
    *,
    board: str | None = None,
    subtarget: str | None = None,
) -> dict:
    """Return target information for a device profile name.

    Passing *board*/*subtarget* narrows the search, which matters for target
    families where several subtargets declare a device with the same name
    (x86 declares "generic" for both "64" and "generic").
    """
    tree = Path(tree)
    linux = tree / "target" / "linux"
    if not linux.exists():
        raise util.BuildError(f"no target/linux directory in {tree}")

    normalized = name.replace("-", "_").lower()
    for board_dir in sorted(path for path in linux.iterdir() if path.is_dir()):
        if board and board_dir.name != board:
            continue
        subtargets = _board_subtargets(board_dir)
        for image_mk in _image_makefiles(board_dir):
            found_subtarget = _resolve_subtarget(board_dir, image_mk, subtargets)
            if not found_subtarget or (subtarget and found_subtarget != subtarget):
                continue
            for device in _device_blocks(image_mk):
                if device["name"].replace("-", "_").lower() != normalized:
                    continue
                return {
                    "board": board_dir.name,
                    "subtarget": found_subtarget,
                    "name": device["name"],
                    "model": device["model"],
                    "vendor": device["vendor"],
                    "source": str(image_mk.relative_to(tree)),
                }

    candidates = [item for item in _all_devices(tree, board) if "rg-x60" in item.lower()]
    if not candidates:
        candidates = _all_devices(tree, board)[:40]
    scope = f" ({board}/{subtarget})" if board else ""
    raise util.BuildError(
        f"device profile {name!r} was not found in {tree}/target/linux{scope}.\nAvailable devices: "
        + ", ".join(candidates)
    )


def _packages(tree: Path, device: str | None = None) -> list[str]:
    """Return the package list for this checkout and device.

    Argon master integrates the config app into the theme package, so the
    standalone luci-app-argon-config is only selected when it was cloned
    (non-integrated theme, e.g. v2.4.8).
    """
    packages = list(PACKAGES)
    if not (Path(tree) / "package" / "new" / "luci-app-argon-config").exists():
        packages.remove("CONFIG_PACKAGE_luci-app-argon-config")
    packages.extend(DEVICE_PACKAGES.get(device or "", []))
    return sorted(packages)


def _render_config(target: dict, packages: list[str]) -> str:
    lines = ["# Generated by ZeroWrt - do not edit"]
    lines.extend(
        [
            f"CONFIG_TARGET_{target['board']}=y",
            f"CONFIG_TARGET_{target['board']}_{target['subtarget']}=y",
            f"{profile_symbol(target)}=y",
        ]
    )
    lines.extend(f"{package}=y" for package in sorted(packages))
    lines.extend(
        [
            "CONFIG_DEVEL=y",
            # PassWall: use the Xray core, drop the Sing-Box core.
            "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray=y",
            "# CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox is not set",
            # geoip.dat / geosite.dat: Xray's geo-based routing rules need them,
            # and PassWall logs a missing-geodata error for every shunt node
            # without them.
            "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_V2ray_Geodata=y",
            "CONFIG_PACKAGE_xray-core=y",
            "# CONFIG_PACKAGE_sing-box is not set",
        ]
    )
    return "\n".join(lines) + "\n"


def generate(tree: Path, device: str) -> dict:
    tree = Path(tree)
    target = resolve_target(tree, device)
    packages = _packages(tree, device)
    version = build_date()
    util.log(
        f"device {target['name']} ({target['vendor']} {target['model']}) on {target['board']}/{target['subtarget']}"
    )

    config_path = tree / ".config"
    util.write_text(config_path, _render_config(target, packages))
    util.log(f"wrote {config_path}")

    util.header("Resolving configuration (make defconfig)")
    log_path = tree / "defconfig.log"
    util.run(["make", "defconfig"], cwd=tree, log_path=log_path, check=True)

    resolved = util.read_text(config_path)
    required = [
        f"{profile_symbol(target)}=y",
        "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray=y",
        "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_V2ray_Geodata=y",
        "CONFIG_PACKAGE_xray-core=y",
        *[f"{package}=y" for package in packages],
    ]
    missing = [item for item in required if item not in resolved]
    if missing:
        tail = "\n".join(util.read_text(log_path).splitlines()[-40:])
        raise util.BuildError(
            "the following selections were dropped by defconfig (missing dependencies?):\n  - "
            + "\n  - ".join(missing)
            + "\n\nLast defconfig output:\n"
            + tail
        )

    # PassWall must ship exactly one core: a leftover Sing-Box selection would
    # put two large kernels in the image and silently win at runtime.
    stale = [
        item
        for item in (
            "CONFIG_PACKAGE_sing-box=y",
            "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox=y",
        )
        if item in resolved
    ]
    if stale:
        raise util.BuildError(
            "sing-box is still selected; PassWall should use the Xray core:\n  - " + "\n  - ".join(stale)
        )

    info = {
        "board": target["board"],
        "subtarget": target["subtarget"],
        "device": target["name"],
        "device_model": target["model"],
        "device_vendor": target["vendor"],
        "artifact": device,
        "kind": target.get("kind", "device"),
    }
    resolved_version = re.search(r'^CONFIG_VERSION_NUMBER="?([^"\n]+)"?$', resolved, re.M)
    info["version"] = resolved_version.group(1) if resolved_version else version
    util.write_text(tree / ".zerowrt-info.json", json.dumps(info, indent=2) + "\n")
    util.log(
        f"configuration ready: {info['board']}/{info['subtarget']} device={info['device']} version={info['version']}"
    )
    return info
