"""External packages and feed conflict removal.

Only the packages that must differ from the 24.10 feeds are cloned here:

* PassWall (LuCI app + its core packages)
* OpenClash
* Argon theme (the theme now contains the Argon configuration UI)
* luci-app-ota
* Go 1.27 (Xray needs it)

Everything is cloned below ``package/new`` (except Go, which replaces the feed
directory it belongs to).  A package name scanner then removes the feed copies,
including the ``package/feeds`` symlinks, so the buildroot cannot silently pick
an old PassWall core or the feed Argon theme.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from . import util

PASSWALL_REPO = "Openwrt-Passwall/openwrt-passwall"
PASSWALL_REF = "f19da54330424c54e16fd636cee5d76a2a6ee102"
PASSWALL_DIR = "openwrt-passwall"

PASSWALL_PACKAGES_REPO = "Openwrt-Passwall/openwrt-passwall-packages"
PASSWALL_PACKAGES_REF = "da712cf06cf4e6fd39e147fb36e6ec936003fcc9"
PASSWALL_PACKAGES_DIR = "openwrt-passwall-packages"

OPENCLASH_REPO = "vernesong/OpenClash"
OPENCLASH_REF = "e553e82e01c697aefbe1555261a503f425e00ccd"
OPENCLASH_DIR = "OpenClash"

ARGON_THEME_REPO = "jerrykuku/luci-theme-argon"
ARGON_THEME_REF = "c6d63bd68aa9272e40c35cee5e615f45cc1e4eb0"
ARGON_THEME_DIR = "luci-theme-argon"

OTA_REPO = "MinimaxFlora/luci-app-ota"
OTA_REF = "929cece34b27bb8816178eb490b86f7138133512"

GOLANG_REPO = "sbwml/packages_lang_golang"
GOLANG_REF = "cd8953c31e0f64ea2853f87bb0f32256646a160d"

BUILD_PACKAGE_RE = re.compile(r"call\s+BuildPackage,\s*([^)\n]+)\)")
NAME_RE = re.compile(r"^(?:PKG_NAME|LUCI_NAME)\s*:?=\s*(\S+)", re.M)


def _makefile_names(makefile: Path) -> set[str]:
    if not makefile.is_file():
        return set()
    text = util.read_text(makefile)
    match = NAME_RE.search(text)
    pkg_name = match.group(1).strip() if match else ""

    names: set[str] = set()
    for raw in BUILD_PACKAGE_RE.findall(text):
        name = raw.replace("$(PKG_NAME)", pkg_name).strip()
        if name and "$" not in name:
            names.add(name)
    if pkg_name and "$" not in pkg_name:
        names.add(pkg_name)
    if names:
        return names
    # LuCI themes and some applications rely on the directory name rather than
    # an explicit PKG_NAME.  The parent directory is the package name in that
    # case, and it is also a useful fallback for older Makefiles.
    return {makefile.parent.name}


def declared_package_names(directory: Path) -> set[str]:
    """Package names declared by ``directory/Makefile``."""
    return _makefile_names(Path(directory) / "Makefile")


def package_names_under(root: Path) -> set[str]:
    """Every package name declared by any Makefile below *root*."""
    root = Path(root)
    names: set[str] = set()
    if not root.is_dir():
        return names
    for makefile in root.rglob("Makefile"):
        names |= _makefile_names(makefile)
    return names


def new_package_names(tree: Path) -> set[str]:
    return package_names_under(Path(tree) / "package" / "new")


def _prune_feed_packages(base: Path, names: set[str], *, removed: list[Path]) -> None:
    """Delete package directories below *base* that provide one of ``names``."""
    base = Path(base)
    if not base.exists():
        return
    candidates = {makefile.parent for makefile in base.rglob("Makefile")}
    # The Go feed is intentionally replaced in place; never prune it even if a
    # cloned package happens to declare a package named "golang".
    protected = base / "packages" / "lang" / "golang"
    # Deepest first: removing a parent must not hide a nested package that also
    # needs to be reported.
    for candidate in sorted(candidates, key=lambda path: len(path.parts), reverse=True):
        if not candidate.exists():
            continue
        if candidate == protected or protected in candidate.parents:
            continue
        if declared_package_names(candidate) & names and util.remove_path(candidate):
            removed.append(candidate)


def prune_feed_conflicts(tree: Path) -> list[Path]:
    """Remove feed copies of every package cloned into ``package/new``."""
    tree = Path(tree)
    names = new_package_names(tree)
    removed: list[Path] = []
    if not names:
        return removed

    _prune_feed_packages(tree / "feeds", names, removed=removed)
    _prune_feed_packages(tree / "package" / "feeds", names, removed=removed)

    # Symlinks are not package directories; remove the ones whose name matches,
    # then clean up links that became dangling after the feed copy was deleted.
    links_root = tree / "package" / "feeds"
    if links_root.exists():
        for path in sorted(links_root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
            if not path.is_symlink():
                continue
            if (path.name in names or not path.exists()) and util.remove_path(path):
                removed.append(path)

    for path in removed:
        try:
            util.log(f"removed feed duplicate {path.relative_to(tree)}")
        except ValueError:
            util.log(f"removed feed duplicate {path}")
    return removed


def _clone(repo: str, ref: str, dest: Path) -> Path:
    dest = Path(dest)
    if dest.is_symlink() or dest.exists():
        util.remove_path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    util.log(f"adding {dest.name} ({repo} @ {ref})")
    util.clone(repo, dest, ref=ref, token=None, depth=1)
    return dest


def _replace_feed_dir(tree: Path, relative: Path, repo: str, ref: str) -> Path:
    return _clone(repo, ref, Path(tree) / relative)


def _ensure_golang_link(tree: Path) -> None:
    """Keep ``package/feeds/packages/golang`` valid after replacing the feed dir."""
    link = Path(tree) / "package" / "feeds" / "packages" / "golang"
    target = Path(tree) / "feeds" / "packages" / "lang" / "golang"
    if not target.exists():
        return
    if link.is_symlink() and not link.exists():
        util.remove_path(link)
    if link.exists() or link.is_symlink():
        return
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(os.path.relpath(target, link.parent))


def add_external_packages(tree: Path) -> None:
    """Clone the external package set and remove the feed duplicates."""
    tree = Path(tree)
    new_dir = tree / "package" / "new"
    new_dir.mkdir(parents=True, exist_ok=True)

    _clone(PASSWALL_REPO, PASSWALL_REF, new_dir / PASSWALL_DIR)
    passwall_packages = _clone(
        PASSWALL_PACKAGES_REPO,
        PASSWALL_PACKAGES_REF,
        new_dir / PASSWALL_PACKAGES_DIR,
    )
    # PassWall can select Sing-Box, but on MT7986 it only makes the image much
    # larger.  Remove both the cloned source and the feed copy; the .config also
    # explicitly unsets it.
    util.remove_path(passwall_packages / "sing-box")
    util.remove_path(tree / "feeds" / "packages" / "net" / "sing-box")
    util.remove_path(tree / "package" / "feeds" / "packages" / "sing-box")
    # homeproxy is a sing-box front end; leaving it in the tree only produces a
    # "dependency on sing-box which does not exist" defconfig warning.
    util.remove_path(tree / "feeds" / "luci" / "applications" / "luci-app-homeproxy")
    util.remove_path(tree / "package" / "feeds" / "luci" / "luci-app-homeproxy")

    _clone(OPENCLASH_REPO, OPENCLASH_REF, new_dir / OPENCLASH_DIR)

    theme = _clone(ARGON_THEME_REPO, ARGON_THEME_REF, new_dir / ARGON_THEME_DIR)
    # New Argon releases integrate the configuration UI into the theme.  Drop
    # the compatibility shim (if present) and the old feed package so there is
    # exactly one Argon implementation in the tree.
    util.remove_path(theme / "compat")
    util.remove_path(tree / "feeds" / "luci" / "applications" / "luci-app-argon-config")
    util.remove_path(tree / "package" / "feeds" / "luci" / "luci-app-argon-config")

    add_ota_app(tree)
    _replace_feed_dir(tree, Path("feeds/packages/lang/golang"), GOLANG_REPO, GOLANG_REF)

    _validate_layout(new_dir)
    prune_feed_conflicts(tree)
    _ensure_golang_link(tree)


def add_ota_app(tree: Path) -> Path:
    """Clone ``luci-app-ota`` into ``package/new``."""
    dest = _clone(OTA_REPO, OTA_REF, Path(tree) / "package" / "new" / "luci-app-ota")
    if not (dest / "Makefile").exists():
        raise util.BuildError(f"luci-app-ota checkout is missing a Makefile: {dest}")
    if not (dest / "root" / "usr" / "bin" / "ota").exists():
        raise util.BuildError(f"luci-app-ota checkout is incomplete: {dest}")
    util.log("OTA app added: package/new/luci-app-ota")
    return dest


def _validate_layout(new_dir: Path) -> None:
    checks = {
        "package/new/openwrt-passwall/luci-app-passwall/Makefile": new_dir
        / "openwrt-passwall"
        / "luci-app-passwall"
        / "Makefile",
        "package/new/openwrt-passwall-packages/xray-core/Makefile": new_dir
        / "openwrt-passwall-packages"
        / "xray-core"
        / "Makefile",
        "package/new/OpenClash/luci-app-openclash/Makefile": new_dir / "OpenClash" / "luci-app-openclash" / "Makefile",
        "package/new/luci-theme-argon/Makefile": new_dir / "luci-theme-argon" / "Makefile",
        "package/new/luci-app-ota/Makefile": new_dir / "luci-app-ota" / "Makefile",
    }
    missing = [name for name, path in checks.items() if not path.exists()]
    if missing:
        raise util.BuildError("unexpected repository layout, missing:\n  - " + "\n  - ".join(missing))

    theme = new_dir / "luci-theme-argon"
    for relative in (
        theme / "root/etc/config/argon",
        theme / "htdocs/luci-static/argon/img/bg1.webp",
        theme / "htdocs/luci-static/argon/favicon.ico",
        theme / "htdocs/luci-static/resources/view/argon-config.js",
    ):
        if not relative.exists():
            raise util.BuildError(f"Argon theme is incomplete, missing: {relative}")

    if (new_dir / "openwrt-passwall-packages" / "sing-box").exists():
        raise util.BuildError("sing-box is still present in package/new; remove it before building")
