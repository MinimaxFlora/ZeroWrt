"""Unit tests for the ZeroWrt build helpers.

Run with:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
import unittest.mock
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from zerowrt_core import build, configgen, images, packages, profiles, settings, source, util  # noqa: E402

TODAY = datetime.now().strftime("%Y%m%d")


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
                "ZEROWRT_DEVICE": "ruijie_rg-x60-new",
            }
        )
        self.assertEqual(value.ip, "192.168.8.1")
        self.assertEqual(value.ssid("5g"), "Lab-5G")
        self.assertEqual(value.device, "ruijie_rg-x60-new")


class ProfilesTest(unittest.TestCase):
    def test_only_the_rg_x60_is_supported(self) -> None:
        self.assertEqual(profiles.names(), ["ruijie_rg-x60-new"])

        profile = profiles.require("ruijie_rg-x60-new")
        self.assertEqual(profile.source, "immortalwrt")
        self.assertEqual(profile.device, "ruijie_rg-x60-new-ubootmod")

        upstream = profiles.source(profile)
        self.assertEqual(upstream.repo, "Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly")
        self.assertEqual(upstream.ref, "openwrt-24.10-6.6")
        self.assertEqual(profiles.DEFAULT_DEVICE, "ruijie_rg-x60-new")

    def test_x86_profile_is_gone(self) -> None:
        self.assertIsNone(profiles.find("x86_64"))
        with self.assertRaises(util.BuildError):
            profiles.require("x86_64")

    def test_unknown_profile_raises(self) -> None:
        with self.assertRaises(util.BuildError):
            profiles.require("ruijie_rg-x60-pro")


class CorePatchesTest(TempTreeTest):
    """Core customisations for the MT798x ImmortalWrt tree."""

    VERSION_MK = """\
VERSION_DIST:=$(call qstrip,$(CONFIG_VERSION_DIST))
VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),ImmortalWrt)
VERSION_MANUFACTURER:=$(call qstrip,$(CONFIG_VERSION_MANUFACTURER))
VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),ImmortalWrt)
VERSION_NUMBER:=$(call qstrip,$(CONFIG_VERSION_NUMBER))
VERSION_NUMBER:=$(if $(VERSION_NUMBER),$(VERSION_NUMBER),24.10-SNAPSHOT)
"""

    CONFIG_GENERATE = """\
generate_static_system() {
\t\tset system.@system[-1].hostname='ImmortalWrt'
}
generate_network() {
\t\tcase "$1" in
\t\t\tlan)
\t\t\t\tcase "$board" in
\t\t\t\t\truijie,rg-x60*)
\t\t\t\t\t\tipad=${ipaddr:-"192.168.110.1"}
\t\t\t\t\t;;
\t\t\t\t\t*)
\t\t\t\t\t\tipad=${ipaddr:-"192.168.6.1"}
\t\t\t\t\t;;
\t\t\t\tesac
\t\t\t;;
\t\tesac
}
"""

    OPENWRT_RELEASE = """\
DISTRIB_ID='%D'
DISTRIB_RELEASE='%V'
DISTRIB_REVISION='%R'
DISTRIB_DESCRIPTION='%D %V %C'
"""

    OS_RELEASE = """\
NAME="%D"
PRETTY_NAME="%D %V"
OPENWRT_RELEASE="%D %V %C"
"""

    UPSTREAM_BANNER = """\
  _______                     ________        __
 |       |.-----.-----.-----.|  |  |  |.----.|  |_
"""

    OVERLAY_BANNER = "ImmortalWrt-798x-24.10 from PadavanOnly\n"

    MTWIFI = """\
