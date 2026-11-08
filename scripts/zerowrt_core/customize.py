"""In-tree firmware customisation.

Every change is anchored on a named upstream line and verified afterwards.  A
silently missed replacement is how a firmware ships with the wrong LAN address,
an open WiFi network or the upstream ImmortalWrt banner.
"""

from __future__ import annotations

import base64
import io
import re
import shutil
from pathlib import Path

from . import state, util
from .settings import BuildSettings

VERSION_MK = Path("include/version.mk")
CONFIG_GENERATE = Path("package/base-files/files/bin/config_generate")
OPENWRT_RELEASE = Path("package/base-files/files/etc/openwrt_release")
OS_RELEASE = Path("package/base-files/files/usr/lib/os-release")
BANNER = Path("package/base-files/files/etc/banner")
SHADOW = Path("package/base-files/files/etc/shadow")
MTWIFI = Path("package/mtk/applications/mtwifi-cfg/files/mtwifi.sh")
ARGON_THEME = Path("package/new/luci-theme-argon")

VERSION_DIST_RE = re.compile(
    r"^(VERSION_DIST:=\$\(if \$\(VERSION_DIST\),\$\(VERSION_DIST\),)([^)\n]+)(\))$",
    re.M,
)
VERSION_MANUFACTURER_RE = re.compile(
    r"^(VERSION_MANUFACTURER:=\$\(if \$\(VERSION_MANUFACTURER\),\$\(VERSION_MANUFACTURER\),)([^)\n]+)(\))$",
    re.M,
)
HOSTNAME_RE = re.compile(r"hostname='(?:LEDE|OpenWrt|ImmortalWrt|ZeroWrt)'")


def _tree(tree: Path) -> Path:
    return Path(tree)


def _require(path: Path) -> None:
    if not path.exists():
        raise util.BuildError(f"missing {path}; the source tree layout changed")


def remove_vendor_overrides(tree: Path) -> None:
    """Delete ``files/etc`` so it cannot override our banner/config_generate."""
    tree = _tree(tree)
    override = tree / "files" / "etc"
    if override.exists():
        util.remove_path(override)
        util.log("removed files/etc (vendor overrides)")
    files_dir = tree / "files"
    if files_dir.is_dir() and not any(files_dir.iterdir()):
        files_dir.rmdir()


def patch_version_mk(tree: Path, *, dist: str) -> None:
    tree = _tree(tree)
    path = tree / VERSION_MK
    _require(path)
    util.header("Patching include/version.mk")

    text = util.read_text(path)
    text, dist_count = VERSION_DIST_RE.subn(rf"\g<1>{dist}\g<3>", text)
    text, manufacturer_count = VERSION_MANUFACTURER_RE.subn(rf"\g<1>{dist}\g<3>", text)
    if dist_count != 1:
        raise util.BuildError(f"{VERSION_MK}: VERSION_DIST default was not found")
    if manufacturer_count != 1:
        raise util.BuildError(f"{VERSION_MK}: VERSION_MANUFACTURER default was not found")
    util.write_text(path, text)
    util.log(f"VERSION_DIST/VERSION_MANUFACTURER -> {dist}")


def patch_release_files(tree: Path, *, dist: str, version: str) -> None:
    tree = _tree(tree)
    release = tree / OPENWRT_RELEASE
    os_release = tree / OS_RELEASE
    _require(release)
    _require(os_release)
    util.header("Patching release strings")

    text = util.read_text(release)
    text, description = re.subn(
        r"^DISTRIB_DESCRIPTION='[^']*'$",
        f"DISTRIB_DESCRIPTION='{dist}-{version}'",
        text,
        flags=re.M,
    )
    text, revision = re.subn(
        r"^DISTRIB_REVISION='[^']*'$",
        "DISTRIB_REVISION=' By MinimaxFlora'",
        text,
        flags=re.M,
    )
    if description != 1 or revision != 1:
        raise util.BuildError(f"{OPENWRT_RELEASE}: DISTRIB_DESCRIPTION/REVISION lines were not found")
    util.write_text(release, text)

    release_line = f'OPENWRT_RELEASE="{dist} 标准版 @R{version} BY MinimaxFlora"'
    text = util.read_text(os_release)
    text, count = re.subn(r"^OPENWRT_RELEASE=.*$", release_line, text, flags=re.M)
    if count != 1:
        raise util.BuildError(f"{OS_RELEASE}: OPENWRT_RELEASE line was not found")
    util.write_text(os_release, text)
    util.log(f"release strings -> {dist}-{version}")


