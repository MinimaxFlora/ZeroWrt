from __future__ import annotations

import unittest

from zerowrt_core import profiles
from zerowrt_core.settings import BuildSettings


class ProfileTest(unittest.TestCase):
    def test_all_requested_devices_are_registered(self) -> None:
        expected = {
            "netcore_n60-pro",
            "ruijie_ew-6000gx-pro-expand",
            "ruijie_ew-6000gx-pro",
            "ruijie_ew-6000gx-pro-stock",
            "ruijie_ew-6000gx-pro-ubootmod",
            "ruijie_rg-x60-new-expand",
            "ruijie_rg-x60-new",
            "ruijie_rg-x60-new-stock",
            "ruijie_rg-x60-new-ubootmod",
            "supergateway_s20l",
            "supergateway_s20m",
            "supergateway_s20p",
        }
        self.assertEqual(set(profiles.names()), expected)
        self.assertEqual(len(profiles.names()), 12)

    def test_all_devices_use_unified_10_0_0_1(self) -> None:
        for name in profiles.names():
            profile = profiles.require(name)
            self.assertEqual(profile.lan_ip, "10.0.0.1", name)

    def test_target_is_always_mediatek_filogic(self) -> None:
        for name in profiles.names():
            profile = profiles.require(name)
            self.assertEqual(profile.target, "mediatek/filogic")

    def test_default_is_netcore(self) -> None:
        self.assertEqual(profiles.DEFAULT_DEVICE, "netcore_n60-pro")
        self.assertEqual(profiles.RELEASE_TAG, "mediatek_filogic")

    def test_settings_effective_ip(self) -> None:
        ruijie = BuildSettings(device="ruijie_rg-x60-new")
        self.assertEqual(ruijie.effective_ip(), "10.0.0.1")
        other = BuildSettings(device="netcore_n60-pro")
        self.assertEqual(other.effective_ip(), "10.0.0.1")
        override = BuildSettings(device="netcore_n60-pro", lan_ip="10.0.0.2")
        self.assertEqual(override.effective_ip(), "10.0.0.2")


if __name__ == "__main__":
    unittest.main()
