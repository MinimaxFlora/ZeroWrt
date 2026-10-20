"""Unit tests for the ZeroWrt build helpers.

Run with:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from zerowrt_core import build, configgen, images, packages, source, util  # noqa: E402


class TempTreeTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, relative: str, content: str | bytes) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path


class CorePatchesTest(TempTreeTest):
    VERSION_MK = """\
VERSION_DIST:=$(call qstrip,$(CONFIG_VERSION_DIST))
VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),OpenWrt)
VERSION_MANUFACTURER:=$(call qstrip,$(CONFIG_VERSION_MANUFACTURER))
VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),OpenWrt)
"""

    CONFIG_GENERATE = """\
generate_static_system() {
\tset system.@system[-1].hostname='LEDE'
}
generate_network() {
\tcase "$protocol" in
\t\tstatic)
\t\t\tcase "$1" in
\t\t\t\tlan) ipad=${ipaddr:-"192.168.1.1"} ;;
\t\t\t\t*) ipad=${ipaddr:-"192.168.$((addr_offset++)).1"} ;;
\t\t\tesac
\t\t;;
\tesac
}
"""

    DEFAULT_SETTINGS = """\
sed -i '/DISTRIB_DESCRIPTION/d' /etc/openwrt_release
echo "DISTRIB_DESCRIPTION='LEDE '" >> /etc/openwrt_release
sed -i -e '/OPENWRT_RELEASE/d' /usr/lib/os-release
echo 'OPENWRT_RELEASE="LEDE R@BUILD_DATE@"' >> /usr/lib/os-release
"""

    TARGET_MK = """\
DEFAULT_PACKAGES.router:=\\
\tluci-app-arpbind luci-app-ssr-plus luci-app-vlmcsd \\
\tluci-app-wol curl
"""

    WIFI_SCRIPT = """\
mac80211_emit_detect() {
\tlocal dev="$1"
\tlocal band="$3"
\tlocal ssid="$default_ssid"

\t[ -n "$ssid" ] || ssid="LEDE"

\tuci -q batch <<-EOF
\t\tset wireless.${iface}.ssid='${ssid}'
\tEOF
}
"""

    def prepare(self) -> Path:
        self.write("include/version.mk", self.VERSION_MK)
        self.write("package/base-files/files/bin/config_generate", self.CONFIG_GENERATE)
        self.write("package/base-files/luci/bin/config_generate", self.CONFIG_GENERATE)
        self.write("package/lean/default-settings/files/zzz-default-settings", self.DEFAULT_SETTINGS)
        self.write("include/target.mk", self.TARGET_MK)
        self.write("package/lean/luci-app-ssr-plus/Makefile", "include $(TOPDIR)/rules.mk\n")
        self.write("package/kernel/mac80211/files/lib/wifi/mac80211.sh", self.WIFI_SCRIPT)
        return self.root

    def test_core_customisations(self) -> None:
        tree = self.prepare()
        source.apply_core_customisations(tree)

        version = util.read_text(tree / "include/version.mk")
        self.assertIn("VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),ZeroWrt)", version)
        self.assertIn("VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),ZeroWrt)", version)

        for relative in source.CORE_FILES.values():
            if relative.name == "config_generate":
                text = util.read_text(tree / relative)
                self.assertIn('lan) ipad=${ipaddr:-"10.0.0.1"}', text)
                self.assertIn("hostname='ZeroWrt'", text)
                self.assertNotIn("192.168.1.1", text)

        settings = util.read_text(tree / source.CORE_FILES["default_settings"])
        self.assertIn("DISTRIB_DESCRIPTION='ZeroWrt '", settings)
        self.assertIn('OPENWRT_RELEASE="ZeroWrt R@BUILD_DATE@"', settings)
        self.assertNotIn("LEDE", settings)

        target_mk = util.read_text(tree / "include/target.mk")
        self.assertIn("luci-app-ssr-plus", target_mk)
        self.assertIn("luci-app-arpbind", target_mk)
        self.assertTrue((tree / "package/lean/luci-app-ssr-plus").exists())

        wifi = util.read_text(tree / source.WIFI_SCRIPTS[0])
        self.assertIn('2g) ssid="ZeroWrt-2.4G"', wifi)
        self.assertIn('5g) ssid="ZeroWrt-5G"', wifi)
        self.assertNotIn('ssid="LEDE"', wifi)


class DeviceDetectionTest(TempTreeTest):
    def prepare(self) -> Path:
        self.write("target/linux/mediatek/Makefile", "SUBTARGETS:=filogic mt7622\nKERNEL_PATCHVER:=6.12\n")
        self.write("target/linux/mediatek/filogic/target.mk", "DEFAULT_PACKAGES += kmod-mt7986-firmware\n")
        self.write("target/linux/mediatek/mt7622/target.mk", "# other subtarget\n")
        self.write(
            "target/linux/mediatek/image/filogic.mk",
            """\