def patch_config_generate(tree: Path, *, hostname: str, ip: str) -> None:
    """Set the hostname and unify both upstream LAN defaults.

    The upstream file has two LAN branches: Ruijie boards get
    ``192.168.110.1`` and every other board gets ``192.168.6.1``.  ZeroWrt uses
    one configurable address for every device, default ``10.0.0.1``; both
    upstream defaults are replaced, while the non-LAN
    ``192.168.$((addr_offset++)).1`` fallback is left untouched.
    """
    tree = _tree(tree)
    path = tree / CONFIG_GENERATE
    _require(path)
    util.header("Patching config_generate (hostname / LAN IP)")

    text = util.read_text(path)
    text, host_count = HOSTNAME_RE.subn(f"hostname='{hostname}'", text)
    if host_count != 1:
        raise util.BuildError(f"{CONFIG_GENERATE}: default hostname was not found")

    replaced = 0
    for expected in ("192.168.110.1", "192.168.6.1"):
        old = f'ipad=${{ipaddr:-"{expected}"}}'
        new = f'ipad=${{ipaddr:-"{ip}"}}'
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            replaced += count

    new_default = f'ipad=${{ipaddr:-"{ip}"}}'
    if text.count(new_default) < 2:
        raise util.BuildError(f"{CONFIG_GENERATE}: expected the Ruijie and non-Ruijie LAN defaults")

    util.write_text(path, text)
    util.log(f"LAN IP -> {ip} for both LAN defaults ({replaced} replaced)")


def patch_banner(tree: Path, assets: Path) -> None:
    tree = _tree(tree)
    source = Path(assets) / "banner"
    if not source.is_file():
        raise util.BuildError(f"banner asset not found: {source}")
    destination = tree / BANNER
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    util.log(f"login banner: {BANNER}")


def _openssl_hash(password: str) -> str:
    if util.which("openssl") is None:
        raise util.BuildError("openssl is required to generate the root password hash")
    code, output = util.run(
        ["openssl", "passwd", "-5", "-stdin"],
        input_text=password + "\n",
        capture=True,
        quiet=True,
        check=False,
    )
    digest = output.strip().splitlines()[-1] if output.strip() else ""
    if code != 0 or not digest.startswith("$5$"):
        raise util.BuildError("openssl could not generate a SHA-256 crypt password hash")
    return digest


def patch_root_password(tree: Path, password: str) -> None:
    if not password:
        util.log("root password left unchanged")
        return
    tree = _tree(tree)
    path = tree / SHADOW
    _require(path)
    util.header("Setting the default root password")
    digest = _openssl_hash(password)
    text = util.read_text(path)
    text, count = re.subn(r"^root:[^:]*:", f"root:{digest}:", text, count=1, flags=re.M)
    if count != 1:
        raise util.BuildError(f"{SHADOW}: root entry was not found")
    util.write_text(path, text)
    util.log("root password hash written to package/base-files/files/etc/shadow")


