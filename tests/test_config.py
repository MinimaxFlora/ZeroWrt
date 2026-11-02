from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from zerowrt_core import config, profiles, util


class ConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = profiles.require("ruijie_rg-x60-new")
        self.target = config.target_symbol(self.profile)

    def test_set_option_replaces_assignment(self) -> None:
        text = "CONFIG_PACKAGE_luci-app-ota=y\nCONFIG_OTHER=y\n"
        updated = config.set_option(text, "CONFIG_PACKAGE_luci-app-ota", "n")
        self.assertIn("CONFIG_PACKAGE_luci-app-ota=n", updated)
        self.assertNotIn("CONFIG_PACKAGE_luci-app-ota=y", updated)
        self.assertIn("CONFIG_OTHER=y", updated)

    def test_set_option_replaces_not_set(self) -> None:
        text = "# CONFIG_PACKAGE_luci-app-ota is not set\n"
        updated = config.set_option(text, "CONFIG_PACKAGE_luci-app-ota", "y")
        self.assertIn("CONFIG_PACKAGE_luci-app-ota=y", updated)
        self.assertNotIn("is not set", updated)

    def test_render_adds_ota_and_keeps_target(self) -> None:
        text = f"{self.target}=y\nCONFIG_PACKAGE_luci-app-ota=y\n"
        updated = config.render_config(text, self.profile)
        self.assertIn(f"{self.target}=y", updated)
        self.assertIn("CONFIG_PACKAGE_luci-i18n-ota-zh-cn=y", updated)
        self.assertEqual(updated.count("CONFIG_PACKAGE_luci-app-ota=y"), 1)

    def test_render_rejects_wrong_device(self) -> None:
        with self.assertRaises(util.BuildError):
            config.render_config("CONFIG_TARGET_mediatek_filogic=y\n", self.profile)

    def test_resolve_device_reads_image_makefile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            image = tree / "target" / "linux" / "mediatek" / "image"
            image.mkdir(parents=True)
            (image / "filogic-ext.mk").write_text(
                "define Device/ruijie_rg-x60-new-mtkuboot\n"
                "  DEVICE_VENDOR := Ruijie\n"
                "  DEVICE_MODEL := RG-X60 New\n"
                "  DEVICE_VARIANT := (MTK U-Boot layout)\n"
                "  DEVICE_DTS := mt7986a-ruijie-rg-x60-new-mtkuboot\n"
                "endef\n",
                encoding="utf-8",
            )
            info = config.resolve_device(tree, self.profile)
            self.assertEqual(info["device_vendor"], "Ruijie")
            self.assertEqual(info["device_model"], "RG-X60 New")
            self.assertEqual(info["device_dts"], "mt7986a-ruijie-rg-x60-new-mtkuboot")


if __name__ == "__main__":
    unittest.main()
