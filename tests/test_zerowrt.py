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

from zerowrt_core import build, configgen, images, packages, settings, source, util  # noqa: E402


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


class SettingsTest(unittest.TestCase):
    def test_defaults_are_valid(self) -> None:
        value = settings.BuildSettings().validated()
        self.assertEqual(value.ip, "10.0.0.1")
        self.assertEqual(value.device, "ruijie_rg-x60-new")
        self.assertEqual(value.wifi_password, "1234567890")
        self.assertEqual(value.ssid("2g"), "ZeroWrt-2.4G")
        self.assertEqual(value.ssid("5g"), "ZeroWrt-5G")

    def test_custom_names(self) -> None:
        value = settings.BuildSettings(wifi_name="MyNet").validated()
        self.assertEqual(value.ssid("2g"), "MyNet-2.4G")
        self.assertEqual(value.ssid("6g"), "MyNet-6G")

    def test_invalid_ip(self) -> None:
        with self.assertRaises(util.BuildError):
            settings.BuildSettings(ip="10.0.0.999").validated()

    def test_short_password(self) -> None:
        with self.assertRaises(util.BuildError):
            settings.BuildSettings(wifi_password="short").validated()

    def test_environment_override(self) -> None:
        value = settings.BuildSettings.from_environment(
            {
                "ZEROWRT_IP": "192.168.8.1",
                "ZEROWRT_WIFI_NAME": "Lab",
                "ZEROWRT_WIFI_PASSWORD": "password123",
                "ZEROWRT_DEVICE": "ruijie_rg-x60-pro",
            }
        )
        self.assertEqual(value.ip, "192.168.8.1")
        self.assertEqual(value.ssid("5g"), "Lab-5G")
        self.assertEqual(value.device, "ruijie_rg-x60-pro")


class CorePatchesTest(TempTreeTest):
    VERSION_MK = """\
VERSION_DIST:=$(call qstrip,$(CONFIG_VERSION_DIST))
VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),OpenWrt)
VERSION_MANUFACTURER:=$(call qstrip,$(CONFIG_VERSION_MANUFACTURER))
VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),OpenWrt)
VERSION_NUMBER:=$(call qstrip,$(CONFIG_VERSION_NUMBER))
VERSION_NUMBER:=$(if $(VERSION_NUMBER),$(VERSION_NUMBER),24.10.5)
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

    WIFI_SCRIPT = """\
mac80211_emit_detect() {
\tlocal band="$3"
\tlocal ssid="$default_ssid"
\tlocal key="$default_key"
\tlocal encryption="$default_encryption"

\t[ -n "$ssid" ] || ssid="LEDE"
\tkey="$default_key"

\tcase "$band" in
\t\t6g)
\t\t\t[ -n "$encryption" ] || encryption="owe"
\t\t;;
\t\t*)
\t\t\t[ -n "$encryption" ] || encryption="none"
\t\t;;
\tesac
}
"""

    def prepare(self) -> Path:
        self.write("include/version.mk", self.VERSION_MK)
        self.write("package/base-files/files/bin/config_generate", self.CONFIG_GENERATE)
        self.write("package/base-files/luci/bin/config_generate", self.CONFIG_GENERATE)
        self.write("package/lean/default-settings/files/zzz-default-settings", self.DEFAULT_SETTINGS)
        self.write("package/kernel/mac80211/files/lib/wifi/mac80211.sh", self.WIFI_SCRIPT)
        self.write(
            "target/linux/mediatek/Makefile",
            "KERNEL_PATCHVER:=6.12\nKERNEL_TESTING_PATCHVER:=6.18\n",
        )
        return self.root

    def test_core_customisations(self) -> None:
        tree = self.prepare()
        build_settings = settings.BuildSettings(
            ip="192.168.8.1",
            wifi_name="LabNet",
            wifi_password="password123",
            device="ruijie_rg-x60",
        ).validated()
        source.apply_core_customisations(tree, build_settings)

        version = util.read_text(tree / "include/version.mk")
        self.assertIn("VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),ZeroWrt)", version)
        self.assertIn("VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),ZeroWrt)", version)
        kernel = util.read_text(tree / "target/linux/mediatek/Makefile")
        self.assertIn("KERNEL_PATCHVER:=6.18", kernel)
        self.assertIn(f"VERSION_NUMBER:={configgen.build_date()}", version)

        for relative in source.CORE_FILES.values():
            if relative.name == "config_generate":
                text = util.read_text(tree / relative)
                self.assertIn('lan) ipad=${ipaddr:-"192.168.8.1"}', text)
                self.assertIn("hostname='ZeroWrt'", text)
                self.assertNotIn("192.168.1.1", text)

        default_settings = util.read_text(tree / source.CORE_FILES["default_settings"])
        self.assertIn("DISTRIB_DESCRIPTION='ZeroWrt '", default_settings)
        self.assertIn('OPENWRT_RELEASE="ZeroWrt R@BUILD_DATE@"', default_settings)
        self.assertNotIn("LEDE", default_settings)

        wifi = util.read_text(tree / source.WIFI_SCRIPTS[0])
        self.assertIn("2g) ssid=LabNet-2.4G", wifi)
        self.assertIn("5g) ssid=LabNet-5G", wifi)
        self.assertIn("key=password123", wifi)
        self.assertIn('encryption="psk2"', wifi)
        self.assertIn('encryption="sae"', wifi)
        self.assertNotIn('ssid="LEDE"', wifi)

    def test_ssr_plus_removed(self) -> None:
        tree = self.prepare()
        self.write("include/target.mk", "DEFAULT_PACKAGES.router += luci-app-ssr-plus luci-app-wol\n")
        self.write("package/lean/luci-app-ssr-plus/Makefile", "include $(TOPDIR)/rules.mk\n")
        self.write("target/linux/mediatek/filogic/target.mk", "DEFAULT_PACKAGES += luci-app-ssr-plus\n")
        build_settings = settings.BuildSettings().validated()

        source.apply_core_customisations(tree, build_settings)

        self.assertFalse((tree / "package/lean/luci-app-ssr-plus").exists())
        self.assertNotIn("luci-app-ssr-plus", util.read_text(tree / "include/target.mk"))
        self.assertNotIn(
            "luci-app-ssr-plus",
            util.read_text(tree / "target/linux/mediatek/filogic/target.mk"),
        )


class DeviceLookupTest(TempTreeTest):
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
""",
        )
        return self.root

    def test_find_device(self) -> None:
        device = configgen.find_device(self.prepare(), "ruijie_rg-x60")
        self.assertEqual(device["board"], "mediatek")
        self.assertEqual(device["subtarget"], "filogic")
        self.assertEqual(device["model"], "RG-X60")

    def test_find_pro_device(self) -> None:
        device = configgen.find_device(self.prepare(), "ruijie_rg-x60-pro")
        self.assertEqual(device["name"], "ruijie_rg-x60-pro")

    def test_missing_device_raises(self) -> None:
        self.prepare()
        with self.assertRaises(util.BuildError):
            configgen.find_device(self.root, "missing_device")


