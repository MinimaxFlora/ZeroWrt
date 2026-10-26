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
from datetime import datetime
from pathlib import Path

from . import images, util

ARGON_THEME_REPO = "jerrykuku/luci-theme-argon"
ARGON_THEME_REF = "master"
ARGON_CONFIG_REPO = "jerrykuku/luci-app-argon-config"
ARGON_CONFIG_REF = "master"
# One repository carries the PassWall toolchain, its two LuCI front ends and
# OpenClash, so a build only needs a single checkout and upstream breakage can
# be fixed in one place.
HELLOWORLD_REPO = "MinimaxFlora/openwrt_helloworld"
HELLOWORLD_REF = "main"
# Same idea as helloworld: one repository carries mosdns itself, its LuCI
# front end and geo2txt, so nothing has to come from the feeds.
MOSDNS_REPO = "sbwml/luci-app-mosdns"
MOSDNS_REF = "v5"
RAMFREE_REPO = "sbwml/luci-app-ramfree"
RAMFREE_REF = "main"

PACKAGE_DIR_NAMES = {
    # Argon theme and the standalone settings app.
    "luci-theme-argon",
    "luci-app-argon-config",
    # helloworld: the two LuCI front ends and the cores they pull in.
    "luci-app-passwall",
    "luci-app-passwall2",
    "luci-app-openclash",
    "xray-core",
    "xray-plugin",
    "v2ray-plugin",
    # helloworld/v2ray-geodata builds these two; the feeds ship the same names
    # from a directory called net/v2ray-geodata, so all three are listed.
    "v2ray-geodata",
    "v2ray-geoip",
    "v2ray-geosite",
    "sing-box",
    "chinadns-ng",
    "dns2socks",
    "geoview",
    "hysteria",
    "ipt2socks",
    "microsocks",
    "naiveproxy",
    "shadow-tls",
    "shadowsocks-rust",
    "shadowsocksr-libev",
    "simple-obfs",
    "simple-obfs-client",
    "simple-obfs-server",
    "tcping",
    # sbwml/luci-app-mosdns carries the daemon, the LuCI app and geo2txt.
    "mosdns",
    "luci-app-mosdns",
    "geo2txt",
    "luci-app-ramfree",
}

BUILD_PACKAGE_RE = re.compile(r"call BuildPackage,([^)\n]+)\)")
PKG_NAME_RE = re.compile(r"^PKG_NAME\s*:?=\s*(\S+)", re.M)


def declared_package_names(directory: Path) -> set[str]:
    """Names a package directory registers with the buildroot.

    OpenWrt normally takes the package name from the directory, but a single
    Makefile can build several packages: helloworld's ``v2ray-geodata``
    directory registers ``v2ray-geoip`` and ``v2ray-geosite``, while the feeds
    ship the very same names from a directory called ``net/v2ray-geodata``.
    LuCI apps go the other way and write ``BuildPackage,$(PKG_NAME)``, which
    only resolves after reading ``PKG_NAME`` from the same Makefile.
    Comparing directory names alone therefore misses real conflicts.
    """
    makefile = Path(directory) / "Makefile"
    if not makefile.is_file():
        return set()

    text = util.read_text(makefile)
    match = PKG_NAME_RE.search(text)
    pkg_name = match.group(1) if match else ""

    names: set[str] = set()
    for raw in BUILD_PACKAGE_RE.findall(text):
        name = raw.replace("$(PKG_NAME)", pkg_name).strip()
        if not name or "$" in name:
            # Generated names such as shadowsocks-rust-$(component): the
            # directory name already covers those packages.
            continue
        names.add(name)
    if pkg_name:
        names.add(pkg_name)
    return names


def new_package_names(tree: Path) -> set[str]:
    """Every package name owned by package/new.

    The static list covers what is cloned; when package/new already exists the
    checkouts are scanned too, so adding a repository without updating this
    file cannot silently leave a duplicate in the feeds.
    """
    names = set(PACKAGE_DIR_NAMES)
    new_dir = Path(tree) / "package" / "new"
    if not new_dir.is_dir():
        return names

    for root, dirs, _files in os.walk(new_dir, topdown=True, followlinks=False):
        for name in dirs:
            candidate = Path(root) / name
            names |= declared_package_names(candidate)
    return names


def _env(name: str, default: str) -> str:
    return (os.environ.get(name) or default).strip()