def patch_wifi(tree: Path, settings: BuildSettings) -> None:
    tree = _tree(tree)
    path = tree / MTWIFI
    _require(path)
    util.header("Patching default WiFi configuration")

    text = util.read_text(path)
    expected = {band: settings.ssid(band) for band in ("2g", "5g")}
    for label, band in (("2.4G", "2g"), ("5G", "5g")):
        old = f'ssid="ImmortalWrt-{label}"'
        new = f'ssid="{expected[band]}"'
        if new in text:
            continue
        text, count = re.subn(re.escape(old), new, text)
        if count != 1:
            raise util.BuildError(f"{MTWIFI}: default {label} SSID was not found")

    # Quote the SSID passed to UCI so spaces in the configured name cannot
    # split the command.
    text = text.replace(
        "set wireless.default_${dev}.ssid=${ssid}",
        "set wireless.default_${dev}.ssid='${ssid}'",
    )

    encryption_pattern = re.compile(
        r"^(?P<indent>[ \t]*)set wireless\.default_\$\{dev\}\.encryption=none\s*$",
        re.M,
    )

    def add_key(match: re.Match[str]) -> str:
        indent = match.group("indent")
        return (
            f"{indent}set wireless.default_${{dev}}.encryption=psk2\n"
            f"{indent}set wireless.default_${{dev}}.key='{settings.wifi_password}'"
        )

    text, count = encryption_pattern.subn(add_key, text)
    if count == 0:
        # Already patched (or a different layout): replace the key if present,
        # and insert one after the encryption line if it is missing.
        key_pattern = re.compile(r"^(?P<indent>[ \t]*)set wireless\.default_\$\{dev\}\.key=.*$", re.M)
        if key_pattern.search(text):
            text = key_pattern.sub(
                lambda m: f"{m.group('indent')}set wireless.default_${{dev}}.key='{settings.wifi_password}'",
                text,
                count=1,
            )
        elif "set wireless.default_${dev}.encryption=psk2" in text:
            text = text.replace(
                "set wireless.default_${dev}.encryption=psk2",
                "set wireless.default_${dev}.encryption=psk2\n"
                f"\t\t\t\t\tset wireless.default_${{dev}}.key='{settings.wifi_password}'",
                1,
            )
        else:
            raise util.BuildError(f"{MTWIFI}: open default WiFi network was not found")
    util.write_text(path, text)

    final = util.read_text(path)
    for _band, ssid in expected.items():
        if f'ssid="{ssid}"' not in final:
            raise util.BuildError(f"{MTWIFI}: SSID {ssid} was not applied")
    if "encryption=psk2" not in final or f"key='{settings.wifi_password}'" not in final:
        raise util.BuildError(f"{MTWIFI}: WPA2 key was not applied")
    if "ImmortalWrt-" in final:
        raise util.BuildError(f"{MTWIFI}: an upstream SSID is still present")
    util.log(
        f"SSIDs: {expected['2g']} / {expected['5g']}; encryption: psk2; password: {'*' * len(settings.wifi_password)}"
    )


def _set_uci_option(text: str, name: str, value: str) -> str:
    pattern = re.compile(rf"^(?P<indent>[ \t]*)option\s+{re.escape(name)}\s+.*$", re.M)
    replacement = f"\\g<indent>option {name} '{value}'"
    text, count = pattern.subn(replacement, text, count=1)
    if count:
        return text
    text, count = re.subn(
        r"(^config\s+global\s*$)",
        rf"\1\n\toption {name} '{value}'",
        text,
        count=1,
        flags=re.M,
    )
    if count != 1:
        raise util.BuildError("Argon config: 'config global' section was not found")
    return text


def _open_favicon(path: Path):
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - runner installs python3-pil
        raise util.BuildError("Pillow is required to convert assets/favicon.ico") from exc
    if not path.is_file():
        raise util.BuildError(f"favicon asset not found: {path}")
    with Image.open(path) as opened:
        return opened.convert("RGBA")


def _save_png(image, destination: Path, size: int) -> None:
    from PIL import Image

    resampling = getattr(Image, "Resampling", Image).LANCZOS
    destination.parent.mkdir(parents=True, exist_ok=True)
    resized = image.resize((size, size), resampling)
    resized.save(destination, format="PNG", optimize=True)


