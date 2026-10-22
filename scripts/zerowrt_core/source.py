"""Source tree handling: clone the private LEDE tree, update feeds and apply
the core ZeroWrt customisations that must happen inside the source tree.
"""

from __future__ import annotations

import os
import re
import shlex
from datetime import datetime
from pathlib import Path

from . import util
from .settings import BuildSettings

DEFAULT_REF = "ruijie-rg-x60-new"

# Feed packages that must disappear so that the ZeroWrt copies win.
# - the argon theme/plugin are cloned from jerrykuku's repositories instead
# - PassWall ships its own cores, which would otherwise clash with the feed
FEED_CONFLICTS = {
    "luci-theme-argon",
    "luci-app-argon-config",
    "luci-app-passwall",
    "luci-app-openclash",
    "luci-app-ssr-plus",
    # PassWall core libraries (see Openwrt-Passwall/openwrt-passwall README)
    "xray-core",
    "v2ray-geodata",
    "sing-box",
    "chinadns-ng",
    "dns2socks",
    "hysteria",
    "ipt2socks",
    "microsocks",
    "naiveproxy",
    "shadowsocks-rust",
    "shadowsocksr-libev",
    "simple-obfs",
    "tcping",
    "v2ray-plugin",
    "xray-plugin",
    "geoview",
    "shadow-tls",
}

CORE_FILES = {
    "version": Path("include/version.mk"),
    "config_generate": Path("package/base-files/files/bin/config_generate"),
    "config_generate_luci": Path("package/base-files/luci/bin/config_generate"),
    "default_settings": Path("package/lean/default-settings/files/zzz-default-settings"),
}

WIFI_SCRIPTS = (
    Path("package/kernel/mac80211/files/lib/wifi/mac80211.sh"),
    Path("package/network/config/wifi-scripts/files/lib/wifi/mac80211.sh"),
)

KERNEL_VERSION = "6.18"
KERNEL_BOARDS = ("mediatek", "x86")

SSID_LINE_RE = re.compile(r'^(?P<indent>[ \t]*)\[ -n "\$ssid" \] \|\| ssid=(["\']?)(?:LEDE|OpenWrt)\2[ \t]*$', re.M)
SSID_FALLBACK_RE = re.compile(r'^(?P<indent>[ \t]*)ssid=(["\']?)(?:LEDE|OpenWrt)\2[ \t]*$', re.M)
# Fixed channel widths: 40 MHz on 2.4 GHz, 160 MHz on 5 GHz. The stock script
# derives the width from what the radio reports and often ends up at 20/80.
HTMODE_TAIL = """\techo \"${prefix}${width}\"
}
"""
HTMODE_TAIL_NEW = """\t# ZeroWrt: fixed channel widths, 40 MHz on 2.4 GHz and 160 MHz on 5 GHz.
\tcase \"$band\" in
\t\t2g) echo \"${prefix}40\" ;;
\t\t5g) echo \"${prefix}160\" ;;
\t\t*) echo \"${prefix}${width}\" ;;
\tesac
}
"""

KEY_LINE_RE = re.compile(r'^(?P<indent>[ \t]*)key="\$default_key"[ \t]*$', re.M)


def _ssid_block(indent: str, settings: BuildSettings) -> str:
    lines = [f'{indent}case "$band" in']
    for band in ("2g", "5g", "6g"):
        lines.append(f"{indent}\t{band}) ssid={shlex.quote(settings.ssid(band))} ;;")
    lines.append(f"{indent}\t*) ssid={shlex.quote(settings.wifi_name)} ;;")
    lines.append(f"{indent}esac")
    return "\n".join(lines)


def _wifi_key_block(indent: str, settings: BuildSettings) -> str:
    key = shlex.quote(settings.wifi_password)
    lines = [
        f"{indent}key={key}",
        f'{indent}case "$band" in',
        f'{indent}\t6g) encryption="sae" ;;',
        f'{indent}\t*) encryption="psk2" ;;',
        f"{indent}esac",
    ]
    return "\n".join(lines)


