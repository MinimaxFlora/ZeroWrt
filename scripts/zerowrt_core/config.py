"""Generate and install per-device ``.config`` files.

``config generate`` expands the high-power template for every device, validates
the result, then saves a small ``diffconfig.sh`` fragment under ``configs/``.
``config apply`` copies that fragment to the source tree and runs
``make defconfig`` once at build time.
"""

from __future__ import annotations

import re
import shutil
import time
from pathlib import Path

from . import profiles, state, util

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIGS_DIR = PROJECT_ROOT / "configs"
BASE_CONFIG = Path("defconfig/mt7975-ipailna-high-power.config")
BOARD = profiles.BOARD
SUBTARGET = profiles.SUBTARGET

# Device/target selection lines only.  CONFIG_TARGET_ROOTFS_* and the other
# image options must survive.
TARGET_SELECTION_RE = re.compile(
    r"^(?:# )?CONFIG_TARGET_"
    r"(?:DEVICE[^\s=]*|MULTI_PROFILE[^\s=]*|PER_DEVICE_ROOTFS[^\s=]*|PROFILE[^\s=]*|"
    r"BOARD[^\s=]*|SUBTARGET[^\s=]*|ARCH_PACKAGES[^\s=]*|mediatek[^\s=]*)"
    r"(?:=.*| is not set)\s*$",
    re.M,
)

PACKAGE_SELECTIONS: dict[str, str | None] = {
    "CONFIG_PACKAGE_luci-app-3cat": "y",
    "CONFIG_PACKAGE_luci-app-acme": "y",
    "CONFIG_PACKAGE_luci-theme-argon": "y",
    "CONFIG_PACKAGE_luci-app-arpbind": "y",
    "CONFIG_PACKAGE_luci-app-commands": "y",
    "CONFIG_PACKAGE_luci-app-ddns": "y",
    "CONFIG_PACKAGE_luci-app-openclash": "y",
    "CONFIG_PACKAGE_luci-app-passwall": "y",
    "CONFIG_PACKAGE_luci-app-ramfree": "y",
    "CONFIG_PACKAGE_luci-app-ttyd": "y",
    "CONFIG_PACKAGE_luci-app-upnp": "y",
    "CONFIG_PACKAGE_luci-app-ota": "y",
    "CONFIG_PACKAGE_luci-i18n-ota-zh-cn": "y",
    "CONFIG_PACKAGE_luci-proto-wireguard": "y",
    "CONFIG_PACKAGE_wireguard-tools": "y",
    "CONFIG_PACKAGE_kmod-wireguard": "y",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray": "y",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox": None,
    "CONFIG_PACKAGE_sing-box": None,
    "CONFIG_PACKAGE_ddns-scripts-aliyun": "y",
    "CONFIG_PACKAGE_ddns-scripts-cloudflare": "y",
    "CONFIG_PACKAGE_ddns-scripts-dnspod": "y",
    "CONFIG_PACKAGE_ddns-scripts-freedns": "y",
    "CONFIG_PACKAGE_ddns-scripts-godaddy": "y",
}