def _write_argon_svg(image, destination: Path) -> None:
    from PIL import Image

    resampling = getattr(Image, "Resampling", Image).LANCZOS
    buffer = io.BytesIO()
    image.resize((256, 256), resampling).save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" '
        'viewBox="0 0 256 256">\n'
        f'  <image width="256" height="256" href="data:image/png;base64,{encoded}"/>\n'
        "</svg>\n"
    )
    util.write_text(destination, svg)


def patch_argon(tree: Path, assets: Path) -> None:
    tree = _tree(tree)
    theme = tree / ARGON_THEME
    _require(theme / "Makefile")
    htdocs = theme / "htdocs" / "luci-static" / "argon"
    _require(htdocs / "img" / "bg1.webp")
    _require(htdocs / "favicon.ico")
    _require(theme / "root" / "etc" / "config" / "argon")
    util.header("Patching Argon theme (background, logo, icons, light mode)")

    background = Path(assets) / "bg1.webp"
    favicon = Path(assets) / "favicon.ico"
    if not background.is_file() or not favicon.is_file():
        raise util.BuildError("assets/bg1.webp and assets/favicon.ico are required for Argon")
    shutil.copyfile(background, htdocs / "img" / "bg1.webp")
    shutil.copyfile(favicon, htdocs / "favicon.ico")

    image = _open_favicon(favicon)
    for size in (32, 16):
        _save_png(image, htdocs / "icon" / f"favicon-{size}x{size}.png", size)
    _save_png(image, htdocs / "icon" / "android-icon-192x192.png", 192)
    _save_png(image, htdocs / "icon" / "apple-icon-144x144.png", 144)
    _write_argon_svg(image, htdocs / "img" / "argon.svg")

    config = theme / "root" / "etc" / "config" / "argon"
    text = util.read_text(config)
    for name, value in (
        ("mode", "light"),
        ("primary", "#EC4899"),
        ("dark_primary", "#BE185D"),
        ("dark_primary_mode", "custom"),
    ):
        text = _set_uci_option(text, name, value)
    util.write_text(config, text)
    util.log("Argon: bg1.webp / favicon / SVG logo / PNG icons / forced light mode / #EC4899")


def _verify_argon(tree: Path, assets: Path) -> list[str]:
    problems: list[str] = []
    theme = tree / ARGON_THEME
    htdocs = theme / "htdocs" / "luci-static" / "argon"
    checks = {
        "background": htdocs / "img" / "bg1.webp",
        "favicon": htdocs / "favicon.ico",
        "svg logo": htdocs / "img" / "argon.svg",
        "android icon": htdocs / "icon" / "android-icon-192x192.png",
        "apple icon": htdocs / "icon" / "apple-icon-144x144.png",
        "favicon 16": htdocs / "icon" / "favicon-16x16.png",
        "favicon 32": htdocs / "icon" / "favicon-32x32.png",
    }
    for label, path in checks.items():
        if not path.is_file():
            problems.append(f"Argon {label} is missing: {path.relative_to(tree)}")
    if (htdocs / "img" / "bg1.webp").is_file() and (htdocs / "img" / "bg1.webp").read_bytes() != (
        Path(assets) / "bg1.webp"
    ).read_bytes():
        problems.append("Argon background does not match assets/bg1.webp")
    if (htdocs / "favicon.ico").is_file() and (htdocs / "favicon.ico").read_bytes() != (
        Path(assets) / "favicon.ico"
    ).read_bytes():
        problems.append("Argon favicon does not match assets/favicon.ico")
    if (htdocs / "img" / "argon.svg").is_file() and (
        "data:image/png;base64," not in util.read_text(htdocs / "img" / "argon.svg")
    ):
        problems.append("Argon SVG logo was not generated from the favicon")
    config_path = theme / "root" / "etc" / "config" / "argon"
    if config_path.is_file():
        config = util.read_text(config_path)
        for needle in (
            "option mode 'light'",
            "option primary '#EC4899'",
            "option dark_primary '#BE185D'",
            "option dark_primary_mode 'custom'",
        ):
            if needle not in config:
                problems.append(f"Argon config is missing {needle!r}")
    return problems