def clone_lede(tree: Path, *, repo: str | None = None, ref: str | None = None, token: str | None = None) -> str:
    tree = Path(tree)
    repo = (repo or os.environ.get("LEDE_REPO", "")).strip()
    token = (token or os.environ.get("LEDE_TOKEN", "")).strip()
    ref = (ref or os.environ.get("LEDE_REF") or DEFAULT_REF).strip()

    if not repo:
        raise util.BuildError(
            "the LEDE_REPO secret is not configured\n"
            "Add a repository secret named LEDE_REPO with the private source "
            "repository in 'owner/name' form."
        )
    if not token:
        raise util.BuildError(
            "the LEDE_TOKEN secret is not configured\n"
            "Add a repository secret named LEDE_TOKEN with a PAT that can read "
            "the private LEDE source repository."
        )

    util.header("Cloning the LEDE source tree")
    util.log(f"reference: {ref}")
    sha = util.clone(repo, tree, ref=ref, token=token, depth=1)
    util.log(f"checked out commit {sha[:12]}")
    return sha


def _prune_packages(base: Path, names: set[str], *, removed: list[Path]) -> None:
    if not base.exists():
        return
    for root, dirs, _files in os.walk(base, topdown=True, followlinks=False):
        keep = []
        for name in dirs:
            candidate = Path(root) / name
            if name in names:
                if util.remove_path(candidate):
                    removed.append(candidate)
                continue
            keep.append(name)
        dirs[:] = keep


def prune_feed_conflicts(tree: Path) -> list[Path]:
    """Remove conflicting packages from feeds/ and from package/feeds/."""
    tree = Path(tree)
    removed: list[Path] = []
    _prune_packages(tree / "feeds", FEED_CONFLICTS, removed=removed)
    _prune_packages(tree / "package" / "feeds", FEED_CONFLICTS, removed=removed)
    for path in removed:
        util.log(f"removed feed package {path.relative_to(tree)}")
    return removed


def update_feeds(tree: Path) -> None:
    tree = Path(tree)
    feeds = tree / "scripts" / "feeds"
    if not feeds.exists():
        raise util.BuildError(f"feeds script not found: {feeds}")

    util.header("Updating OpenWrt feeds")
    util.run([str(feeds), "update", "-a"], cwd=tree, check=False, log_path=tree / "feeds-update.log")

    for required in ("luci", "packages"):
        if not (tree / "feeds" / required).exists():
            raise util.BuildError(f"feed '{required}' is missing after update; check network access")

    # Drop the conflicting sources *before* installing, then rebuild the
    # feed indexes so ``feeds install`` does not try to install the removed
    # packages again.
    prune_feed_conflicts(tree)
    util.run([str(feeds), "update", "-i", "-a"], cwd=tree, check=False)

    util.header("Installing OpenWrt feeds")
    util.run([str(feeds), "install", "-a"], cwd=tree, check=False, log_path=tree / "feeds-install.log")
    prune_feed_conflicts(tree)

    critical = {
        "luci-compat": tree / "package" / "feeds" / "luci" / "luci-compat",
        "lyaml": tree / "package" / "feeds" / "packages" / "lyaml",
    }
    missing = [name for name, path in critical.items() if not path.exists()]
    if missing:
        raise util.BuildError(
            "feeds install did not provide: " + ", ".join(missing) + "\nCheck feeds-install.log in the build tree."
        )


def remove_ssr_plus(tree: Path) -> None:
    """Drop ShadowSocksR Plus+ from the feed, the tree and default packages."""
    tree = Path(tree)
    util.header("Removing ShadowSocksR Plus+")

    removed: list[Path] = []
    for base in (tree / "package", tree / "feeds"):
        _prune_packages(base, {"luci-app-ssr-plus"}, removed=removed)
    for path in removed:
        util.log(f"removed {path.relative_to(tree)}")

    token_re = re.compile(r"(?<![\w./-])luci-app-ssr-plus(?![\w./-])[ \t]*")
    patched: list[Path] = []
    candidates = [tree / "include" / "target.mk"]
    linux_dir = tree / "target" / "linux"
    if linux_dir.exists():
        candidates.extend(linux_dir.rglob("*.mk"))
    for path in candidates:
        if not path.exists():
            continue
        text = util.read_text(path)
        if "luci-app-ssr-plus" not in text:
            continue
        util.write_text(path, token_re.sub(" ", text))
        patched.append(path)
        util.log(f"{path.relative_to(tree)}: removed luci-app-ssr-plus")

    if not removed and not patched:
        util.warn("luci-app-ssr-plus was not present")


