from __future__ import annotations

import unittest

from zerowrt_core import util
from zerowrt_core.settings import BuildSettings


class SettingsTest(unittest.TestCase):
    def test_defaults(self) -> None:
        settings = BuildSettings()
        self.assertEqual(settings.device, "netcore_n60-pro")
        self.assertEqual(settings.lan_ip, "10.0.0.1")
        self.assertEqual(settings.ota_url, "https://ota.tatalvpai.vip/ota.json")
        self.assertEqual(settings.wifi_password, "1234567890")
        self.assertEqual(settings.ssid("2g"), "ZeroWrt-2.4G")
        self.assertEqual(settings.ssid("5g"), "ZeroWrt-5G")

    def test_environment(self) -> None:
        settings = BuildSettings.from_environment(
            {
                "ZEROWRT_DEVICE": "ruijie_rg-x60-new",
                "ZEROWRT_LAN_IP": "10.0.0.2",
                "ZEROWRT_WIFI_NAME": "Lab",
                "ZEROWRT_WIFI_PASSWORD": "abcdefgh",
            }
        )
        self.assertEqual(settings.effective_ip(), "10.0.0.2")
        self.assertEqual(settings.ssid("5g"), "Lab-5G")

    def test_invalid_ip(self) -> None:
        with self.assertRaises(util.BuildError):
            BuildSettings(lan_ip="192.168.1.999")

    def test_ipv6_rejected(self) -> None:
        with self.assertRaises(util.BuildError):
            BuildSettings(lan_ip="fd00::1")

    def test_invalid_wifi_password(self) -> None:
        with self.assertRaises(util.BuildError):
            BuildSettings(wifi_password="short")

    def test_unknown_device(self) -> None:
        with self.assertRaises(util.BuildError):
            BuildSettings(device="not-a-device")

    def test_ssid_too_long(self) -> None:
        with self.assertRaises(util.BuildError):
            BuildSettings(wifi_name="x" * 32)


if __name__ == "__main__":
    unittest.main()
