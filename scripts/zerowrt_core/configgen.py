"""Generate the OpenWrt ``.config`` for the ZeroWrt firmware.

The target is read from ``configs/zerowrt.config``. If no target is pinned
there, it is detected from the LEDE source tree (the private branch already
carries the Ruijie RG-X60 support).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from . import util

DEVICE_PATTERN = re.compile(r"rg[-_]?x60", re.I)

DEFAULT_PACKAGES = [
    "CONFIG_PACKAGE_luci-theme-argon=y",
    "CONFIG_PACKAGE_luci-app-argon-config=y",
    "CONFIG_PACKAGE_luci-app-passwall=y",
    "CONFIG_PACKAGE_luci-app-openclash=y",
    "CONFIG_PACKAGE_luci-app-ssr-plus=y",
]


def _board_subtargets(board_dir: Path) -> list[str]:
    subtargets: list[str] = []
    makefile = board_dir / "Makefile"
    if makefile.exists():
        match = re.search(r"^SUBTARGETS\s*:?=\s*(.+)$", util.read_text(makefile), re.M)
        if match:
            subtargets = match.group(1).split()
    if not subtargets:
        subtargets = [p.name for p in board_dir.iterdir() if p.is_dir() and (p / "target.mk").exists()]
    return subtargets


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
            "model": (model.group(1).strip() if model else ""),
            "dts": (dts.group(1).strip() if dts else ""),
            "vendor": (vendor.group(1).strip() if vendor else ""),
            "block": block,
        }


def _image_makefiles(board_dir: Path):
    for path in sorted(board_dir.glob("image/*.mk")):
        yield path
    for subtarget_dir in sorted(board_dir.iterdir()):
        if not subtarget_dir.is_dir():
            continue
        for path in sorted(subtarget_dir.glob("image/*.mk")):
            yield path


def detect_device(tree: Path, hint: str | None = None) -> dict:
    """Find the RG-X60 device definition in target/linux."""
    tree = Path(tree)
    linux = tree / "target" / "linux"
    if not linux.exists():
        raise util.BuildError(f"no target/linux directory in {tree}")

    candidates: list[dict] = []
    for board_dir in sorted(p for p in linux.iterdir() if p.is_dir()):
        subtargets = _board_subtargets(board_dir)
        for image_mk in _image_makefiles(board_dir):
            parent = image_mk.parent
            if parent.name != "image":
                continue
            owner = parent.parent
            if owner == board_dir:
                stem = image_mk.stem
                subtarget = stem if stem in subtargets else (subtargets[0] if len(subtargets) == 1 else None)
            else:
                subtarget = owner.name
            if not subtarget or subtarget not in subtargets:
                continue
            for device in _device_blocks(image_mk):
                haystack = f"{device['name']} {device['model']} {device['dts']} {device['vendor']}"
                if not DEVICE_PATTERN.search(haystack):
                    continue
                device.update(
                    board=board_dir.name,
                    subtarget=subtarget,
                    source=str(image_mk.relative_to(tree)),
                )
                candidates.append(device)

    if not candidates:
        available = _ruijie_devices(tree)
        message = (
            "could not find a Ruijie RG-X60 device in the LEDE tree.\n"
            "Pin the target explicitly in configs/zerowrt.config, for example:\n"
            "  CONFIG_TARGET_mediatek=y\n"
            "  CONFIG_TARGET_mediatek_filogic=y\n"
            "  CONFIG_TARGET_mediatek_filogic_DEVICE_ruijie_rg-x60-pro=y"
        )
        if available:
            message += "\nDevices mentioning 'ruijie': " + ", ".join(sorted(available))
        raise util.BuildError(message)

    hint_key = (hint or "").strip().lower()
    hint_norm = re.sub(r"[-_]", "", hint_key)

    def score(device: dict) -> tuple:
        name = device["name"].lower()
        name_norm = re.sub(r"[-_]", "", name)
        value = 0
        if hint_norm:
            if hint_norm == name_norm:
                value += 1000
            elif hint_norm in name_norm:
                value += 100
        if re.search(r"rg[-_]?x60$", name):
            value += 40
        if "pro" not in name:
            value += 20
        if "pro" not in hint_key and "pro" in name:
            value -= 15
        return (value, -len(name))

    candidates.sort(key=score, reverse=True)
    best = candidates[0]
    util.log(
        f"detected device {best['name']} ({best['vendor']} {best['model']}) "
        f"on {best['board']}/{best['subtarget']} via {best['source']}"
    )
    if len(candidates) > 1:
        util.log("other matching devices: " + ", ".join(sorted(c["name"] for c in candidates[1:])))
    return best


def _ruijie_devices(tree: Path) -> list[str]:
    names: list[str] = []
    for image_mk in (Path(tree) / "target" / "linux").glob("**/image/*.mk"):
        for device in _device_blocks(image_mk):
            if "ruijie" in f"{device['name']} {device['vendor']} {device['model']}".lower():
                names.append(device["name"])
    return names


def parse_overrides(path: Path | None) -> dict[str, str]:
    """Read ``KEY=VALUE`` lines from configs/zerowrt.config."""
    values: dict[str, str] = {}
    if not path or not Path(path).exists():
        return values
    for raw in util.read_text(Path(path)).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line or not line.startswith("CONFIG_"):
            util.warn(f"ignoring unsupported config line: {raw}")
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _target_from_overrides(overrides: dict[str, str]) -> dict | None:
    for key in overrides:
        match = re.fullmatch(r"CONFIG_TARGET_([a-zA-Z0-9_]+?)_([a-zA-Z0-9_]+)_DEVICE_(\S+)", key)
        if match and overrides[key] == "y":
            return {
                "board": match.group(1),
                "subtarget": match.group(2),
                "name": match.group(3),
                "model": "",
                "vendor": "",
                "source": "configs/zerowrt.config",
            }
    return None


def _render_config(target: dict, overrides: dict[str, str]) -> str:
    values: dict[str, str] = {}
    values[f"CONFIG_TARGET_{target['board']}"] = "y"
    values[f"CONFIG_TARGET_{target['board']}_{target['subtarget']}"] = "y"
    values[f"CONFIG_TARGET_{target['board']}_{target['subtarget']}_DEVICE_{target['name']}"] = "y"

    if not overrides:
        for line in DEFAULT_PACKAGES:
            key, value = line.split("=", 1)
            values[key] = value

    for key, value in overrides.items():
        if key.startswith("CONFIG_TARGET_"):
            continue
        values[key] = value

    lines = ["# Generated by ZeroWrt - do not edit, use configs/zerowrt.config"]
    target_lines = [key for key in values if key.startswith("CONFIG_TARGET_")]
    other_lines = [key for key in values if not key.startswith("CONFIG_TARGET_")]
    for key in sorted(target_lines):
        lines.append(f"{key}={values[key]}")
    for key in sorted(other_lines):
        lines.append(f"{key}={values[key]}")
    return "\n".join(lines) + "\n"


def generate(tree: Path, config_file: Path | None, *, device: str | None = None) -> dict:
    tree = Path(tree)
    overrides = parse_overrides(config_file)

    target = _target_from_overrides(overrides)
    if target:
        util.log(
            f"using target from {config_file}: "
            f"{target['board']}/{target['subtarget']} device {target['name']}"
        )
    else:
        target = detect_device(tree, hint=device or os.environ.get("DEVICE_PROFILE"))

    config_text = _render_config(target, overrides)
    write_config = tree / ".config"
    util.write_text(write_config, config_text)
    util.log(f"wrote {write_config}")

    util.header("Resolving configuration (make defconfig)")
    log_path = tree / "defconfig.log"
    util.run(["make", "defconfig"], cwd=tree, log_path=log_path, check=True)

    resolved = util.read_text(write_config)
    required = [
        f"CONFIG_TARGET_{target['board']}_{target['subtarget']}_DEVICE_{target['name']}=y",
        "CONFIG_PACKAGE_luci-theme-argon=y",
        "CONFIG_PACKAGE_luci-app-passwall=y",
        "CONFIG_PACKAGE_luci-app-openclash=y",
        "CONFIG_PACKAGE_luci-app-ssr-plus=y",
    ]
    if (tree / "package" / "new" / "luci-app-argon-config").exists():
        required.append("CONFIG_PACKAGE_luci-app-argon-config=y")

    missing = [item for item in required if item not in resolved]
    if missing:
        tail = "\n".join(util.read_text(log_path).splitlines()[-40:])
        raise util.BuildError(
            "the following selections were dropped by defconfig (missing dependencies?):\n  - "
            + "\n  - ".join(missing)
            + "\n\nLast defconfig output:\n"
            + tail
        )

    info = {
        "board": target["board"],
        "subtarget": target["subtarget"],
        "device": target["name"],
        "device_model": target.get("model", ""),
        "device_vendor": target.get("vendor", ""),
    }
    version = re.search(r'^CONFIG_VERSION_NUMBER="?([^"\n]+)"?$', resolved, re.M)
    info["version"] = version.group(1) if version else ""

    info_path = tree / ".zerowrt-info.json"
    util.write_text(info_path, json.dumps(info, indent=2) + "\n")
    util.log(
        f"configuration ready: {info['board']}/{info['subtarget']} "
        f"device={info['device']} version={info['version']}"
    )
    return info


def load_info(tree: Path) -> dict:
    path = Path(tree) / ".zerowrt-info.json"
    if path.exists():
        return json.loads(util.read_text(path))
    return {}