def patch_missing_feed_deps(tree: Path) -> None:
    """kmod-fs-exfat-oot is not packaged in this tree, so luci-app-diskman only
    produces a build warning about it. Drop the dependency from the feed."""
    makefile = Path(tree) / "package/feeds/luci/luci-app-diskman/Makefile"
    if not makefile.exists():
        return

    text = util.read_text(makefile)
    updated = re.sub(r"\s*\+kmod-fs-exfat-oot", "", text)
    if updated != text:
        util.write_text(makefile, updated)
        util.log("luci-app-diskman: dropped the kmod-fs-exfat-oot dependency")


def patch_version_mk(tree: Path) -> None:
    path = Path(tree) / CORE_FILES["version"]
    if not path.exists():
        raise util.BuildError(f"missing {path}")

    util.header("Patching include/version.mk")
    # Upstream defines the default with OpenWrt or LEDE depending on the tree,
    # so rewrite whatever the assignment holds instead of matching two literals:
    # a literal that is not there is not a problem and must not warn.
    for variable in ("VERSION_DIST", "VERSION_MANUFACTURER"):
        text = util.read_text(path)
        wanted = f"{variable}:=$(if $({variable}),$({variable}),ZeroWrt)"

        if wanted in text:
            util.log(f"{variable} already points at ZeroWrt")
            continue

        updated, count = re.subn(
            rf"^{variable}:=\$\(if \$\({variable}\),\$\({variable}\),[^)\n]+\)",
            lambda _m, value=wanted: value,
            text,
            flags=re.M,
        )
        if count:
            util.write_text(path, updated)
            util.log(f"{variable} default -> ZeroWrt")
        else:
            util.warn(f"{variable} has an unexpected definition")

    version = datetime.now().strftime("%Y%m%d")
    text = util.read_text(path)
    # Force the date: CONFIG_VERSION_NUMBER is a hidden Kconfig symbol, so it
    # cannot be provided through .config reliably.
    new_text, count = re.subn(
        r"VERSION_NUMBER:=\$\(call qstrip,\$\(CONFIG_VERSION_NUMBER\)\)\s*\n"
        r"VERSION_NUMBER:=\$\(if \$\(VERSION_NUMBER\),\$\(VERSION_NUMBER\),[^)\n]+\)",
        f"VERSION_NUMBER:={version}",
        text,
    )
    if count:
        util.write_text(path, new_text)
        util.log(f"VERSION_NUMBER forced to {version}")
    else:
        # Fallback for a slightly different upstream layout.
        new_text, count = re.subn(
            r"(VERSION_NUMBER:=\$\(if \$\(VERSION_NUMBER\),\$\(VERSION_NUMBER\),)[^)\n]+(\))",
            rf"\g<1>{version}\g<2>",
            text,
        )
        if count:
            util.write_text(path, new_text)
            util.log(f"VERSION_NUMBER default set to {version}")
        else:
            util.warn("VERSION_NUMBER default was not found")


def patch_config_generate(tree: Path, ip: str) -> None:
    util.header("Patching config_generate (LAN IP / hostname)")
    for relative in (CORE_FILES["config_generate"], CORE_FILES["config_generate_luci"]):
        path = Path(tree) / relative
        if not path.exists():
            util.warn(f"missing {relative}; skipping")
            continue

        text = util.read_text(path)
        original = text
        # Default LAN address used by the generated /etc/config/network.
        text = text.replace('"192.168.1.1"', f'"{ip}"')
        text = re.sub(r'(lan\)\s*ipad=\$\{ipaddr:-")[^"]+(")', rf"\g<1>{ip}\g<2>", text)
        # Default hostname of the generated /etc/config/system.
        text = re.sub(r"(hostname=')(?:LEDE|OpenWrt)(')", r"\g<1>ZeroWrt\g<2>", text)

        if text != original:
            util.write_text(path, text)
            util.log(f"patched {relative}")
        else:
            util.warn(f"{relative}: no known defaults matched")

        final = util.read_text(path)
        if ip not in final:
            raise util.BuildError(f"{relative}: LAN address was not changed to {ip}")
        if "hostname='ZeroWrt'" not in final:
            util.warn(f"{relative}: hostname default was not changed")