detect_mtwifi() {
\t\t\t\t\tssid="ImmortalWrt-2.4G"
\t\t\t\t\tset wireless.default_${dev}.ssid=${ssid}
\t\t\t\tuci -q batch <<-EOF
\t\t\t\t\tset wireless.default_${dev}=wifi-iface
\t\t\t\t\tset wireless.default_${dev}.encryption=none
\t\t\t\tEOF
\t\t\t\t\tssid="ImmortalWrt-5G"
}
"""

    def prepare(self) -> Path:
        self.write("include/version.mk", self.VERSION_MK)
        self.write("package/base-files/files/bin/config_generate", self.CONFIG_GENERATE)
        self.write("package/base-files/files/etc/openwrt_release", self.OPENWRT_RELEASE)
        self.write("package/base-files/files/usr/lib/os-release", self.OS_RELEASE)
        self.write("package/base-files/files/etc/banner", self.UPSTREAM_BANNER)
        self.write("files/etc/banner", self.OVERLAY_BANNER)
        self.write("package/mtk/applications/mtwifi-cfg/files/mtwifi.sh", self.MTWIFI)
        return self.root

    def test_core_customisations(self) -> None:
        tree = self.prepare()
        build_settings = settings.BuildSettings(
            ip="192.168.8.1",
            wifi_name="LabNet",
            wifi_password="password123",
        ).validated()
        source.apply_core_customisations(tree, build_settings)

        version = util.read_text(tree / "include/version.mk")
        self.assertIn("VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),ZeroWrt)", version)
        self.assertIn("VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),ZeroWrt)", version)
        self.assertIn(f"VERSION_NUMBER:={configgen.build_date()}", version)

        config_generate = util.read_text(tree / source.CORE_FILES["config_generate"])
        self.assertEqual(config_generate.count('ipad=${ipaddr:-"192.168.8.1"}'), 2)
        self.assertNotIn("192.168.110.1", config_generate)
        self.assertNotIn("192.168.6.1", config_generate)
        self.assertIn("hostname='ZeroWrt'", config_generate)
        self.assertNotIn("ImmortalWrt", config_generate)

        release = util.read_text(tree / source.CORE_FILES["openwrt_release"])
        self.assertIn(f"DISTRIB_DESCRIPTION='ZeroWrt-{TODAY}'", release)
        self.assertIn("DISTRIB_REVISION=' By MinimaxFlora'", release)
        self.assertNotIn("%D %V %C", release)

        os_release = util.read_text(tree / source.CORE_FILES["os_release"])
        self.assertIn(f'OPENWRT_RELEASE="ZeroWrt 标准版 @R{TODAY} BY MinimaxFlora"', os_release)

        # The tree overlay would override the bundled banner in the image.
        self.assertFalse((tree / "files").exists())

        wifi = util.read_text(tree / source.CORE_FILES["mtwifi"])
        self.assertIn('ssid="LabNet-2.4G"', wifi)
        self.assertIn('ssid="LabNet-5G"', wifi)
        self.assertIn("encryption=psk2", wifi)
        self.assertIn("key=password123", wifi)
        self.assertNotIn("encryption=none", wifi)

        expected_banner = (REPO_ROOT / "assets" / "banner").read_text(encoding="utf-8")
        self.assertEqual(util.read_text(tree / source.CORE_FILES["banner"]), expected_banner)

    def test_verify_rejects_a_leftover_board_default(self) -> None:
        tree = self.prepare()
        build_settings = settings.BuildSettings().validated()
        source.apply_core_customisations(tree, build_settings)

        path = tree / source.CORE_FILES["config_generate"]
        text = util.read_text(path).replace('ipad=${ipaddr:-"10.0.0.1"}', 'ipad=${ipaddr:-"192.168.110.1"}', 1)
        util.write_text(path, text)
        with self.assertRaises(util.BuildError):
            source.verify_core(tree, build_settings)

    def test_missing_banner_asset_is_not_fatal(self) -> None:
        tree = self.prepare()
        self.write("package/base-files/files/etc/banner", self.UPSTREAM_BANNER)
        with unittest.mock.patch.object(source, "read_banner", return_value=None):
            source.apply_core_customisations(tree, settings.BuildSettings().validated())
        self.assertEqual(util.read_text(tree / source.CORE_FILES["banner"]), self.UPSTREAM_BANNER)

    def test_missing_mtwifi_is_fatal(self) -> None:
        tree = self.prepare()
        (tree / source.CORE_FILES["mtwifi"]).unlink()
        with self.assertRaises(util.BuildError):
            source.apply_core_customisations(tree, settings.BuildSettings().validated())

    def test_customisations_can_be_reapplied(self) -> None:
        tree = self.prepare()
        build_settings = settings.BuildSettings().validated()
        source.apply_core_customisations(tree, build_settings)
        # A re-run (local debugging, retried step) must not fail on its own
        # output.
        source.apply_core_customisations(tree, build_settings)


class DeviceLookupTest(TempTreeTest):
    def prepare(self) -> Path:
        self.write("target/linux/mediatek/Makefile", "SUBTARGETS:=filogic mt7622\nKERNEL_PATCHVER:=6.6\n")
        self.write("target/linux/mediatek/filogic/target.mk", "DEFAULT_PACKAGES += kmod-mt7986-firmware\n")
        self.write("target/linux/mediatek/mt7622/target.mk", "# other subtarget\n")
        self.write(
            "target/linux/mediatek/image/filogic.mk",
            """\
