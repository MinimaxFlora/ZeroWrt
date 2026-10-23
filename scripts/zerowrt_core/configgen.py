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
    "CONFIG_PACKAGE_luci-app-turboacc",
    "CONFIG_PACKAGE_luci-i18n-turboacc-zh-cn",
]

# Targets that are selected by a regular target profile instead of a device.
PROFILE_TARGETS = {
    "x86_64": {
        "board": "x86",
        "subtarget": "64",
        "name": "Generic",
        "kind": "profile",
        "model": "x86/64",
        "vendor": "Generic",
        "source": "built-in",
    },
}


def build_date() -> str:
    """Firmware version shown on the login page and in image names."""
    return datetime.now().strftime("%Y%m%d")


def resolve_target(tree: Path, name: str) -> dict:
    """Resolve a workflow device selection to target information."""
    built_in = PROFILE_TARGETS.get(name)
    if built_in:
        return dict(built_in)
    return find_device(tree, name)


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


def _all_devices(tree: Path) -> list[str]:
    names: list[str] = []
    linux = Path(tree) / "target" / "linux"
    for board_dir in sorted(path for path in linux.iterdir() if path.is_dir()):
        for image_mk in _image_makefiles(board_dir):
            names.extend(device["name"] for device in _device_blocks(image_mk))
    return sorted(set(names))


def find_device(tree: Path, name: str) -> dict:
    """Return target information for a device profile name."""
    tree = Path(tree)
    linux = tree / "target" / "linux"
    if not linux.exists():
        raise util.BuildError(f"no target/linux directory in {tree}")

    normalized = name.replace("-", "_").lower()
    for board_dir in sorted(path for path in linux.iterdir() if path.is_dir()):
        subtargets = _board_subtargets(board_dir)
        for image_mk in _image_makefiles(board_dir):
            subtarget = _resolve_subtarget(board_dir, image_mk, subtargets)
            if not subtarget:
                continue
            for device in _device_blocks(image_mk):
                if device["name"].replace("-", "_").lower() != normalized:
                    continue
                return {
                    "board": board_dir.name,
                    "subtarget": subtarget,
                    "name": device["name"],
                    "model": device["model"],
                    "vendor": device["vendor"],
                    "source": str(image_mk.relative_to(tree)),
                }

    candidates = [item for item in _all_devices(tree) if "rg-x60" in item.lower()]
    if not candidates:
        candidates = _all_devices(tree)[:40]
    raise util.BuildError(
        f"device profile {name!r} was not found in {tree}/target/linux.\nAvailable devices: " + ", ".join(candidates)
    )


def _packages(tree: Path) -> list[str]:
    """Return the package list for this checkout.

    Argon master integrates the config app into the theme package, so the
    standalone luci-app-argon-config is only selected when it was cloned
    (non-integrated theme, e.g. v2.4.8).
    """
    packages = list(PACKAGES)
    if not (Path(tree) / "package" / "new" / "luci-app-argon-config").exists():
        packages.remove("CONFIG_PACKAGE_luci-app-argon-config")
    return packages


def _render_config(target: dict, packages: list[str]) -> str:
    lines = ["# Generated by ZeroWrt - do not edit"]
    if target.get("kind") == "profile":
        profile = f"CONFIG_TARGET_{target['board']}_{target['subtarget']}_{target['name']}"
    else:
        profile = f"CONFIG_TARGET_{target['board']}_{target['subtarget']}_DEVICE_{target['name']}"
    lines.extend(
        [
            f"CONFIG_TARGET_{target['board']}=y",
            f"CONFIG_TARGET_{target['board']}_{target['subtarget']}=y",
            f"{profile}=y",
        ]
    )
    lines.extend(f"{package}=y" for package in sorted(packages))
    lines.extend(
        [
            "CONFIG_DEVEL=y",
            # PassWall: use the Sing-Box core, drop the large Xray core.
            "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox=y",
            "# CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray is not set",
            "CONFIG_PACKAGE_sing-box=y",
            "# CONFIG_PACKAGE_xray-core is not set",
        ]
    )
    return "\n".join(lines) + "\n"


def generate(tree: Path, device: str) -> dict:
    tree = Path(tree)
    target = resolve_target(tree, device)
    packages = _packages(tree)
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
    if target.get("kind") == "profile":
        profile = f"CONFIG_TARGET_{target['board']}_{target['subtarget']}_{target['name']}=y"
    else:
        profile = f"CONFIG_TARGET_{target['board']}_{target['subtarget']}_DEVICE_{target['name']}=y"
    required = [
        profile,
        "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox=y",
        "CONFIG_PACKAGE_sing-box=y",
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

    if "CONFIG_PACKAGE_xray-core=y" in resolved or "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray=y" in resolved:
        raise util.BuildError("xray-core is still selected; PassWall should use the Sing-Box core")

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