def patch_default_settings(tree: Path) -> None:
    path = Path(tree) / CORE_FILES["default_settings"]
    if not path.exists():
        util.warn(f"missing {path.relative_to(tree)}; skipping distribution strings")
        return

    util.header("Patching default settings (distribution strings)")
    text = util.read_text(path)
    original = text
    text = text.replace("DISTRIB_DESCRIPTION='LEDE '", "DISTRIB_DESCRIPTION='ZeroWrt '")
    text = text.replace("DISTRIB_DESCRIPTION='OpenWrt '", "DISTRIB_DESCRIPTION='ZeroWrt '")
    text = text.replace('OPENWRT_RELEASE="LEDE R@BUILD_DATE@"', 'OPENWRT_RELEASE="ZeroWrt R@BUILD_DATE@"')
    text = text.replace('OPENWRT_RELEASE="OpenWrt R@BUILD_DATE@"', 'OPENWRT_RELEASE="ZeroWrt R@BUILD_DATE@"')

    if text != original:
        util.write_text(path, text)
        util.log(f"patched {path.relative_to(tree)}")
    else:
        util.warn("distribution description lines were not found; check the upstream file")

    final = util.read_text(path)
    if "DISTRIB_DESCRIPTION='ZeroWrt '" not in final:
        util.warn("DISTRIB_DESCRIPTION was not updated to ZeroWrt")
    if 'OPENWRT_RELEASE="ZeroWrt ' not in final:
        util.warn("OPENWRT_RELEASE was not updated to ZeroWrt")


def patch_wireless(tree: Path, settings: BuildSettings) -> None:
    """Apply the configured SSID and password to the stock WiFi generator."""
    tree = Path(tree)
    util.header("Patching default WiFi configuration")

    candidates = [tree / relative for relative in WIFI_SCRIPTS]
    if not any(path.exists() for path in candidates):
        candidates = [
            path
            for path in (tree / "package").rglob("mac80211.sh")
            if re.search(r'ssid=(["\']?)(?:LEDE|OpenWrt)\1', util.read_text(path))
        ]

    patched: list[Path] = []
    for path in candidates:
        if not path.exists():
            continue
        text = util.read_text(path)
        new_text, count = SSID_LINE_RE.subn(lambda match: _ssid_block(match.group("indent"), settings), text)
        if count == 0:
            new_text, count = SSID_FALLBACK_RE.subn(lambda match: _ssid_block(match.group("indent"), settings), text)
        if count == 0:
            continue

        new_text, key_count = KEY_LINE_RE.subn(lambda match: _wifi_key_block(match.group("indent"), settings), new_text)
        if key_count == 0:
            raise util.BuildError(f"{path.relative_to(tree)}: WiFi key default not found")

        if HTMODE_TAIL in new_text:
            new_text = new_text.replace(HTMODE_TAIL, HTMODE_TAIL_NEW, 1)
            mode_count = 1
        else:
            mode_count = 0

        util.write_text(path, new_text)
        patched.append(path)
        util.log(f"{path.relative_to(tree)}: SSIDs {settings.ssid('2g')} / {settings.ssid('5g')}")
        if mode_count:
            util.log(f"{path.relative_to(tree)}: channel width 40 MHz (2.4G) / 160 MHz (5 GHz)")
        else:
            util.warn(f"{path.relative_to(tree)}: htmode block not found, channel width unchanged")

    if not patched:
        raise util.BuildError(
            "no default SSID assignment was found in the LEDE wireless scripts; cannot apply the WiFi settings"
        )

    for path in patched:
        text = util.read_text(path)
        missing = [settings.ssid(band) for band in ("2g", "5g") if shlex.quote(settings.ssid(band)) not in text]
        if missing:
            raise util.BuildError(f"{path.relative_to(tree)}: missing SSIDs {', '.join(missing)}")
        expected_encryption = 'encryption="psk2"'
        if expected_encryption not in text:
            raise util.BuildError(f"{path.relative_to(tree)}: expected {expected_encryption} was not applied")


