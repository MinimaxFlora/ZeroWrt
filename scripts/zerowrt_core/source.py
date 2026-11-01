"""Source tree handling: clone the ImmortalWrt tree, update feeds and apply the
core ZeroWrt customisations that have to happen inside it.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from . import packages, profiles, util
from .settings import BuildSettings

CORE_FILES = {
    "version": Path("include/version.mk"),
    "config_generate": Path("package/base-files/files/bin/config_generate"),
    "openwrt_release": Path("package/base-files/files/etc/openwrt_release"),
    "os_release": Path("package/base-files/files/usr/lib/os-release"),
    "banner": Path("package/base-files/files/etc/banner"),
    # The MTK wireless stack generates /etc/config/wireless here.
    "mtwifi": Path("package/mtk/applications/mtwifi-cfg/files/mtwifi.sh"),
}

# Tree level overlay. ImmortalWrt ships files/etc/banner, and that copy wins
# over package/base-files/files/etc/banner in the image, so the directory is
# removed before the ZeroWrt banner is installed.
TREE_OVERLAY = Path("files")

# The ZeroWrt login banner, kept with the other branding assets so that it can
# be edited without touching the build code.
BANNER_FILE = Path("assets") / "banner"
REPO_ROOT = Path(__file__).resolve().parents[2]

# mtwifi.sh ships one default SSID per radio band and leaves the network open.
MTWIFI_SSID_RE = re.compile(r'ssid="(?:ImmortalWrt|LEDE|OpenWrt)-(2\.4G|5G|6G)"')
MTWIFI_OPEN_RE = re.compile(r"(?P<indent>[ \t]*)set wireless\.default_\$\{dev\}\.encryption=none\n")
MTWIFI_BANDS = {"2.4G": "2g", "5G": "5g", "6G": "6g"}

IPAD_RE = re.compile(r'ipad=\$\{ipaddr:-"[^"]*"\}')
HOSTNAME_RE = re.compile(r"(hostname=')(?:LEDE|OpenWrt|ImmortalWrt)(')")


def clone_source(
    tree: Path,
    *,
    device: str,
    repo: str | None = None,
    ref: str | None = None,
) -> dict[str, str]:
    """Clone the source tree that *device* is built from and return its info."""
    profile = profiles.require(device)
    source = profiles.source(profile)
    repo = (repo or os.environ.get("ZEROWRT_SOURCE_REPO") or source.repo).strip()
    ref = (ref or os.environ.get("ZEROWRT_SOURCE_REF") or source.ref).strip()

    util.header(f"Cloning {source.label}")
    util.log(f"repository: {repo}")
    util.log(f"reference: {ref}")
    sha = util.clone(repo, Path(tree), ref=ref, token=None, depth=1)
    util.log(f"checked out commit {sha[:12]}")
    return {
        "repo": repo,
        "ref": ref,
        "commit": sha,
        "source": profile.source,
        "label": source.label,
    }


def _prune_packages(base: Path, names: set[str], *, removed: list[Path]) -> None:
    """Delete every directory that provides one of ``names``.

    A package directory counts when its *name* matches or when its Makefile
    registers one of the names with ``BuildPackage``. The second test matters
    because the feeds do not use our directory names: helloworld's
    ``v2ray-geodata`` builds ``v2ray-geoip`` and ``v2ray-geosite``, both of
    which also come out of ``feeds/packages/net/v2ray-geodata``.
    A directory only counts as a package when it owns a Makefile: a LuCI app
    ships static assets under paths such as ``htdocs/.../mosdns``, which we
    must leave alone.
    """
    if not base.exists():
        return
    for root, dirs, _files in os.walk(base, topdown=True, followlinks=False):
        keep = []
        for name in dirs:
            candidate = Path(root) / name
            if (candidate / "Makefile").is_file() and (
                candidate.name in names or packages.declared_package_names(candidate) & names
            ):
                if util.remove_path(candidate):
                    removed.append(candidate)
                continue
            keep.append(name)
        dirs[:] = keep


def prune_feed_conflicts(tree: Path) -> list[Path]:
    """Remove conflicting packages from feeds/ and from package/feeds/.

    Anything that is cloned into ``package/new`` has to disappear here: two
    sources for one package name make the buildroot report a duplicate, and
    the feed version usually wins silently because it was scanned first.
    """
    tree = Path(tree)
    names = packages.new_package_names(tree)
    removed: list[Path] = []
    _prune_packages(tree / "feeds", names, removed=removed)
    _prune_packages(tree / "package" / "feeds", names, removed=removed)
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


def strip_tree_overlay(tree: Path) -> None:
    """Delete the tree level ``files/`` overlay.

    ImmortalWrt keeps ``files/etc/banner`` there and that copy overrides the
    base-files banner in the image, which would silently undo the ZeroWrt
    branding. The directory holds nothing else today.
    """
    tree = Path(tree)
    overlay = tree / TREE_OVERLAY
    if not overlay.exists():
        return
    util.header("Removing the tree overlay")
    if util.remove_path(overlay):
        util.log(f"removed {TREE_OVERLAY}/")
    else:
        raise util.BuildError(f"unable to remove {overlay}")


def patch_version_mk(tree: Path) -> None:
    path = Path(tree) / CORE_FILES["version"]
    if not path.exists():
        raise util.BuildError(f"missing {path}")

    util.header("Patching include/version.mk")
    # Upstream names the distribution ImmortalWrt (OpenWrt or LEDE in other
    # trees), so rewrite whatever the assignment holds instead of matching a
    # literal: a literal that is not there is not a problem.
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


def patch_release_files(tree: Path) -> None:
    """Write the ZeroWrt release strings the way the old ``sed`` commands did.

    The tree ships *templates* here (``%D``/``%V``/``%C``), so the strings are
    written as literals instead of relying on substitution.
    """
    tree = Path(tree)
    date = datetime.now().strftime("%Y%m%d")
    description = f"ZeroWrt-{date}"
    revision = " By MinimaxFlora"
    release_line = f'OPENWRT_RELEASE="ZeroWrt 标准版 @R{date} BY MinimaxFlora"'

    util.header("Patching release strings")

    release = tree / CORE_FILES["openwrt_release"]
    if release.exists():
        text = util.read_text(release)
        text, description_count = re.subn(
            r"^DISTRIB_DESCRIPTION=.*$",
            f"DISTRIB_DESCRIPTION='{description}'",
            text,
            flags=re.M,
        )
        text, revision_count = re.subn(
            r"^DISTRIB_REVISION=.*$",
            f"DISTRIB_REVISION='{revision}'",
            text,
            flags=re.M,
        )
        util.write_text(release, text)
        util.log(f"patched {CORE_FILES['openwrt_release']}")
        if not description_count or not revision_count:
            util.warn(f"{CORE_FILES['openwrt_release']}: DISTRIB_* lines were not all found")
    else:
        util.warn(f"missing {CORE_FILES['openwrt_release']}")

    os_release = tree / CORE_FILES["os_release"]
    if os_release.exists():
        text, count = re.subn(r"^OPENWRT_RELEASE=.*$", release_line, util.read_text(os_release), flags=re.M)
        util.write_text(os_release, text)
        util.log(f"patched {CORE_FILES['os_release']}")
        if not count:
            util.warn(f"{CORE_FILES['os_release']}: OPENWRT_RELEASE was not found")
    else:
        util.warn(f"missing {CORE_FILES['os_release']}")


def read_banner(assets_dir: Path | str | None = None) -> str | None:
    """Read the ZeroWrt banner art, or None when the asset is unavailable."""
    candidates = [REPO_ROOT / BANNER_FILE]
    if assets_dir:
        candidates.insert(0, Path(assets_dir) / BANNER_FILE)
    for path in candidates:
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return None


def patch_banner(tree: Path, assets_dir: Path | str | None = None) -> bool:
    """Replace the login banner shipped by base-files with the ZeroWrt art."""
    tree = Path(tree)
    banner = read_banner(assets_dir)
    if banner is None:
        util.warn(f"{BANNER_FILE} not found; keeping the upstream banner")
        return False

    path = tree / CORE_FILES["banner"]
    if not path.exists():
        util.warn(f"missing {CORE_FILES['banner']}; skipping the banner")
        return False
    if util.read_text(path) == banner:
        util.log("login banner already up to date")
        return True

    util.write_text(path, banner)
    util.log(f"patched {CORE_FILES['banner']}")
    return True


def patch_config_generate(tree: Path, ip: str) -> None:
    path = Path(tree) / CORE_FILES["config_generate"]
    if not path.exists():
        raise util.BuildError(f"missing {path}")

    util.header("Patching config_generate (LAN IP / hostname)")
    text = util.read_text(path)
    original = text
    # Default LAN address of the generated /etc/config/network. ImmortalWrt has
    # a per-board branch ("ruijie,rg-x60*") that defaults to 192.168.110.1, so
    # every "ipad=${ipaddr:-...}" default is rewritten.
    text = IPAD_RE.sub(f'ipad=${{ipaddr:-"{ip}"}}', text)
    # Default hostname of the generated /etc/config/system.
    text = HOSTNAME_RE.sub(r"\g<1>ZeroWrt\g<2>", text)

    if text != original:
        util.write_text(path, text)
        util.log(f"patched {CORE_FILES['config_generate']}")
    else:
        util.warn(f"{CORE_FILES['config_generate']}: no known defaults matched")

    final = util.read_text(path)
    if ip not in final:
        raise util.BuildError(f"{CORE_FILES['config_generate']}: LAN address was not changed to {ip}")
    if "hostname='ZeroWrt'" not in final:
        util.warn(f"{CORE_FILES['config_generate']}: hostname default was not changed")


def patch_wifi(tree: Path, settings: BuildSettings) -> None:
    """Apply the SSID and password to ImmortalWrt's MTK wireless generator.

    ``mtwifi.sh`` probes the closed-source MTK driver and writes one
    ``wifi-iface`` per radio, with a hardcoded ``ImmortalWrt-2.4G`` /
    ``ImmortalWrt-5G`` SSID and ``encryption=none``.
    """
    tree = Path(tree)
    util.header("Patching default WiFi configuration (mtwifi)")

    path = tree / CORE_FILES["mtwifi"]
    if not path.exists():
        raise util.BuildError(f"missing {CORE_FILES['mtwifi']}; cannot apply the WiFi settings")

    text = util.read_text(path)
    expected_ssids = [f'ssid="{settings.ssid(band)}"' for band in ("2g", "5g")]
    if all(item in text for item in expected_ssids) and "encryption=psk2" in text:
        util.log("default WiFi configuration already up to date")
        return

    def ssid_line(match: re.Match[str]) -> str:
        return f'ssid="{settings.ssid(MTWIFI_BANDS[match.group(1)])}"'

    text, ssid_count = MTWIFI_SSID_RE.subn(ssid_line, text)
    if ssid_count < 2:
        raise util.BuildError(f"{CORE_FILES['mtwifi']}: expected a 2.4G and a 5G default SSID, found {ssid_count}")

    key = settings.wifi_password

    def open_network(match: re.Match[str]) -> str:
        indent = match.group("indent")
        return (
            f"{indent}set wireless.default_${{dev}}.encryption=psk2\n{indent}set wireless.default_${{dev}}.key={key}\n"
        )

    text, open_count = MTWIFI_OPEN_RE.subn(open_network, text)
    if open_count != 1:
        raise util.BuildError(f"{CORE_FILES['mtwifi']}: expected one open default wifi-iface, found {open_count}")

    util.write_text(path, text)
    util.log(f"patched {CORE_FILES['mtwifi']}")

    final = util.read_text(path)
    for band in ("2g", "5g"):
        if f'ssid="{settings.ssid(band)}"' not in final:
            raise util.BuildError(f"{CORE_FILES['mtwifi']}: SSID {settings.ssid(band)} was not applied")
    for expected in ("encryption=psk2", f"key={key}"):
        if expected not in final:
            raise util.BuildError(f"{CORE_FILES['mtwifi']}: expected {expected} was not applied")


def apply_core_customisations(tree: Path, settings: BuildSettings, assets_dir: Path | str | None = None) -> None:
    tree = Path(tree)
    strip_tree_overlay(tree)
    patch_version_mk(tree)
    patch_release_files(tree)
    patch_config_generate(tree, settings.ip)
    patch_banner(tree, assets_dir)
    patch_wifi(tree, settings)
    verify_core(tree, settings, assets_dir)


def verify_core(tree: Path, settings: BuildSettings, assets_dir: Path | str | None = None) -> None:
    tree = Path(tree)
    util.header("Verifying core customisations")
    problems: list[str] = []

    version = util.read_text(tree / CORE_FILES["version"])
    if "VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),ZeroWrt)" not in version:
        problems.append("VERSION_DIST default is not ZeroWrt")
    if "VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),ZeroWrt)" not in version:
        problems.append("VERSION_MANUFACTURER default is not ZeroWrt")

    release = tree / CORE_FILES["openwrt_release"]
    if release.exists():
        text = util.read_text(release)
        if not re.search(r"^DISTRIB_DESCRIPTION='ZeroWrt-\d{8}'$", text, re.M):
            problems.append("DISTRIB_DESCRIPTION is not 'ZeroWrt-<date>'")
        if "DISTRIB_REVISION=' By MinimaxFlora'" not in text:
            problems.append("DISTRIB_REVISION is not ' By MinimaxFlora'")

    os_release = tree / CORE_FILES["os_release"]
    if os_release.exists():
        text = util.read_text(os_release)
        if not re.search(r'^OPENWRT_RELEASE="ZeroWrt 标准版 @R\d{8} BY MinimaxFlora"$', text, re.M):
            problems.append("OPENWRT_RELEASE is not the ZeroWrt release string")

    config_generate = tree / CORE_FILES["config_generate"]
    if config_generate.exists():
        text = util.read_text(config_generate)
        # Every board branch has its own default (the ruijie,rg-x60* branch
        # ships 192.168.110.1); the LAN address must not depend on the board.
        defaults = set(re.findall(r'ipad=\$\{ipaddr:-"([^"]*)"\}', text))
        wrong = sorted(value for value in defaults if value != settings.ip)
        if wrong:
            problems.append(f"{CORE_FILES['config_generate']} still defaults to {', '.join(wrong)}")

    mtwifi = tree / CORE_FILES["mtwifi"]
    if mtwifi.exists():
        text = util.read_text(mtwifi)
        missing = [settings.ssid(band) for band in ("2g", "5g") if f'ssid="{settings.ssid(band)}"' not in text]
        if missing:
            problems.append(f"{CORE_FILES['mtwifi']} does not set {', '.join(missing)}")
    else:
        problems.append(f"{CORE_FILES['mtwifi']} is missing")

    if (tree / TREE_OVERLAY).exists():
        problems.append(f"{TREE_OVERLAY}/ overlay is still present")

    banner = read_banner(assets_dir)
    if banner is not None:
        banner_path = tree / CORE_FILES["banner"]
        if not banner_path.exists():
            problems.append(f"{CORE_FILES['banner']} is missing")
        elif util.read_text(banner_path) != banner:
            problems.append(f"{CORE_FILES['banner']} does not match {BANNER_FILE}")

    if problems:
        raise util.BuildError("core customisation failed:\n  - " + "\n  - ".join(problems))
    util.log("core customisations verified")