REQUIRED_SELECTIONS = [
    "CONFIG_TARGET_mediatek=y",
    "CONFIG_TARGET_mediatek_filogic=y",
    "CONFIG_TARGET_MULTI_PROFILE=y",
    "CONFIG_TARGET_PER_DEVICE_ROOTFS=y",
    "CONFIG_PACKAGE_luci-app-3cat=y",
    "CONFIG_PACKAGE_luci-app-acme=y",
    "CONFIG_PACKAGE_luci-theme-argon=y",
    "CONFIG_PACKAGE_luci-app-arpbind=y",
    "CONFIG_PACKAGE_luci-app-commands=y",
    "CONFIG_PACKAGE_luci-app-ddns=y",
    "CONFIG_PACKAGE_luci-app-openclash=y",
    "CONFIG_PACKAGE_luci-app-passwall=y",
    "CONFIG_PACKAGE_luci-app-ramfree=y",
    "CONFIG_PACKAGE_luci-app-ttyd=y",
    "CONFIG_PACKAGE_luci-app-upnp=y",
    "CONFIG_PACKAGE_luci-app-ota=y",
    "CONFIG_PACKAGE_luci-i18n-ota-zh-cn=y",
    "CONFIG_PACKAGE_luci-proto-wireguard=y",
    "CONFIG_PACKAGE_wireguard-tools=y",
    "CONFIG_PACKAGE_kmod-wireguard=y",
    "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray=y",
    "CONFIG_PACKAGE_ddns-scripts-aliyun=y",
    "CONFIG_PACKAGE_ddns-scripts-cloudflare=y",
    "CONFIG_PACKAGE_ddns-scripts-dnspod=y",
    "CONFIG_PACKAGE_ddns-scripts-freedns=y",
    "CONFIG_PACKAGE_ddns-scripts-godaddy=y",
    # The high-power template must keep the MTK acceleration stack.
    "CONFIG_PACKAGE_kmod-mt_wifi=y",
    "CONFIG_PACKAGE_kmod-mediatek_hnat=y",
    "CONFIG_PACKAGE_luci-app-turboacc-mtk=y",
    "CONFIG_PACKAGE_luci-app-mtwifi-cfg=y",
]

DEVICE_BLOCK_RE = re.compile(r"^define\s+Device/(?P<name>\S+)\s*$", re.M)
DEVICE_KEYS = ("DEVICE_VENDOR", "DEVICE_MODEL", "DEVICE_VARIANT", "DEVICE_DTS")


def target_symbol(device: str) -> str:
    return f"CONFIG_TARGET_DEVICE_{BOARD}_{SUBTARGET}_DEVICE_{device}"


def target_packages_symbol(device: str) -> str:
    return f"CONFIG_TARGET_DEVICE_PACKAGES_{BOARD}_{SUBTARGET}_DEVICE_{device}"


def set_option(text: str, name: str, value: str | None) -> str:
    """Set a Kconfig symbol, replacing an assignment or ``not set`` line."""
    pattern = re.compile(rf"^(?:# )?{re.escape(name)}(?:=.*| is not set)\s*$", re.M)
    text = pattern.sub("", text)
    text = text.rstrip("\n") + "\n"
    if value is None:
        text += f"# {name} is not set\n"
    else:
        text += f"{name}={value}\n"
    return text


def strip_target_selection(text: str) -> str:
    """Remove all target/device choices while preserving image options."""
    return TARGET_SELECTION_RE.sub("", text)


def render_config(text: str, profile: profiles.DeviceProfile) -> str:
    """Return *text* with exactly one selected target device and ZeroWrt apps."""
    text = strip_target_selection(text)
    text = text.rstrip("\n") + "\n\n"
    text += "\n".join(
        [
            "CONFIG_TARGET_mediatek=y",
            "CONFIG_TARGET_mediatek_filogic=y",
            # These two expose the "Target Devices" menu and per-device rootfs;
            # they do not select more than one device by themselves.
            "CONFIG_TARGET_MULTI_PROFILE=y",
            "CONFIG_TARGET_PER_DEVICE_ROOTFS=y",
            f"{target_symbol(profile.device)}=y",
            f'{target_packages_symbol(profile.device)}=""',
        ]
    )
    text += "\n"
    for name, value in PACKAGE_SELECTIONS.items():
        text = set_option(text, name, value)
    return text


def preview(tree: Path, *, device: str) -> str:
    """Return the pre-defconfig ``.config`` for *device* without running make."""
    tree = Path(tree)
    profile = profiles.require(device)
    base = tree / BASE_CONFIG
    if not base.is_file():
        raise util.BuildError(f"high-power config template not found: {base}")
    return render_config(util.read_text(base), profile)


def _device_block(text: str, name: str) -> str | None:
    match = DEVICE_BLOCK_RE.search(text)
    while match:
        if match.group("name") == name:
            end = text.find("\nendef", match.end())
            return text[match.end() : end if end != -1 else len(text)]
        match = DEVICE_BLOCK_RE.search(text, match.end())
    return None


