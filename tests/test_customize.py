from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

from zerowrt_core import customize, state, util
from zerowrt_core.settings import BuildSettings

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS = REPO_ROOT / "assets"


class CustomizeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tree = Path(self.tmp.name)
        self.build_date = int(time.time())
        self.version = state.version_for(self.build_date)
        state.write(
            self.tree,
            {
                "build_date": self.build_date,
                "version": self.version,
                "device": "netcore_n60-pro",
                "profile": "netcore_n60-pro",
                "dist": "ZeroWrt",
            },
        )
        self._write_tree()

    def _write(self, relative: str, text: str) -> None:
        path = self.tree / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def _write_bytes(self, relative: str, data: bytes) -> None:
        path = self.tree / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def _write_tree(self) -> None:
        self._write(
            "include/version.mk",
            "VERSION_NUMBER:=$(call qstrip,$(CONFIG_VERSION_NUMBER))\n"
            "VERSION_NUMBER:=$(if $(VERSION_NUMBER),$(VERSION_NUMBER),24.10-SNAPSHOT)\n"
            "VERSION_DIST:=$(call qstrip,$(CONFIG_VERSION_DIST))\n"
            "VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),ImmortalWrt)\n"
            "VERSION_MANUFACTURER:=$(call qstrip,$(CONFIG_VERSION_MANUFACTURER))\n"
            "VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),ImmortalWrt)\n",
        )
        self._write(
            "package/base-files/files/etc/openwrt_release",
            "DISTRIB_ID='%D'\nDISTRIB_RELEASE='%V'\nDISTRIB_DESCRIPTION='%D %V %C'\nDISTRIB_REVISION='%R'\n",
        )
        self._write(
            "package/base-files/files/usr/lib/os-release",
            'NAME="%D"\nOPENWRT_RELEASE="%D %V %C"\n',
        )
        self._write(
            "package/base-files/files/bin/config_generate",
            "lan)\n"
            '\tcase "$board" in\n'
            "\t\truijie,ew-6000gx-pro*|\\\n"
            "\t\truijie,rg-x60*)\n"
            '\t\t\tipad=${ipaddr:-"192.168.110.1"}\n'
            "\t\t;;\n"
            "\t\t*)\n"
            '\t\t\tipad=${ipaddr:-"192.168.6.1"}\n'
            "\t\t;;\n"
            "\tesac\n"
            '\t*) ipad=${ipaddr:-"192.168.$((addr_offset++)).1"} ;;\n'
            "set system.@system[-1].hostname='ImmortalWrt'\n",
        )
        self._write("package/base-files/files/etc/banner", "old banner\n")
        self._write("files/etc/banner", "vendor override\n")
        self._write("package/base-files/files/etc/shadow", "root:::0:99999:7:::\n")
        self._write(
            "package/mtk/applications/mtwifi-cfg/files/mtwifi.sh",
            'ssid="ImmortalWrt-2.4G"\n'
            'ssid="ImmortalWrt-5G"\n'
            "set wireless.default_${dev}.ssid=${ssid}\n"
            "\t\t\t\t\tset wireless.default_${dev}.encryption=none\n",
        )
        self._write(
            "feeds/luci/modules/luci-mod-status/htdocs/luci-static/resources/view/status/include/10_system.js",
            "return baseclass.extend({\n"
            "\trender: function(data) {\n"
            "\t\tvar fields = [\n"
            "\t\t\t_('Hostname'), boardinfo.hostname,\n"
            "\t\t\t_('CPU usage (%)'),    cpuusage.cpuusage\n"
            "\t\t];\n"
            "\t}\n"
            "});\n",
        )
        self._write(
            "feeds/luci/modules/luci-base/po/zh_Hans/base.po",
            'msgid ""\nmsgstr ""\n"Language: zh_Hans\\n"\n',
        )
        self._write("package/new/luci-theme-argon/Makefile", "include $(TOPDIR)/rules.mk\n")
        self._write_bytes("package/new/luci-theme-argon/htdocs/luci-static/argon/img/bg1.webp", b"old bg")
        self._write_bytes("package/new/luci-theme-argon/htdocs/luci-static/argon/favicon.ico", b"old icon")
        self._write(
            "package/new/luci-theme-argon/root/etc/config/argon",
            "config global\n"
            "\toption login_style 'classic'\n"
            "\toption primary '#5e72e4'\n"
            "\toption dark_primary '#483d8b'\n"
            "\toption dark_primary_mode 'auto'\n"
            "\toption mode 'normal'\n"
            "\toption online_wallpaper 'none'\n",
        )

    def _apply(self, settings: BuildSettings | None = None) -> None:
        with mock.patch.object(customize, "_openssl_hash", return_value="$5$fake$hash"):
            customize.apply(
                self.tree,
                settings or BuildSettings(root_password="password"),
                assets=ASSETS,
                repo_root=REPO_ROOT,
            )

    def test_apply_and_verify(self) -> None:
        self._apply()
        version_mk = (self.tree / "include/version.mk").read_text(encoding="utf-8")
        self.assertIn("VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),ZeroWrt)", version_mk)
        self.assertIn(
            "VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),ZeroWrt)",
            version_mk,
        )
        self.assertIn("24.10-SNAPSHOT", version_mk)

        release = (self.tree / "package/base-files/files/etc/openwrt_release").read_text(encoding="utf-8")
        self.assertIn(f"DISTRIB_DESCRIPTION='ZeroWrt-{self.version}'", release)
        self.assertIn("DISTRIB_REVISION=' By MinimaxFlora'", release)
        os_release = (self.tree / "package/base-files/files/usr/lib/os-release").read_text(encoding="utf-8")
        self.assertIn(
            f'OPENWRT_RELEASE="ZeroWrt 标准版 @R{self.version} BY MinimaxFlora"',
            os_release,
        )

        generate = (self.tree / "package/base-files/files/bin/config_generate").read_text(encoding="utf-8")
        self.assertIn("hostname='ZeroWrt'", generate)
        self.assertEqual(generate.count('ipad=${ipaddr:-"10.0.0.1"}'), 2)
        self.assertNotIn("192.168.110.1", generate)
        self.assertNotIn('ipad=${ipaddr:-"192.168.6.1"}', generate)

        self.assertFalse((self.tree / "files/etc").exists())
        self.assertEqual(
            (self.tree / "package/base-files/files/etc/banner").read_bytes(),
            (ASSETS / "banner").read_bytes(),
        )
        self.assertIn(
            "root:$5$fake$hash:",
            (self.tree / "package/base-files/files/etc/shadow").read_text(encoding="utf-8"),
        )

        wifi = (self.tree / "package/mtk/applications/mtwifi-cfg/files/mtwifi.sh").read_text(encoding="utf-8")
        self.assertIn('ssid="ZeroWrt-2.4G"', wifi)
        self.assertIn('ssid="ZeroWrt-5G"', wifi)
        self.assertIn("encryption=psk2", wifi)
        self.assertIn("key='1234567890'", wifi)
        self.assertNotIn("ImmortalWrt-", wifi)

        argon = (self.tree / "package/new/luci-theme-argon/root/etc/config/argon").read_text(encoding="utf-8")
        self.assertIn("option mode 'light'", argon)
        self.assertIn("option primary '#EC4899'", argon)
        self.assertIn("option dark_primary '#BE185D'", argon)
        self.assertEqual(
            (self.tree / "package/new/luci-theme-argon/htdocs/luci-static/argon/img/bg1.webp").read_bytes(),
            (ASSETS / "bg1.webp").read_bytes(),
        )
        self.assertEqual(
            (self.tree / "package/new/luci-theme-argon/htdocs/luci-static/argon/favicon.ico").read_bytes(),
            (ASSETS / "favicon.ico").read_bytes(),
        )
        with Image.open(
            self.tree / "package/new/luci-theme-argon/htdocs/luci-static/argon/icon/favicon-32x32.png"
        ) as image:
            self.assertEqual(image.size, (32, 32))
        with Image.open(
            self.tree / "package/new/luci-theme-argon/htdocs/luci-static/argon/icon/android-icon-192x192.png"
        ) as image:
            self.assertEqual(image.size, (192, 192))
        svg = (self.tree / "package/new/luci-theme-argon/htdocs/luci-static/argon/img/argon.svg").read_text(
            encoding="utf-8"
        )
        self.assertIn("data:image/png;base64,", svg)

    def test_apply_is_idempotent(self) -> None:
        self._apply()
        self._apply()
        wifi = (self.tree / "package/mtk/applications/mtwifi-cfg/files/mtwifi.sh").read_text(encoding="utf-8")
        self.assertEqual(wifi.count("key='1234567890'"), 1)
        generate = (self.tree / "package/base-files/files/bin/config_generate").read_text(encoding="utf-8")
        self.assertEqual(generate.count('ipad=${ipaddr:-"10.0.0.1"}'), 2)

    def test_explicit_lan_ip_replaces_both_defaults(self) -> None:
        self._apply(BuildSettings(lan_ip="10.0.0.2", root_password="password"))
        generate = (self.tree / "package/base-files/files/bin/config_generate").read_text(encoding="utf-8")
        self.assertEqual(generate.count('ipad=${ipaddr:-"10.0.0.2"}'), 2)
        self.assertNotIn("192.168.110.1", generate)
        self.assertNotIn('ipad=${ipaddr:-"192.168.6.1"}', generate)
        self.assertIn('ipad=${ipaddr:-"192.168.$((addr_offset++)).1"}', generate)

    def test_lan_ip_equal_to_upstream_default_is_valid(self) -> None:
        self._apply(BuildSettings(lan_ip="192.168.110.1", root_password="password"))
        generate = (self.tree / "package/base-files/files/bin/config_generate").read_text(encoding="utf-8")
        self.assertEqual(generate.count('ipad=${ipaddr:-"192.168.110.1"}'), 2)
        self.assertNotIn('ipad=${ipaddr:-"192.168.6.1"}', generate)

    def test_custom_wifi(self) -> None:
        self._apply(BuildSettings(wifi_name="Lab", wifi_password="abcdefgh", root_password="password"))
        wifi = (self.tree / "package/mtk/applications/mtwifi-cfg/files/mtwifi.sh").read_text(encoding="utf-8")
        self.assertIn('ssid="Lab-5G"', wifi)
        self.assertIn("key='abcdefgh'", wifi)

    def test_missing_mtwifi_fails(self) -> None:
        (self.tree / "package/mtk/applications/mtwifi-cfg/files/mtwifi.sh").unlink()
        with self.assertRaises(util.BuildError):
            self._apply()

    def test_wrong_default_ssid_fails(self) -> None:
        path = self.tree / "package/mtk/applications/mtwifi-cfg/files/mtwifi.sh"
        path.write_text('ssid="Something-2.4G"\n', encoding="utf-8")
        with self.assertRaises(util.BuildError):
            self._apply()


if __name__ == "__main__":
    unittest.main()
