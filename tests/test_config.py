from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zerowrt_core import config, profiles, state


class ConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = profiles.require("netcore_n60-pro")

    def test_set_option_replaces_assignment_and_not_set(self) -> None:
        text = "CONFIG_PACKAGE_luci-app-ota=y\n# CONFIG_PACKAGE_x is not set\n"
        text = config.set_option(text, "CONFIG_PACKAGE_luci-app-ota", "n")
        text = config.set_option(text, "CONFIG_PACKAGE_x", "y")
        self.assertIn("CONFIG_PACKAGE_luci-app-ota=n", text)
        self.assertIn("CONFIG_PACKAGE_x=y", text)
        self.assertNotIn("is not set", text)

    def test_strip_keeps_rootfs_options(self) -> None:
        text = (
            "CONFIG_TARGET_mediatek=y\n"
            "CONFIG_TARGET_mediatek_mt7986=y\n"
            "CONFIG_TARGET_MULTI_PROFILE=y\n"
            "CONFIG_TARGET_PER_DEVICE_ROOTFS=y\n"
            "CONFIG_TARGET_DEVICE_mediatek_mt7986_DEVICE_glinet_gl-mt6000=y\n"
            'CONFIG_TARGET_DEVICE_PACKAGES_mediatek_mt7986_DEVICE_glinet_gl-mt6000=""\n'
            "CONFIG_TARGET_ROOTFS_SQUASHFS=y\n"
            "CONFIG_TARGET_KERNEL_PARTSIZE=32\n"
            "CONFIG_PACKAGE_kmod-mt_wifi=y\n"
        )
        stripped = config.strip_target_selection(text)
        self.assertNotIn("CONFIG_TARGET_mediatek", stripped)
        self.assertNotIn("gl-mt6000", stripped)
        self.assertIn("CONFIG_TARGET_ROOTFS_SQUASHFS=y", stripped)
        self.assertIn("CONFIG_TARGET_KERNEL_PARTSIZE=32", stripped)
        self.assertIn("CONFIG_PACKAGE_kmod-mt_wifi=y", stripped)

    def test_render_selects_exactly_one_device_and_packages(self) -> None:
        base = (
            "CONFIG_TARGET_mediatek=y\n"
            "CONFIG_TARGET_mediatek_mt7986=y\n"
            "CONFIG_TARGET_DEVICE_mediatek_filogic_DEVICE_ruijie_rg-x60-new=y\n"
            'CONFIG_TARGET_DEVICE_PACKAGES_mediatek_filogic_DEVICE_ruijie_rg-x60-new=""\n'
            "CONFIG_TARGET_ROOTFS_SQUASHFS=y\n"
            "CONFIG_PACKAGE_kmod-mt_wifi=y\n"
            "CONFIG_PACKAGE_kmod-mediatek_hnat=y\n"
            "CONFIG_PACKAGE_luci-app-turboacc-mtk=y\n"
            "CONFIG_PACKAGE_luci-app-mtwifi-cfg=y\n"
            "# CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray is not set\n"
            "CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox=y\n"
            "CONFIG_PACKAGE_sing-box=y\n"
        )
        rendered = config.render_config(base, self.profile)
        self.assertIn("CONFIG_TARGET_mediatek=y", rendered)
        self.assertIn("CONFIG_TARGET_mediatek_filogic=y", rendered)
        self.assertIn("CONFIG_TARGET_MULTI_PROFILE=y", rendered)
        self.assertIn("CONFIG_TARGET_PER_DEVICE_ROOTFS=y", rendered)
        self.assertIn(
            "CONFIG_TARGET_DEVICE_mediatek_filogic_DEVICE_netcore_n60-pro=y",
            rendered,
        )
        self.assertIn(
            'CONFIG_TARGET_DEVICE_PACKAGES_mediatek_filogic_DEVICE_netcore_n60-pro=""',
            rendered,
        )
        self.assertNotIn("ruijie_rg-x60-new", rendered)
        self.assertNotIn("CONFIG_TARGET_mediatek_mt7986=y", rendered)
        self.assertIn("CONFIG_TARGET_ROOTFS_SQUASHFS=y", rendered)
        self.assertIn("CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray=y", rendered)
        self.assertIn("# CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox is not set", rendered)
        self.assertIn("# CONFIG_PACKAGE_sing-box is not set", rendered)
        self.assertIn("CONFIG_PACKAGE_ddns-scripts-aliyun=y", rendered)
        self.assertIn("CONFIG_PACKAGE_luci-app-3cat=y", rendered)
        self.assertIn("CONFIG_PACKAGE_luci-proto-wireguard=y", rendered)
        self.assertIn("CONFIG_PACKAGE_wireguard-tools=y", rendered)
        self.assertIn("CONFIG_PACKAGE_kmod-wireguard=y", rendered)
        self.assertNotIn("CONFIG_PACKAGE_luci-app-argon-config=y", rendered)
        self.assertEqual(
            rendered.count("CONFIG_TARGET_DEVICE_mediatek_filogic_DEVICE_netcore_n60-pro"),
            1,
        )
        self.assertEqual(
            rendered.count("CONFIG_TARGET_DEVICE_PACKAGES_mediatek_filogic_DEVICE_netcore_n60-pro"),
            1,
        )

    def test_check_resolved_rejects_second_device_and_singbox(self) -> None:
        resolved = (
            f"{config.target_symbol(self.profile.device)}=y\n"
            "CONFIG_TARGET_DEVICE_mediatek_filogic_DEVICE_ruijie_rg-x60-new=y\n"
            "CONFIG_PACKAGE_sing-box=y\n"
        )
        problems = config._check_resolved(resolved, self.profile)
        self.assertTrue(any("another device" in item for item in problems))
        self.assertTrue(any("sing-box" in item for item in problems))

    def test_roundtrip_diff_detects_changed_option(self) -> None:
        before = "CONFIG_A=y\n# CONFIG_B is not set\n"
        after = "CONFIG_A=n\n# CONFIG_B is not set\n"
        self.assertEqual(config._roundtrip_diff(before, after), ["CONFIG_A"])
        self.assertEqual(config._roundtrip_diff(before, before), [])

    def test_preview_without_make(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            base = tree / "defconfig" / "mt7975-ipailna-high-power.config"
            base.parent.mkdir(parents=True)
            base.write_text(
                "CONFIG_TARGET_mediatek_mt7986=y\nCONFIG_PACKAGE_kmod-mt_wifi=y\n",
                encoding="utf-8",
            )
            text = config.preview(tree, device="netcore_n60-pro")
            self.assertIn(
                "CONFIG_TARGET_DEVICE_mediatek_filogic_DEVICE_netcore_n60-pro=y",
                text,
            )
            self.assertIn("CONFIG_PACKAGE_luci-proto-wireguard=y", text)

    def test_resolve_device_vendor_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            image = tree / "target" / "linux" / "mediatek" / "image"
            image.mkdir(parents=True)
            (image / "filogic.mk").write_text(
                "define Device/supergateway_s20-common\n"
                "  DEVICE_VENDOR := Super Gateway\n"
                "endef\n"
                "define Device/supergateway_s20l\n"
                "  $(call Device/supergateway_s20-common)\n"
                "  DEVICE_MODEL := S20L\n"
                "  DEVICE_DTS := mt7986a-supergateway-s20l\n"
                "endef\n",
                encoding="utf-8",
            )
            info = config.resolve_device(tree, profiles.require("supergateway_s20l"))
            self.assertEqual(info["device_vendor"], "Super Gateway")
            self.assertEqual(info["device_model"], "S20L")
            self.assertEqual(info["device_dts"], "mt7986a-supergateway-s20l")

    def test_resolve_device_avoids_duplicate_variant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            image = tree / "target" / "linux" / "mediatek" / "image"
            image.mkdir(parents=True)
            (image / "filogic.mk").write_text(
                "define Device/ruijie_rg-x60-new-expand\n"
                "  DEVICE_VENDOR := Ruijie\n"
                "  DEVICE_MODEL := RG-X60 New (Expand)\n"
                "  DEVICE_DTS := mt7986a-ruijie-rg-x60-new-expand\n"
                "endef\n",
                encoding="utf-8",
            )
            info = config.resolve_device(tree, profiles.require("ruijie_rg-x60-new-expand"))
            self.assertEqual(info["device_model"], "RG-X60 New (Expand)")
            self.assertEqual(info["device_variant"], "")

    def test_static_configs_exist_for_every_device(self) -> None:
        for name in profiles.names():
            profile = profiles.require(name)
            path = config.static_path(profile)
            self.assertTrue(path.is_file(), path)
            text = path.read_text(encoding="utf-8")
            target = f"{config.target_symbol(profile.device)}=y"
            self.assertIn(target, text)
            devices = [
                line
                for line in text.splitlines()
                if line.startswith("CONFIG_TARGET_DEVICE_") and line.endswith("=y") and "PACKAGES" not in line
            ]
            self.assertEqual(devices, [target], path.name)
            # diffconfig.sh output is a small delta, not a 9000-line .config.
            self.assertLess(len(text.splitlines()), 3000, path.name)

    def test_apply_copies_static_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            state.write(
                tree,
                {
                    "build_date": 1762524000,
                    "version": "20261109",
                    "device": "netcore_n60-pro",
                    "profile": "netcore_n60-pro",
                },
            )
            expected = config.static_path(profiles.require("netcore_n60-pro")).read_text(encoding="utf-8")
            with mock.patch.object(config, "_run_defconfig", return_value=expected):
                info = config.apply(tree, device="netcore_n60-pro")
            self.assertEqual((tree / ".config").read_text(encoding="utf-8"), expected)
            self.assertEqual(info["device"], "netcore_n60-pro")
            self.assertEqual(info["version"], "20261109")


if __name__ == "__main__":
    unittest.main()