def patch_kernel_version(tree: Path, version: str = KERNEL_VERSION) -> None:
    """Switch the selected target boards to the requested kernel patch version."""
    tree = Path(tree)
    util.header(f"Switching kernel to {version}")
    patched: list[Path] = []
    for board in KERNEL_BOARDS:
        path = tree / "target" / "linux" / board / "Makefile"
        if not path.exists():
            continue
        text = util.read_text(path)
        new_text, count = re.subn(r"^KERNEL_PATCHVER\s*:?=\s*.*$", f"KERNEL_PATCHVER:={version}", text, flags=re.M)
        new_text, count2 = re.subn(
            r"^KERNEL_TESTING_PATCHVER\s*:?=\s*.*$",
            f"KERNEL_TESTING_PATCHVER:={version}",
            new_text,
            flags=re.M,
        )
        if count or count2:
            util.write_text(path, new_text)
            patched.append(path)
            util.log(f"{path.relative_to(tree)}: kernel {version}")

    if not patched:
        raise util.BuildError("no target Makefile with KERNEL_PATCHVER was found; cannot switch the kernel")


TURBOACC_HW_DEVICES = {
    # Devices with the MediaTek PPE and WED hardware accelerators.
    "ruijie_rg-x60-new": True,
    "x86_64": False,
}


def patch_turboacc(tree: Path, settings: BuildSettings) -> None:
    """Ship default TurboACC settings for this device.

    The settings live in the image overlay instead of a target tree so that
    upstream pull requests keep applying cleanly.
    """
    tree = Path(tree)
    path = tree / "files" / "etc" / "uci-defaults" / "99-zerowrt-turboacc"
    path.parent.mkdir(parents=True, exist_ok=True)

    hardware = TURBOACC_HW_DEVICES.get(settings.device, False)

    lines = [
        "#!/bin/sh",
        "# Generated by ZeroWrt: TurboACC defaults for this device.",
        "[ -f /etc/config/turboacc ] || exit 0",
        "",
        "uci -q set turboacc.config.tcpcca='bbr'",
    ]

    if hardware:
        lines += [
            "",
            "# MT7986A: hardware NAT plus the wireless offload (WED).",
            "uci -q set turboacc.config.fastpath='flow_offloading'",
            "uci -q set turboacc.config.fastpath_fo_hw='1'",
            "uci -q set turboacc.config.fastpath_mh_eth_hnat_wed='1'",
        ]

    lines += ["", "uci -q commit turboacc", "exit 0", ""]

    path.write_text("\n".join(lines), encoding="utf-8")
    path.chmod(0o755)
    util.log(f"wrote {path.relative_to(tree)} for {settings.device}")


def apply_core_customisations(tree: Path, settings: BuildSettings) -> None:
    tree = Path(tree)
    patch_version_mk(tree)
    patch_config_generate(tree, settings.ip)
    patch_default_settings(tree)
    patch_wireless(tree, settings)
    patch_kernel_version(tree)
    patch_missing_feed_deps(tree)
    remove_ssr_plus(tree)
    patch_turboacc(tree, settings)
    verify_core(tree, settings)


def verify_core(tree: Path, settings: BuildSettings) -> None:
    tree = Path(tree)
    util.header("Verifying core customisations")
    problems: list[str] = []

    version = util.read_text(tree / CORE_FILES["version"])
    if "VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),ZeroWrt)" not in version:
        problems.append("VERSION_DIST default is not ZeroWrt")
    if "VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),ZeroWrt)" not in version:
        problems.append("VERSION_MANUFACTURER default is not ZeroWrt")

    for relative in (CORE_FILES["config_generate"], CORE_FILES["config_generate_luci"]):
        path = tree / relative
        if path.exists() and settings.ip not in util.read_text(path):
            problems.append(f"{relative} does not default to {settings.ip}")

    for relative in WIFI_SCRIPTS:
        path = tree / relative
        if path.exists():
            text = util.read_text(path)
            if shlex.quote(settings.ssid("2g")) not in text or shlex.quote(settings.ssid("5g")) not in text:
                problems.append(f"{relative} does not set {settings.ssid('2g')} / {settings.ssid('5g')}")

    target_mk = tree / "include" / "target.mk"
    if target_mk.exists() and "luci-app-ssr-plus" in util.read_text(target_mk):
        problems.append("include/target.mk still references luci-app-ssr-plus")

    for board in KERNEL_BOARDS:
        path = tree / "target" / "linux" / board / "Makefile"
        if path.exists() and f"KERNEL_PATCHVER:={KERNEL_VERSION}" not in util.read_text(path):
            problems.append(f"target/linux/{board}/Makefile does not use kernel {KERNEL_VERSION}")

    if problems:
        raise util.BuildError("core customisation failed:\n  - " + "\n  - ".join(problems))
    util.log("core customisations verified")