def apply(
    tree: Path,
    settings: BuildSettings,
    *,
    assets: Path,
    repo_root: Path,
) -> None:
    """Apply every requested firmware customisation."""
    tree = _tree(tree)
    info = state.read(tree)
    build_date = state.build_date(info)
    if build_date <= 0:
        raise util.BuildError("build date is missing; run 'source clone' before customising")
    version = str(info.get("version") or state.version_for(build_date))
    profile = settings.profile()

    remove_vendor_overrides(tree)
    patch_version_mk(tree, dist=settings.dist_name)
    patch_release_files(tree, dist=settings.dist_name, version=version)
    patch_config_generate(
        tree,
        hostname=settings.dist_name,
        ip=settings.effective_ip(),
    )
    patch_banner(tree, assets)
    patch_root_password(tree, settings.root_password)
    patch_wifi(tree, settings)
    patch_argon(tree, assets)
    verify(tree, settings, assets=assets)
    util.log(f"customisations applied for {profile.name} ({profile.target}, LAN {settings.effective_ip()})")


def verify(tree: Path, settings: BuildSettings, *, assets: Path) -> None:
    tree = _tree(tree)
    util.header("Verifying customisations")
    problems: list[str] = []
    version = str(state.read(tree).get("version") or "")
    if not version:
        problems.append("build version is missing from .zerowrt-info.json")

    version_text = util.read_text(tree / VERSION_MK)
    if f"VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),{settings.dist_name})" not in version_text:
        problems.append("VERSION_DIST default is wrong")
    manufacturer = f"VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),{settings.dist_name})"
    if manufacturer not in version_text:
        problems.append("VERSION_MANUFACTURER default is wrong")

    release = util.read_text(tree / OPENWRT_RELEASE)
    if f"DISTRIB_DESCRIPTION='{settings.dist_name}-{version}'" not in release:
        problems.append("DISTRIB_DESCRIPTION is wrong")
    if "DISTRIB_REVISION=' By MinimaxFlora'" not in release:
        problems.append("DISTRIB_REVISION is wrong")
    expected_release = f'OPENWRT_RELEASE="{settings.dist_name} 标准版 @R{version} BY MinimaxFlora"'
    if expected_release not in util.read_text(tree / OS_RELEASE):
        problems.append("OPENWRT_RELEASE is wrong")

    generate = util.read_text(tree / CONFIG_GENERATE)
    expected_ip = settings.effective_ip()
    if generate.count(f'ipad=${{ipaddr:-"{expected_ip}"}}') < 2:
        problems.append(f"config_generate does not use {expected_ip} for both LAN defaults")
    for old in ("192.168.110.1", "192.168.6.1"):
        if old != expected_ip and old in generate:
            problems.append(f"config_generate still contains the old default {old}")
    if f"hostname='{settings.dist_name}'" not in generate:
        problems.append("config_generate hostname is wrong")

    if (tree / "files" / "etc").exists():
        problems.append("files/etc still exists and can override the base files")

    banner = tree / BANNER
    if not banner.exists() or banner.read_bytes() != (Path(assets) / "banner").read_bytes():
        problems.append("login banner does not match assets/banner")

    if settings.root_password:
        shadow = util.read_text(tree / SHADOW)
        if not re.search(r"^root:\$5\$", shadow, re.M):
            problems.append("root password hash is not SHA-256 crypt")

    wifi = util.read_text(tree / MTWIFI)
    for band in ("2g", "5g"):
        if f'ssid="{settings.ssid(band)}"' not in wifi:
            problems.append(f"WiFi SSID {settings.ssid(band)} is missing")
    if "encryption=psk2" not in wifi:
        problems.append("WiFi encryption is not WPA2")
    if f"key='{settings.wifi_password}'" not in wifi:
        problems.append("WiFi key is missing")

    problems.extend(_verify_argon(tree, assets))

    if problems:
        raise util.BuildError("customisation failed:\n  - " + "\n  - ".join(problems))
    util.log("customisations verified")