define Device/ruijie_rg-x60-new-ubootmod
  DEVICE_VENDOR := Ruijie
  DEVICE_MODEL := RG-X60 New
  DEVICE_DTS := mt7986a-ruijie-rg-x60-new-ubootmod
endef
TARGET_DEVICES += ruijie_rg-x60-new-ubootmod

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
        device = configgen.find_device(self.prepare(), "ruijie_rg-x60-new-ubootmod")
        self.assertEqual(device["board"], "mediatek")
        self.assertEqual(device["subtarget"], "filogic")
        self.assertEqual(device["model"], "RG-X60 New")

    def test_profile_resolves_the_ubootmod_device(self) -> None:
        tree = self.prepare()
        target = configgen.resolve_target(tree, "ruijie_rg-x60-new")
        self.assertEqual(target["name"], "ruijie_rg-x60-new-ubootmod")
        self.assertEqual(target["board"], "mediatek")
        self.assertEqual(target["subtarget"], "filogic")

    def test_missing_device_raises(self) -> None:
        self.prepare()
        with self.assertRaises(util.BuildError):
            configgen.find_device(self.root, "missing_device")

    def test_unknown_name_falls_back_to_device_lookup(self) -> None:
        tree = self.prepare()
        target = configgen.resolve_target(tree, "ruijie_rg-x60-pro")
        self.assertEqual(target["name"], "ruijie_rg-x60-pro")

    def test_profile_without_source_tree_raises(self) -> None:
        with self.assertRaises(util.BuildError):
            configgen.resolve_target(self.root, "ruijie_rg-x60-new")


class ConfigRenderTest(unittest.TestCase):
    def test_target_and_packages(self) -> None:
        target = {
            "board": "mediatek",
            "subtarget": "filogic",
            "name": "ruijie_rg-x60-new-ubootmod",
            "model": "RG-X60 New",
            "vendor": "Ruijie",
        }
        text = configgen._render_config(target, configgen.PACKAGES)
        self.assertIn("CONFIG_TARGET_mediatek=y", text)
        self.assertIn("CONFIG_TARGET_mediatek_filogic=y", text)
        self.assertIn("CONFIG_TARGET_mediatek_filogic_DEVICE_ruijie_rg-x60-new-ubootmod=y", text)
        for package in configgen.PACKAGES:
            self.assertIn(f"{package}=y", text)
        self.assertNotIn("=y=y", text)
        self.assertNotIn("luci-compat", text)
        self.assertNotIn("CONFIG_VERSION_DIST", text)
        self.assertIn("CONFIG_DEVEL=y", text)

    def test_passwall_uses_sing_box_without_smartdns(self) -> None:
        target = {"board": "mediatek", "subtarget": "filogic", "name": "ruijie_rg-x60-new-ubootmod"}
        text = configgen._render_config(target, [])
        self.assertIn("CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox=y", text)
        self.assertIn("# CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray is not set", text)
        self.assertIn("# CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SmartDNS is not set", text)
        self.assertIn("CONFIG_PACKAGE_sing-box=y", text)
        self.assertIn("# CONFIG_PACKAGE_smartdns is not set", text)
        # Xray must not be pulled in any more.
        self.assertNotIn("CONFIG_PACKAGE_xray-core=y", text)
        self.assertNotIn("INCLUDE_Xray=y", text)