class ConfigRenderTest(unittest.TestCase):
    def test_target_and_packages(self) -> None:
        target = {
            "board": "mediatek",
            "subtarget": "filogic",
            "name": "ruijie_rg-x60",
            "model": "RG-X60",
            "vendor": "Ruijie",
        }
        text = configgen._render_config(target, configgen.PACKAGES)
        self.assertIn("CONFIG_TARGET_mediatek=y", text)
        self.assertIn("CONFIG_TARGET_mediatek_filogic=y", text)
        self.assertIn("CONFIG_TARGET_mediatek_filogic_DEVICE_ruijie_rg-x60=y", text)
        for package in configgen.PACKAGES:
            self.assertIn(f"{package}=y", text)
        self.assertNotIn("=y=y", text)
        self.assertNotIn("luci-compat", text)
        self.assertNotIn("CONFIG_VERSION_DIST", text)
        self.assertIn("CONFIG_DEVEL=y", text)
        self.assertIn("CONFIG_CCACHE=y", text)
        self.assertIn("CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray=y", text)
        self.assertIn("# CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox is not set", text)
        self.assertIn("# CONFIG_PACKAGE_sing-box is not set", text)

    def test_x86_64_profile(self) -> None:
        target = configgen.resolve_target(Path("."), "x86_64")
        text = configgen._render_config(target, configgen.PACKAGES)
        self.assertIn("CONFIG_TARGET_x86=y", text)
        self.assertIn("CONFIG_TARGET_x86_64=y", text)
        self.assertIn("CONFIG_TARGET_x86_64_Generic=y", text)
        self.assertNotIn("_DEVICE_", text)