define Device/ruijie_rg-x60
  DEVICE_VENDOR := Ruijie
  DEVICE_MODEL := RG-X60
  DEVICE_DTS := mt7986a-ruijie-rg-x60
endef
TARGET_DEVICES += ruijie_rg-x60

define Device/ruijie_rg-x60-pro
  DEVICE_VENDOR := Ruijie
  DEVICE_MODEL := RG-X60 Pro
  DEVICE_DTS := mt7986a-ruijie-rg-x60-pro
endef
TARGET_DEVICES += ruijie_rg-x60-pro

define Device/other_vendor
  DEVICE_MODEL := Something
endef
""",
        )
        return self.root

    def test_prefers_non_pro_device(self) -> None:
        device = configgen.detect_device(self.prepare())
        self.assertEqual(device["name"], "ruijie_rg-x60")
        self.assertEqual(device["board"], "mediatek")
        self.assertEqual(device["subtarget"], "filogic")

    def test_hint_selects_pro(self) -> None:
        device = configgen.detect_device(self.prepare(), hint="ruijie_rg-x60-pro")
        self.assertEqual(device["name"], "ruijie_rg-x60-pro")

    def test_missing_device_raises(self) -> None:
        self.write("target/linux/mediatek/Makefile", "SUBTARGETS:=filogic\n")
        self.write("target/linux/mediatek/filogic/target.mk", "")
        self.write("target/linux/mediatek/image/filogic.mk", "define Device/x\n  DEVICE_MODEL := Y\nendef\n")
        with self.assertRaises(util.BuildError):
            configgen.detect_device(self.root)


class ConfigRenderTest(TempTreeTest):
    def test_target_lines_and_ssr_removal(self) -> None:
        text = configgen._render_config(
            {"board": "mediatek", "subtarget": "filogic", "name": "ruijie_rg-x60"},
            {
                "CONFIG_PACKAGE_luci-app-filetransfer": "y",
            },
        )
        self.assertIn("CONFIG_TARGET_mediatek=y", text)
        self.assertIn("CONFIG_TARGET_mediatek_filogic=y", text)
        self.assertIn("CONFIG_TARGET_mediatek_filogic_DEVICE_ruijie_rg-x60=y", text)
        self.assertIn("CONFIG_PACKAGE_luci-app-filetransfer=y", text)
        self.assertNotIn("=y=y", text)
        self.assertNotIn("luci-compat", text)
        self.assertNotIn("CONFIG_VERSION_DIST", text)
        self.assertLess(text.index("CONFIG_TARGET_mediatek=y"), text.index("CONFIG_PACKAGE_"))

    def test_defaults_when_no_overrides(self) -> None:
        text = configgen._render_config(
            {"board": "mediatek", "subtarget": "filogic", "name": "ruijie_rg-x60"}, {}
        )
        for package in (
            "luci-theme-argon",
            "luci-app-argon-config",
            "luci-app-passwall",
            "luci-app-openclash",
            "luci-app-ssr-plus",
        ):
            self.assertIn(f"CONFIG_PACKAGE_{package}=y", text)

    def test_overrides_from_file(self) -> None:
        config = self.write("zerowrt.config", "# comment\nCONFIG_PACKAGE_foo=y\nbad line\n")
        overrides = configgen.parse_overrides(config)
        self.assertEqual(overrides, {"CONFIG_PACKAGE_foo": "y"})

    def test_pinned_target_is_used(self) -> None:
        overrides = {
            "CONFIG_TARGET_mediatek": "y",
            "CONFIG_TARGET_mediatek_filogic": "y",
            "CONFIG_TARGET_mediatek_filogic_DEVICE_ruijie_rg-x60-pro": "y",
        }
        target = configgen._target_from_overrides(overrides)
        self.assertIsNotNone(target)
        self.assertEqual(target["board"], "mediatek")
        self.assertEqual(target["subtarget"], "filogic")
        self.assertEqual(target["name"], "ruijie_rg-x60-pro")


class CollectTest(TempTreeTest):
    def test_collect_renames_firmware(self) -> None:
        self.write(
            ".zerowrt-info.json",
            '{"board": "mediatek", "subtarget": "filogic", '
            '"device": "ruijie_rg-x60-pro", "version": "24.10.5"}\n',
        )
        source_dir = self.root / "bin/targets/mediatek/filogic"
        source_dir.mkdir(parents=True)
        firmware = "zerowrt-24.10.5-mediatek-filogic-ruijie_rg-x60-pro-squashfs-sysupgrade.bin"
        (source_dir / firmware).write_bytes(b"firmware")
        (source_dir / "zerowrt-24.10.5-mediatek-filogic-ruijie_rg-x60-pro.manifest").write_text("{}")
        (source_dir / "config.buildinfo").write_text("CONFIG_X=y\n")

        out = self.root / "dist"
        build.collect(self.root, out)
        names = {path.name for path in out.iterdir()}
        self.assertIn("ZeroWrt-24.10.5-ruijie_rg-x60-pro-squashfs-sysupgrade.bin", names)
        self.assertIn("SHA256SUMS", names)
        self.assertIn("BUILD_INFO.txt", names)
        self.assertIn("config.buildinfo", names)


class ImageTest(unittest.TestCase):
    def test_png_size_and_ico(self) -> None:
        logo = (REPO_ROOT / "assets" / "logo.png").read_bytes()
        self.assertEqual(images.png_size(logo), (64, 64))
        ico = images.png_to_ico(logo)
        self.assertEqual(ico[:4], b"\x00\x00\x01\x00")
        self.assertGreater(len(ico), len(logo))

    def test_svg_wrapper(self) -> None:
        logo = (REPO_ROOT / "assets" / "logo.png").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "argon.svg"
            images.svg_wrapper(logo, target)
            text = target.read_text(encoding="utf-8")
            self.assertIn('viewBox="0 0 64 64"', text)
            self.assertIn("data:image/png;base64,", text)


class ArgonBrandingTest(TempTreeTest):
    def test_theme_and_config_patches(self) -> None:
        static = self.root / "package/new/luci-theme-argon/htdocs/luci-static/argon"
        (static / "img").mkdir(parents=True)
        (static / "icon").mkdir(parents=True)
        (static / "img" / "bg1.jpg").write_bytes(b"old-background")
        (static / "img" / "argon.svg").write_bytes(b"old-logo")
        (static / "favicon.ico").write_bytes(b"old-icon")
        (static / "icon" / "favicon-16x16.png").write_bytes(b"old")

        app = self.root / "package/new/luci-app-argon-config"
        config = app / "root/etc/config/argon"
        config.parent.mkdir(parents=True)
        config.write_text(
            "config global\n\toption login_style 'classic'\n\toption online_wallpaper 'bing'\n",
            encoding="utf-8",
        )
        defaults = app / "root/etc/uci-defaults/luci-argon-config"
        defaults.parent.mkdir(parents=True)
        defaults.write_text(
            'uci -q set "argon.@global[0].online_wallpaper"="bing"\n', encoding="utf-8"
        )

        packages.patch_argon_theme(self.root / "package/new/luci-theme-argon", REPO_ROOT / "assets")
        packages.patch_argon_config(app)

        expected_bg = (REPO_ROOT / "assets" / "background.jpg").read_bytes()
        self.assertEqual((static / "img" / "bg1.jpg").read_bytes(), expected_bg)
        self.assertIn("data:image/png;base64,", (static / "img" / "argon.svg").read_text())
        self.assertEqual((static / "favicon.ico").read_bytes()[:4], b"\x00\x00\x01\x00")
        self.assertEqual(images.png_size((static / "icon" / "favicon-16x16.png").read_bytes()), (16, 16))

        text = config.read_text(encoding="utf-8")
        self.assertIn("option online_wallpaper 'none'", text)
        self.assertNotIn("'bing'", text)
        self.assertIn('"none"', defaults.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