class PackageSelectionTest(TempTreeTest):
    def test_argon_app_only_when_cloned(self) -> None:
        package = "CONFIG_PACKAGE_luci-app-argon-config"
        self.assertNotIn(package, configgen._packages(self.root))
        (self.root / "package/new/luci-app-argon-config").mkdir(parents=True)
        self.assertIn(package, configgen._packages(self.root))

    def test_shared_packages_are_always_selected(self) -> None:
        packages_ = configgen._packages(self.root)
        self.assertIn("CONFIG_PACKAGE_luci-app-ramfree", packages_)
        self.assertIn("CONFIG_PACKAGE_luci-app-passwall", packages_)
        self.assertIn("CONFIG_PACKAGE_luci-app-openclash", packages_)
        self.assertNotIn("CONFIG_PACKAGE_luci-app-mosdns", packages_)

    def test_device_packages_land_in_the_config(self) -> None:
        target = configgen.resolve_target(self._tree(), "ruijie_rg-x60-new")
        text = configgen._render_config(target, configgen._packages(self.root))
        self.assertIn("CONFIG_PACKAGE_luci-app-ramfree=y", text)
        self.assertIn("CONFIG_TARGET_mediatek_filogic_DEVICE_ruijie_rg-x60-new-ubootmod=y", text)

    def _tree(self) -> Path:
        self.write("target/linux/mediatek/Makefile", "SUBTARGETS:=filogic\n")
        self.write("target/linux/mediatek/filogic/target.mk", "BOARDNAME:=MediaTek Filogic\n")
        self.write(
            "target/linux/mediatek/image/filogic.mk",
            "define Device/ruijie_rg-x60-new-ubootmod\n  DEVICE_VENDOR := Ruijie\n"
            "  DEVICE_MODEL := RG-X60 New\nendef\nTARGET_DEVICES += ruijie_rg-x60-new-ubootmod\n",
        )
        return self.root


class FeedConflictTest(TempTreeTest):
    """Feeds must not ship anything that package/new already provides."""

    def feed(self, relative: str, pkg_name: str, buildpackages: str) -> None:
        self.write(f"{relative}/Makefile", f"PKG_NAME:={pkg_name}\ninclude $(TOPDIR)/rules.mk\n{buildpackages}\n")

    def test_geoip_and_geosite_come_from_the_new_tree(self) -> None:
        # helloworld's v2ray-geodata directory builds these two, and the feed
        # ships the same names from a directory called net/v2ray-geodata, so a
        # directory-name match alone would leave the duplicate behind.
        self.feed(
            "feeds/packages/net/v2ray-geodata",
            "v2ray-geodata",
            "$(eval $(call BuildPackage,v2ray-geoip))\n$(eval $(call BuildPackage,v2ray-geosite))",
        )
        source.prune_feed_conflicts(self.root)
        self.assertFalse((self.root / "feeds/packages/net/v2ray-geodata").exists())

    def test_sing_box_feed_copy_is_dropped(self) -> None:
        # ImmortalWrt ships sing-box in feeds/packages/net; half of the build
        # would otherwise come from helloworld and half from the feed.
        self.feed("feeds/packages/net/sing-box", "sing-box", "$(eval $(call BuildPackage,sing-box))")
        source.prune_feed_conflicts(self.root)
        self.assertFalse((self.root / "feeds/packages/net/sing-box").exists())

    def test_passwall_and_ramfree_feed_copies_are_dropped(self) -> None:
        self.feed(
            "feeds/luci/applications/luci-app-passwall",
            "luci-app-passwall",
            "$(eval $(call BuildPackage,$(PKG_NAME)))",
        )
        self.feed(
            "feeds/luci/applications/luci-app-ramfree",
            "luci-app-ramfree",
            "$(eval $(call BuildPackage,$(PKG_NAME)))",
        )
        source.prune_feed_conflicts(self.root)
        self.assertFalse((self.root / "feeds/luci/applications/luci-app-passwall").exists())
        self.assertFalse((self.root / "feeds/luci/applications/luci-app-ramfree").exists())

    def test_installed_feed_links_are_pruned_too(self) -> None:
        self.feed("package/feeds/packages/sing-box", "sing-box", "$(eval $(call BuildPackage,sing-box))")
        source.prune_feed_conflicts(self.root)
        self.assertFalse((self.root / "package/feeds/packages/sing-box").exists())

    def test_unrelated_feed_package_survives(self) -> None:
        self.feed("feeds/packages/net/curl", "curl", "$(eval $(call BuildPackage,curl))")
        source.prune_feed_conflicts(self.root)
        self.assertTrue((self.root / "feeds/packages/net/curl").exists())

    def test_asset_directory_with_a_package_name_survives(self) -> None:
        # A LuCI app ships static assets under a path that can end in a package
        # name; those directories have no Makefile and must not be touched.
        self.write("feeds/luci/applications/luci-app-example/htdocs/sing-box/index.html", "hi")
        source.prune_feed_conflicts(self.root)
        self.assertTrue((self.root / "feeds/luci/applications/luci-app-example/htdocs/sing-box").exists())