class PackageSelectionTest(TempTreeTest):
    def test_argon_app_only_when_cloned(self) -> None:
        package = "CONFIG_PACKAGE_luci-app-argon-config"
        self.assertNotIn(package, configgen._packages(self.root))
        (self.root / "package/new/luci-app-argon-config").mkdir(parents=True)
        self.assertIn(package, configgen._packages(self.root))


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

        branding = self.root / "package/new/luci-theme-argon/htdocs/luci-static/resources/argon/branding.js"
        branding.parent.mkdir(parents=True)
        branding.write_text(
            "var defaults = { favicon: L.resource('../argon/icon/favicon-32x32.png') };\n",
            encoding="utf-8",
        )
        head_meta = self.root / "package/new/luci-theme-argon/ucode/template/themes/argon/head_meta.ut"
        head_meta.parent.mkdir(parents=True, exist_ok=True)
        head_meta.write_text('<link rel="icon" href="{{ media }}/favicon.ico">\n', encoding="utf-8")

        app = self.root / "package/new/luci-app-argon-config"
        config = app / "root/etc/config/argon"
        config.parent.mkdir(parents=True)
        config.write_text(
            "config global\n\toption login_style 'classic'\n\toption online_wallpaper 'bing'\n",
            encoding="utf-8",
        )
        defaults = app / "root/etc/uci-defaults/luci-argon-config"
        defaults.parent.mkdir(parents=True)
        defaults.write_text('uci -q set "argon.@global[0].online_wallpaper"="bing"\n', encoding="utf-8")

        templates = self.root / "package/new/luci-theme-argon/ucode/template/themes/argon"
        templates.mkdir(parents=True, exist_ok=True)
        footer = templates / "footer_login.ut"
        footer.write_text(
            "const firmware_info = version.distname + ' ' + version.distversion + '-' + version.distrevision;\n",
            encoding="utf-8",
        )
        admin_footer = templates / "footer.ut"
        admin_footer.write_text(
            "{{ version.distname }} {{ version.distversion }}-{{ version.distrevision }}\n",
            encoding="utf-8",
        )

        packages.patch_argon_theme(self.root / "package/new/luci-theme-argon", REPO_ROOT / "assets")
        packages.patch_argon_config(app)
        packages.patch_root_favicon(self.root, REPO_ROOT / "assets")

        expected_bg = (REPO_ROOT / "assets" / "background.jpg").read_bytes()
        self.assertEqual((static / "img" / "bg1.jpg").read_bytes(), expected_bg)
        self.assertIn("data:image/png;base64,", (static / "img" / "argon.svg").read_text())
        self.assertEqual((static / "favicon.ico").read_bytes()[:4], b"\x00\x00\x01\x00")
        self.assertEqual(images.png_size((static / "icon" / "favicon-16x16.png").read_bytes()), (16, 16))
        self.assertTrue((static / "icon" / "favicon-zerowrt.png").exists())
        branding_text = branding.read_text(encoding="utf-8")
        self.assertIn("favicon-zerowrt.png') + '?v=", branding_text)
        self.assertRegex(branding_text, r"\?v=\d{14}'")
        self.assertRegex(head_meta.read_text(encoding="utf-8"), r"favicon\.ico\?v=\d{14}")
        self.assertNotIn("distrevision", footer.read_text(encoding="utf-8"))
        self.assertNotIn("distrevision", admin_footer.read_text(encoding="utf-8"))
        self.assertIn("{{ version.distversion }}\n", admin_footer.read_text(encoding="utf-8"))
        root_icon = self.root / "package/base-files/files/www/favicon.ico"
        self.assertEqual(root_icon.read_bytes()[:4], b"\x00\x00\x01\x00")

        text = config.read_text(encoding="utf-8")
        self.assertIn("option online_wallpaper 'none'", text)
        self.assertIn("option mode 'light'", text)
        self.assertIn("option primary '#2E9D72'", text)
        self.assertIn("option dark_primary '#4CAF86'", text)
        self.assertIn("option dark_primary_mode 'custom'", text)
        self.assertNotIn("'bing'", text)
        self.assertIn('"none"', defaults.read_text(encoding="utf-8"))


class CollectTest(TempTreeTest):
    def test_collect_keeps_firmware_names(self) -> None:
        self.write(
            ".zerowrt-info.json",
            '{"board": "mediatek", "subtarget": "filogic", "device": "ruijie_rg-x60-pro", "version": "20261020"}\n',
        )
        source_dir = self.root / "bin/targets/mediatek/filogic"
        source_dir.mkdir(parents=True)
        firmware = "zerowrt-mediatek-filogic-ruijie_rg-x60-pro-squashfs-sysupgrade.bin"
        (source_dir / firmware).write_bytes(b"firmware")
        (source_dir / "zerowrt-mediatek-filogic-ruijie_rg-x60-pro.manifest").write_text("{}")
        (source_dir / "config.buildinfo").write_text("CONFIG_X=y\n")

        out = self.root / "dist"
        build.collect(self.root, out)
        names = {path.name for path in out.iterdir()}
        self.assertIn(firmware, names)
        self.assertIn("SHA256SUMS", names)
        self.assertIn("BUILD_INFO.txt", names)
        self.assertIn("config.buildinfo", names)

    def test_collect_x86_image(self) -> None:
        self.write(
            ".zerowrt-info.json",
            '{"board": "x86", "subtarget": "64", "device": "Generic", "artifact": "x86_64", "version": "20261020"}\n',
        )
        source_dir = self.root / "bin/targets/x86/64"
        source_dir.mkdir(parents=True)
        firmware = "zerowrt-x86-64-generic-squashfs-combined-efi.img.gz"
        (source_dir / firmware).write_bytes(b"firmware")

        out = self.root / "dist"
        build.collect(self.root, out)
        names = {path.name for path in out.iterdir()}
        self.assertIn(firmware, names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