def resolve_device(tree: Path, profile: profiles.DeviceProfile) -> dict:
    """Read vendor/model/DTS from ``target/linux/mediatek/image/*.mk``."""
    tree = Path(tree)
    image_dir = tree / "target" / "linux" / "mediatek" / "image"
    for makefile in sorted(image_dir.glob("*.mk")):
        text = util.read_text(makefile)
        block = _device_block(text, profile.device)
        if block is None:
            continue
        values: dict[str, str] = {}
        for key in DEVICE_KEYS:
            match = re.search(rf"^\s*{key}\s*:?=\s*(.+?)\s*$", block, re.M)
            if match:
                values[key] = match.group(1).strip()
        model = values.get("DEVICE_MODEL", profile.model)
        variant = values.get("DEVICE_VARIANT", profile.variant)
        if variant and variant in model:
            variant = ""
        return {
            "device_vendor": values.get("DEVICE_VENDOR", profile.vendor),
            "device_model": model,
            "device_variant": variant,
            "device_dts": values.get("DEVICE_DTS", ""),
            "device_source": str(makefile.relative_to(tree)),
        }
    util.warn(
        f"device {profile.device!r} was not found in {image_dir}; using the profile vendor/model for the OTA label"
    )
    return {
        "device_vendor": profile.vendor,
        "device_model": profile.model,
        "device_variant": profile.variant,
        "device_dts": "",
        "device_source": "",
    }


def _check_resolved(resolved: str, profile: profiles.DeviceProfile) -> list[str]:
    problems: list[str] = []
    expected_target = f"{target_symbol(profile.device)}=y"
    required = [expected_target, *REQUIRED_SELECTIONS]
    for item in required:
        if item not in resolved:
            problems.append(item)

    if "CONFIG_TARGET_mediatek_mt7986=y" in resolved:
        problems.append("the old mediatek/mt7986 target is still selected")

    for line in resolved.splitlines():
        if (
            line.startswith("CONFIG_TARGET_DEVICE_")
            and line.endswith("=y")
            and "_DEVICE_" in line
            and "PACKAGES" not in line
            and line != expected_target
        ):
            problems.append(f"another device is selected: {line}")

    for name in (
        "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox",
        "CONFIG_PACKAGE_sing-box",
    ):
        if f"{name}=y" in resolved:
            problems.append(f"{name}=y is not allowed (MTK image size)")

    return problems


def config_filename(profile: profiles.DeviceProfile) -> str:
    """Release-friendly file name, e.g. ``netcore-n60-pro.config``."""
    return profile.name.replace("_", "-") + ".config"


def static_path(
    profile: profiles.DeviceProfile,
    root: Path | None = None,
) -> Path:
    base = Path(root) if root is not None else PROJECT_ROOT
    return base / "configs" / config_filename(profile)


def _record_config(
    tree: Path,
    profile: profiles.DeviceProfile,
    *,
    dist_name: str,
    source: Path,
) -> dict:
    info = state.read(tree)
    build_date = state.build_date(info) or int(time.time())
    version = str(info.get("version") or state.version_for(build_date))
    device_info = resolve_device(tree, profile)
    info.update(
        {
            "dist": dist_name,
            "profile": profile.name,
            "artifact": profile.name,
            "board": profile.board,
            "subtarget": profile.subtarget,
            "target": profile.target,
            "device": profile.device,
            "device_vendor": device_info["device_vendor"],
            "device_model": device_info["device_model"],
            "device_variant": device_info.get("device_variant", ""),
            "device_dts": device_info.get("device_dts", ""),
            "device_source": device_info.get("device_source", ""),
            "layout": profile.layout,
            "default_lan_ip": profile.lan_ip,
            "config": str(source),
            "build_date": build_date,
            "version": version,
        }
    )
    state.write(tree, info)
    return info