class OtaIndexTest(TempTreeTest):
    """The OTA index generator must publish the ubootmod image, not preloader.bin."""

    GENERATOR = """\
BAD_TOKENS = (
    "factory",
    "initramfs",
    "vmlinux",
    "kernel",
    "rootfs.",
    "-rootfs",
    "uImage",
    "u-boot",
    "uboot",
    "recovery",
)
"""

    def prepare(self) -> Path:
        self.write("package/new/luci-app-ota/tools/gen_ota_index.py", self.GENERATOR)
        return self.root

    def test_ubootmod_image_is_no_longer_filtered(self) -> None:
        tree = self.prepare()
        packages.patch_ota_index(tree / "package" / "new" / "luci-app-ota")

        text = util.read_text(tree / "package/new/luci-app-ota/tools/gen_ota_index.py")
        self.assertNotIn('"uboot",', text)
        self.assertIn('"preloader",', text)
        self.assertIn('"bl31",', text)
        self.assertIn('"u-boot",', text)

    def test_patch_is_idempotent(self) -> None:
        tree = self.prepare()
        app = tree / "package" / "new" / "luci-app-ota"
        packages.patch_ota_index(app)
        packages.patch_ota_index(app)

    def test_changed_upstream_layout_fails_loudly(self) -> None:
        tree = self.prepare()
        self.write("package/new/luci-app-ota/tools/gen_ota_index.py", 'BAD_TOKENS = ("uboot",)\n')
        with self.assertRaises(util.BuildError):
            packages.patch_ota_index(tree / "package" / "new" / "luci-app-ota")


class ArgonWgetTest(TempTreeTest):
    """Argon's apk-only wget-any must not reach the opkg-only tree."""

    def test_apk_only_dependency_is_replaced(self) -> None:
        makefile = self.write(
            "theme/Makefile",
            "LUCI_DEPENDS:=+luci-base +USE_APK:wget-any +!USE_APK:wget +flock\n",
        )
        packages._fix_argon_wget_dep(self.root / "theme")

        text = util.read_text(makefile)
        self.assertNotIn("wget-any", text)
        self.assertNotIn("USE_APK", text)
        self.assertIn("+wget-ssl", text)
        self.assertIn("+flock", text)

    def test_already_single_dependency_is_left_alone(self) -> None:
        makefile = self.write("theme/Makefile", "LUCI_DEPENDS:=+luci-base +wget-ssl +flock\n")
        packages._fix_argon_wget_dep(self.root / "theme")
        self.assertEqual(util.read_text(makefile), "LUCI_DEPENDS:=+luci-base +wget-ssl +flock\n")

    def test_unexpected_layout_fails_loudly(self) -> None:
        self.write("theme/Makefile", "LUCI_DEPENDS:=+USE_APK:wget-any\n")
        with self.assertRaises(util.BuildError):
            packages._fix_argon_wget_dep(self.root / "theme")


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
            '{"board": "mediatek", "subtarget": "filogic", "device": "ruijie_rg-x60-new-ubootmod", '
            '"artifact": "ruijie_rg-x60-new", "layout": "OpenWrt U-Boot layout (ubootmod)", '
            '"version": "20261020"}\n',
        )
        source_dir = self.root / "bin/targets/mediatek/filogic"
        source_dir.mkdir(parents=True)
        firmware = "zerowrt-mediatek-filogic-ruijie_rg-x60-new-ubootmod-squashfs-sysupgrade.itb"
        (source_dir / firmware).write_bytes(b"firmware")
        (source_dir / "zerowrt-mediatek-filogic-ruijie_rg-x60-new-ubootmod.manifest").write_text("{}")
        (source_dir / "config.buildinfo").write_text("CONFIG_X=y\n")

        out = self.root / "dist"
        build.collect(self.root, out)
        names = {path.name for path in out.iterdir()}
        self.assertIn(firmware, names)
        self.assertIn("SHA256SUMS", names)
        self.assertIn("BUILD_INFO.txt", names)
        self.assertIn("config.buildinfo", names)

        info_text = (out / "BUILD_INFO.txt").read_text(encoding="utf-8")
        self.assertIn("profile: ruijie_rg-x60-new", info_text)
        self.assertIn("layout: OpenWrt U-Boot layout (ubootmod)", info_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