def remove_existing_package_dirs(tree: Path) -> None:
    """Drop any copy of the packages we replace (feeds, package/lean, ...)."""
    tree = Path(tree)
    owned = new_package_names(tree)
    package_root = tree / "package"
    if not package_root.exists():
        return
    for root, dirs, _files in os.walk(package_root, topdown=True, followlinks=False):
        if Path(root).is_relative_to(tree / "package" / "new"):
            dirs[:] = []
            continue
        keep = []
        for name in dirs:
            candidate = Path(root) / name
            if (candidate / "Makefile").is_file() and (
                candidate.name in owned or declared_package_names(candidate) & owned
            ):
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
        util.log(
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

    helloworld_dir = new_dir / "helloworld"
    _clone(
        _env("HELLOWORLD_REPO", HELLOWORLD_REPO),
        _env("HELLOWORLD_REF", HELLOWORLD_REF),
        helloworld_dir,
    )
    _fix_openclash(helloworld_dir)

    # These two sit next to helloworld: one repository per checkout directly
    # under package/new, so the layout is the same everywhere.
    ramfree_dir = new_dir / "luci-app-ramfree"
    _clone(_env("RAMFREE_REPO", RAMFREE_REPO), _env("RAMFREE_REF", RAMFREE_REF), ramfree_dir)
    if not (ramfree_dir / "Makefile").exists():
        raise util.BuildError(f"ramfree checkout is missing a Makefile: {ramfree_dir}")

    mosdns_dir = new_dir / "luci-app-mosdns"
    _clone(_env("MOSDNS_REPO", MOSDNS_REPO), _env("MOSDNS_REF", MOSDNS_REF), mosdns_dir)

    _validate_layout(new_dir)


def _fix_openclash(helloworld_dir: Path) -> None:
    """OpenClash calls po2lmo from the luci-base host build without declaring
    the dependency. Add it so a clean parallel build cannot race."""
    makefile = Path(helloworld_dir) / "luci-app-openclash" / "Makefile"
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
        "package/new/helloworld/luci-app-passwall/Makefile": (
            new_dir / "helloworld" / "luci-app-passwall" / "Makefile"
        ),
        # The PassWall core is Xray; the Sing-Box package is not selected.
        "package/new/helloworld/xray-core/Makefile": (new_dir / "helloworld" / "xray-core" / "Makefile"),
        "package/new/helloworld/v2ray-geodata/Makefile": (new_dir / "helloworld" / "v2ray-geodata" / "Makefile"),
        "package/new/helloworld/luci-app-openclash/Makefile": (
            new_dir / "helloworld" / "luci-app-openclash" / "Makefile"
        ),
        "package/new/luci-app-ramfree/Makefile": (new_dir / "luci-app-ramfree" / "Makefile"),
        "package/new/luci-app-mosdns/mosdns/Makefile": (new_dir / "luci-app-mosdns" / "mosdns" / "Makefile"),
        "package/new/luci-app-mosdns/luci-app-mosdns/Makefile": (
            new_dir / "luci-app-mosdns" / "luci-app-mosdns" / "Makefile"
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
    util.log("theme favicons replaced")

    # One token per run: it changes the icon URLs, so a cached favicon from a
    # previous build can never win over the current one.
    token = datetime.now().strftime("%Y%m%d%H%M%S")
    _patch_branding_cache(theme_dir, icon_dir, logo, token)
    _patch_argon_footer(theme_dir)


def _patch_branding_cache(theme_dir: Path, icon_dir: Path, logo: bytes, token: str) -> None:
    """Point Argon at the ZeroWrt favicon and bust the browser cache.

    ``token`` differs for every build and is appended to the icon URLs. A
    plain filename would let a browser keep serving the favicon it cached
    from an earlier firmware, which is exactly what happens on the Argon
    branding settings page (it renders a plain ``<img>`` element).
    """
    theme_dir = Path(theme_dir)
    if icon_dir.exists():
        resized = images.resize_png(logo, 32)
        (icon_dir / "favicon-zerowrt.png").write_bytes(resized or logo)

    branding = theme_dir / "htdocs" / "luci-static" / "resources" / "argon" / "branding.js"
    if branding.exists():
        text = util.read_text(branding)
        old = "L.resource('../argon/icon/favicon-32x32.png')"
        # L.resource() only whitelists path characters and silently drops an
        # argument that contains a query string, so the token is appended here.
        new = f"L.resource('../argon/icon/favicon-zerowrt.png') + '?v={token}'"
        if old in text:
            util.write_text(branding, text.replace(old, new))
            util.log("Argon branding UI uses the ZeroWrt favicon")
        else:
            util.warn("Argon branding.js default favicon reference not found")

    head_meta = theme_dir / "ucode" / "template" / "themes" / "argon" / "head_meta.ut"
    if head_meta.exists():
        text = util.read_text(head_meta)
        for name in (
            "favicon.ico",
            "icon/favicon-16x16.png",
            "icon/favicon-32x32.png",
            "icon/android-icon-192x192.png",
            "icon/apple-icon-144x144.png",
        ):
            old = "{{ media }}/" + name + '"'
            new = "{{ media }}/" + name + f'?v={token}"'
            text = text.replace(old, new)
        util.write_text(head_meta, text)
        util.log(f"browser icon links are cache-busted ({token})")

    # The login logo is rewritten on every build as well.
    logo_svg = theme_dir / "htdocs" / "luci-static" / "argon" / "img" / "argon.svg"
    for template in ("header_login.ut", "login_background.ut", "head_meta.ut"):
        path = theme_dir / "ucode" / "template" / "themes" / "argon" / template
        if not path.exists():
            continue
        text = util.read_text(path)
        if logo_svg.name not in text:
            continue
        updated = re.sub(r"(argon\.svg)(?!\?v=)", rf"\1?v={token}", text)
        if updated != text:
            util.write_text(path, updated)
            util.log(f"{template}: login logo cache-busted")


def _patch_argon_footer(theme_dir: Path) -> None:
    """Drop the empty revision suffix from the firmware string in both footers.

    The admin pages use template interpolation (``footer.ut``) while the login
    page uses a ucode block (``footer_login.ut``); both render
    "<dist> <version>-<revision>" and the revision is empty for ZeroWrt, which
    left a trailing dash.
    """
    templates = Path(theme_dir) / "ucode" / "template" / "themes" / "argon"
    replacements = {
        "footer.ut": (
            "{{ version.distname }} {{ version.distversion }}-{{ version.distrevision }}",
            "{{ version.distname }} {{ version.distversion }}",
        ),
        "footer_login.ut": (
            "version.distname + ' ' + version.distversion + '-' + version.distrevision",
            "version.distname + ' ' + version.distversion",
        ),
    }

    patched = []
    for name, (old, new) in replacements.items():
        path = templates / name
        if not path.exists():
            continue
        text = util.read_text(path)
        if old not in text:
            util.warn(f"Argon {name}: version expression not found, left unchanged")
            continue
        util.write_text(path, text.replace(old, new))
        patched.append(name)

    if patched:
        util.log("footer firmware string uses ZeroWrt <date>: " + ", ".join(patched))


def patch_root_favicon(tree: Path, assets_dir: Path) -> None:
    """Install the same icon at /www/favicon.ico for browser root requests."""
    logo = (Path(assets_dir) / "logo.png").read_bytes()
    path = Path(tree) / "package" / "base-files" / "files" / "www" / "favicon.ico"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(images.png_to_ico(logo))
    util.log("installed /www/favicon.ico")


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


ARGON_OPTIONS = {
    "online_wallpaper": "none",
    "mode": "light",
    "primary": "#2E9D72",
    "dark_primary": "#4CAF86",
    "dark_primary_mode": "custom",
}


def _set_option(text: str, name: str, value: str) -> str:
    pattern = re.compile(rf"^[ \t]*option[ \t]+{name}[ \t]+.*$", re.M)
    line = f"\toption {name} '{value}'"
    if pattern.search(text):
        return pattern.sub(line, text, count=1)
    if "config global" in text:
        return text.replace("config global", f"config global\n{line}", 1)
    return text + f"\nconfig global\n{line}\n"


def patch_argon_config(app_dir: Path) -> None:
    app_dir = Path(app_dir)
    config = app_dir / "root" / "etc" / "config" / "argon"
    if not config.exists():
        util.warn(f"Argon config not found: {config}")
        return

    util.header("Configuring Argon theme")
    text = util.read_text(config)
    for name, value in ARGON_OPTIONS.items():
        text = _set_option(text, name, value)
    _write_text_if_changed(config, text)

    final = util.read_text(config)
    missing = [name for name, value in ARGON_OPTIONS.items() if f"option {name} '{value}'" not in final]
    if missing:
        raise util.BuildError(f"failed to set Argon options: {', '.join(missing)}")
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
    patch_root_favicon(tree, assets_dir)

    app = tree / "package" / "new" / "luci-app-argon-config"
    if app.exists():
        patch_argon_config(app)
    else:
        # Integrated theme: the same config file lives inside the theme.
        util.log("patching the Argon config bundled with the theme")
        integrated_config = theme / "root" / "etc" / "config" / "argon"
        if integrated_config.exists():
            patch_argon_config(theme)