def _run_defconfig(tree: Path, profile: profiles.DeviceProfile, *, log_name: str) -> str:
    log_path = tree / log_name
    code, _ = util.run(
        ["make", "defconfig"],
        cwd=tree,
        log_path=log_path,
        check=False,
    )
    if code != 0:
        tail = "\n".join(util.read_text(log_path).splitlines()[-80:]) if log_path.exists() else ""
        raise util.BuildError(f"make defconfig failed for {profile.name} ({code})\n{tail}")
    resolved = util.read_text(tree / ".config")
    problems = _check_resolved(resolved, profile)
    if problems:
        tail = "\n".join(util.read_text(log_path).splitlines()[-60:]) if log_path.exists() else ""
        raise util.BuildError(
            f"{profile.name}: generated config is invalid:\n  - "
            + "\n  - ".join(dict.fromkeys(problems))
            + "\n\nLast defconfig output:\n"
            + tail
        )
    return resolved


def _diffconfig(tree: Path) -> str:
    script = tree / "scripts" / "diffconfig.sh"
    if not script.is_file():
        raise util.BuildError(f"diffconfig script not found: {script}")
    code, output = util.run(
        ["bash", str(script)],
        cwd=tree,
        capture=True,
        quiet=True,
        check=False,
    )
    if code != 0 or not output.strip():
        raise util.BuildError(f"diffconfig.sh failed ({code})")
    return output.rstrip() + "\n"


def _config_map(text: str) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and stripped.endswith(" is not set"):
            result[stripped[2:-11].strip()] = None
        elif "=" in stripped and not stripped.startswith("#"):
            key, value = stripped.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def _roundtrip_diff(before: str, after: str) -> list[str]:
    left = _config_map(before)
    right = _config_map(after)
    keys = sorted(set(left) | set(right))
    return [key for key in keys if left.get(key) != right.get(key)]


def generate_all(tree: Path, out_dir: Path | None = None) -> list[Path]:
    """Generate a minimal ``diffconfig.sh`` fragment for every device."""
    tree = Path(tree)
    out_dir = Path(out_dir) if out_dir is not None else CONFIGS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for name in profiles.names():
        profile = profiles.require(name)
        util.header(f"Generating {config_filename(profile)}")
        util.write_text(tree / ".config", preview(tree, device=name))
        resolved = _run_defconfig(tree, profile, log_name=f"defconfig-{profile.name}.log")
        # Store only the delta from Kconfig defaults.  Build restores it and
        # runs defconfig again, which is much smaller than 9000+ lines/device.
        fragment = _diffconfig(tree)
        # Round-trip the fragment before saving it.  A diffconfig that cannot
        # reproduce the validated .config must never reach the repository.
        util.write_text(tree / ".config", fragment)
        roundtrip = _run_defconfig(tree, profile, log_name=f"roundtrip-{profile.name}.log")
        differences = _roundtrip_diff(resolved, roundtrip)
        if differences:
            raise util.BuildError(
                f"{profile.name}: diffconfig round-trip changed {len(differences)} option(s): "
                + ", ".join(differences[:12])
            )
        destination = out_dir / config_filename(profile)
        util.write_text(destination, fragment)
        generated.append(destination)
        util.log(f"generated {destination} ({len(fragment.splitlines())} lines, round-trip OK)")
    return generated


def apply(
    tree: Path,
    *,
    device: str,
    dist_name: str = "ZeroWrt",
) -> dict:
    tree = Path(tree)
    profile = profiles.require(device)
    source = static_path(profile)
    if not source.is_file():
        raise util.BuildError(f"checked-in config not found: {source}; run 'config generate' on a source tree first")

    util.header("Installing device .config")
    text = util.read_text(source)
    target = f"{target_symbol(profile.device)}=y"
    if target not in text:
        raise util.BuildError(f"{source} does not select {profile.device}")
    shutil.copyfile(source, tree / ".config")

    util.header("Expanding diffconfig (make defconfig)")
    resolved = _run_defconfig(tree, profile, log_name="defconfig.log")
    util.log(f"{source} -> {tree / '.config'} ({len(resolved.splitlines())} lines after defconfig)")
    info = _record_config(tree, profile, dist_name=dist_name, source=source)
    util.log(f"configuration ready: {profile.target} device={profile.device} version={info['version']}")
    return info
