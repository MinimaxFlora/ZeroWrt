"""External packages and Argon branding.

Everything that is fetched from GitHub lives under ``package/new`` so the
upstream LEDE tree stays untouched and updates never conflict.

The Argon theme is pinned to the last 2.x release on purpose: 3.x merged the
configuration UI into the theme package, which would collide with the
standalone ``luci-app-argon-config`` package requested for ZeroWrt.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from . import images, util

ARGON_THEME_REPO = "jerrykuku/luci-theme-argon"
ARGON_THEME_REF = "master"
ARGON_CONFIG_REPO = "jerrykuku/luci-app-argon-config"
ARGON_CONFIG_REF = "master"
PASSWALL_REPO = "Openwrt-Passwall/openwrt-passwall"
PASSWALL_REF = "main"
PASSWALL_PACKAGES_REPO = "Openwrt-Passwall/openwrt-passwall-packages"
PASSWALL_PACKAGES_REF = "main"
OPENCLASH_REPO = "vernesong/OpenClash"
OPENCLASH_REF = "master"

PACKAGE_DIR_NAMES = {
    "luci-theme-argon",
    "luci-app-argon-config",
    "luci-app-passwall",
    "luci-app-openclash",
}


def _env(name: str, default: str) -> str:
    return (os.environ.get(name) or default).strip()


def remove_existing_package_dirs(tree: Path) -> None:
    """Drop any copy of the packages we replace (feeds, package/lean, ...)."""
    tree = Path(tree)
    package_root = tree / "package"
    if not package_root.exists():
        return
    for root, dirs, _files in os.walk(package_root, topdown=True, followlinks=False):
        keep = []
        for name in dirs:
            candidate = Path(root) / name
            if name in PACKAGE_DIR_NAMES:
                if util.remove_path(candidate):
                    util.log(f"removed existing package {candidate.relative_to(tree)}")
                continue
            keep.append(name)
        dirs[:] = keep


def _clone(repo: str, ref: str, dest: Path) -> None:
    if dest.exists():
        util.remove_path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    util.log(f"adding {dest.name} ({repo} @ {ref})")
    util.clone(repo, dest, ref=ref, token=None, depth=1)


def add_external_packages(tree: Path) -> None:
    tree = Path(tree)
    new_dir = tree / "package" / "new"
    new_dir.mkdir(parents=True, exist_ok=True)

    remove_existing_package_dirs(tree)

    theme_repo = _env("ARGON_THEME_REPO", ARGON_THEME_REPO)
    theme_ref = _env("ARGON_THEME_REF", ARGON_THEME_REF)
    theme_dir = new_dir / "luci-theme-argon"
    _clone(theme_repo, theme_ref, theme_dir)

    if not (theme_dir / "Makefile").exists():
        raise util.BuildError(f"Argon theme checkout is missing a Makefile: {theme_dir}")

    integrated = theme_is_integrated(theme_dir)
    if integrated:
        # Argon 3.x ships the settings app inside the theme. Keep the tree
        # buildable and explain the deviation instead of creating file
        # conflicts with the standalone migration package.
        util.warn(
            "Argon master includes the configuration app; the standalone "
            "luci-app-argon-config is skipped to avoid duplicate files"
        )
        util.remove_path(theme_dir / "compat")
        config_dir = None
    else:
        config_repo = _env("ARGON_CONFIG_REPO", ARGON_CONFIG_REPO)
        config_ref = _env("ARGON_CONFIG_REF", ARGON_CONFIG_REF)
        config_dir = new_dir / "luci-app-argon-config"
        _clone(config_repo, config_ref, config_dir)
        if not (config_dir / "Makefile").exists():
            raise util.BuildError(f"luci-app-argon-config checkout is missing a Makefile: {config_dir}")

    _clone(
        _env("PASSWALL_REPO", PASSWALL_REPO),
        _env("PASSWALL_REF", PASSWALL_REF),
        new_dir / "passwall-luci",
    )
    _clone(
        _env("PASSWALL_PACKAGES_REPO", PASSWALL_PACKAGES_REPO),
        _env("PASSWALL_PACKAGES_REF", PASSWALL_PACKAGES_REF),
        new_dir / "passwall-packages",
    )
    _clone(
        _env("OPENCLASH_REPO", OPENCLASH_REPO),
        _env("OPENCLASH_REF", OPENCLASH_REF),
        new_dir / "openclash",
    )
    _fix_openclash(new_dir / "openclash")

    _validate_layout(new_dir)


def _fix_openclash(openclash_dir: Path) -> None:
    """OpenClash calls po2lmo from the luci-base host build without declaring
    the dependency. Add it so a clean parallel build cannot race."""
    makefile = Path(openclash_dir) / "luci-app-openclash" / "Makefile"
    if not makefile.exists():
        return
    text = util.read_text(makefile)
    if "luci-base/host" in text:
        return
    if "PKG_BUILD_DEPENDS" in text:
        text = re.sub(
            r"^(PKG_BUILD_DEPENDS\s*[:+]?=\s*)",
            r"\1luci-base/host ",
            text,
            count=1,
            flags=re.M,
        )
    else:
        text = text.replace(
            "include $(TOPDIR)/rules.mk",
            "include $(TOPDIR)/rules.mk\n\nPKG_BUILD_DEPENDS += luci-base/host",
            1,
        )
    util.write_text(makefile, text)
    util.log("openclash: added luci-base/host build dependency (po2lmo)")


def _validate_layout(new_dir: Path) -> None:
    checks = {
        "package/new/passwall-luci/luci-app-passwall/Makefile": (
            new_dir / "passwall-luci" / "luci-app-passwall" / "Makefile"
        ),
        "package/new/passwall-packages/xray-core/Makefile": (new_dir / "passwall-packages" / "xray-core" / "Makefile"),
        "package/new/openclash/luci-app-openclash/Makefile": (
            new_dir / "openclash" / "luci-app-openclash" / "Makefile"
        ),
    }
    missing = [name for name, path in checks.items() if not path.exists()]
    if missing:
        raise util.BuildError("unexpected repository layout, missing:\n  - " + "\n  - ".join(missing))


def theme_is_integrated(theme_dir: Path) -> bool:
    """True for Argon 3.x, where the configuration UI ships with the theme."""
    return any(
        (Path(theme_dir) / relative).exists()
        for relative in (
            "root/etc/config/argon",
            "root/usr/libexec/rpcd/luci.argon_branding",
            "root/usr/share/luci/menu.d/luci-app-argon-config.json",
        )
    )


def _write_text_if_changed(path: Path, text: str) -> None:
    if not path.exists() or util.read_text(path) != text:
        util.write_text(path, text)


def patch_argon_theme(theme_dir: Path, assets_dir: Path) -> None:
    theme_dir = Path(theme_dir)
    assets_dir = Path(assets_dir)
    util.header("Branding the Argon theme")

    static = theme_dir / "htdocs" / "luci-static" / "argon"
    if not static.exists():
        raise util.BuildError(f"cannot find the Argon static assets in {theme_dir}")

    background = (assets_dir / "background.jpg").read_bytes()
    logo = (assets_dir / "logo.png").read_bytes()

    bg_jpg = static / "img" / "bg1.jpg"
    bg_jpg.parent.mkdir(parents=True, exist_ok=True)
    bg_jpg.write_bytes(background)
    util.log(f"login background: {bg_jpg.relative_to(theme_dir)}")

    # Argon 3.x references bg1.webp, older releases use bg1.jpg.
    webp_path = static / "img" / "bg1.webp"
    webp_referenced = webp_path.exists() or _template_mentions(theme_dir, "bg1.webp")
    if webp_referenced:
        webp = images.jpeg_to_webp(background)
        if webp:
            webp_path.write_bytes(webp)
            util.log(f"login background: {webp_path.relative_to(theme_dir)}")
        else:
            util.warn("Pillow cannot write WebP; falling back to bg1.jpg in templates")
            _replace_references(theme_dir, "bg1.webp", "bg1.jpg")

    # Keep the file name referenced by every Argon template, but render the
    # ZeroWrt logo inside it.
    logo_svg = static / "img" / "argon.svg"
    images.svg_wrapper(logo, logo_svg)
    util.log(f"login logo: {logo_svg.relative_to(theme_dir)}")

    ico = images.png_to_ico(logo)
    (static / "favicon.ico").write_bytes(ico)

    icon_sizes = {
        "favicon-16x16.png": 16,
        "favicon-32x32.png": 32,
        "favicon-96x96.png": 96,
        "apple-icon-60x60.png": 60,
        "apple-icon-72x72.png": 72,
        "apple-icon-144x144.png": 144,
        "android-icon-192x192.png": 192,
        "ms-icon-144x144.png": 144,
    }
    icon_dir = static / "icon"
    if icon_dir.exists():
        for name, size in icon_sizes.items():
            target = icon_dir / name
            resized = images.resize_png(logo, size)
            if resized:
                target.write_bytes(resized)
            else:
                # Without Pillow, reuse the source PNG and let the browser scale it.
                target.write_bytes(logo)
    util.log("favicons replaced")


def _replace_references(theme_dir: Path, old: str, new: str) -> None:
    """Rewrite template/JS references from one background file to another."""
    for path in Path(theme_dir).rglob("*"):
        if path.suffix not in {".ut", ".htm", ".html", ".js"} or not path.is_file():
            continue
        text = util.read_text(path)
        if old in text:
            util.write_text(path, text.replace(old, new))
            util.log(f"{path.relative_to(theme_dir)}: {old} -> {new}")


def _template_mentions(theme_dir: Path, needle: str) -> bool:
    for pattern in ("**/*.ut", "**/*.htm", "**/*.js"):
        for path in Path(theme_dir).glob(pattern):
            try:
                if needle in util.read_text(path):
                    return True
            except OSError:
                continue
    return False


def patch_argon_config(app_dir: Path) -> None:
    app_dir = Path(app_dir)
    config = app_dir / "root" / "etc" / "config" / "argon"
    if not config.exists():
        util.warn(f"Argon config not found: {config}")
        return

    util.header("Disabling the Argon online wallpaper")
    text = util.read_text(config)
    line = re.compile(r"^[ \t]*option[ \t]+online_wallpaper[ \t]+.*$", re.M)
    if line.search(text):
        text = line.sub("\toption online_wallpaper 'none'", text)
    elif "config global" in text:
        text = text.replace("config global", "config global\n\toption online_wallpaper 'none'", 1)
    else:
        text += "\nconfig global\n\toption online_wallpaper 'none'\n"
    _write_text_if_changed(config, text)
    if "option online_wallpaper 'none'" not in util.read_text(config):
        raise util.BuildError("failed to set online_wallpaper to none")
    util.log(f"patched {config.relative_to(app_dir)}")

    # Fresh installs only; make upgrades from the old Bing switch agree too.
    defaults = app_dir / "root" / "etc" / "uci-defaults" / "luci-argon-config"
    if defaults.exists():
        util.replace_text(
            defaults,
            'uci -q set "argon.@global[0].online_wallpaper"="bing"',
            'uci -q set "argon.@global[0].online_wallpaper"="none"',
        )


def apply_argon_branding(tree: Path, assets_dir: Path) -> None:
    tree = Path(tree)
    theme = tree / "package" / "new" / "luci-theme-argon"
    if not theme.exists():
        raise util.BuildError("Argon theme was not cloned")

    patch_argon_theme(theme, assets_dir)

    app = tree / "package" / "new" / "luci-app-argon-config"
    if app.exists():
        patch_argon_config(app)
    else:
        # Integrated theme: the same config file lives inside the theme.
        util.warn("standalone luci-app-argon-config not present; patching the theme config")
        integrated_config = theme / "root" / "etc" / "config" / "argon"
        if integrated_config.exists():
            patch_argon_config(theme)
