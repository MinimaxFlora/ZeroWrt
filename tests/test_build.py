from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from zerowrt_core import build, state, util


class BuildTest(unittest.TestCase):
    def _tree(self, files: list[str]) -> tuple[tempfile.TemporaryDirectory, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        tree = Path(tmp.name)
        target = tree / "bin" / "targets" / "mediatek" / "filogic"
        target.mkdir(parents=True)
        for name in files:
            (target / name).write_bytes(b"firmware")
        state.write(
            tree,
            {
                "board": "mediatek",
                "subtarget": "filogic",
                "device": "netcore_n60-pro",
                "build_date": 1762524000,
                "version": "20261107",
            },
        )
        return tmp, tree

    def test_collect_only_firmware(self) -> None:
        names = [
            "zerowrt-mediatek-filogic-netcore_n60-pro-initramfs-kernel.bin",
            "zerowrt-mediatek-filogic-netcore_n60-pro-squashfs-sysupgrade.bin",
            "zerowrt-mediatek-filogic-netcore_n60-pro.manifest",
            "config.buildinfo",
            "feeds.buildinfo",
            "profiles.json",
            "sha256sums",
            "version.buildinfo",
            "mt7981-ram-ddr3-bl2.bin",
            "mt7986-ram-ddr4-bl2.bin",
        ]
        _, tree = self._tree(names)
        out = tree / "dist"
        collected = build.collect(tree, out)
        self.assertEqual(
            {path.name for path in collected},
            {
                "zerowrt-mediatek-filogic-netcore_n60-pro-initramfs-kernel.bin",
                "zerowrt-mediatek-filogic-netcore_n60-pro-squashfs-sysupgrade.bin",
            },
        )
        self.assertEqual({path.name for path in out.iterdir()}, {path.name for path in collected})

    def test_collect_ubootmod_files(self) -> None:
        names = [
            "zerowrt-mediatek-filogic-ruijie_rg-x60-new-ubootmod-bl31-uboot.fip",
            "zerowrt-mediatek-filogic-ruijie_rg-x60-new-ubootmod-initramfs-recovery.itb",
            "zerowrt-mediatek-filogic-ruijie_rg-x60-new-ubootmod-preloader.bin",
            "zerowrt-mediatek-filogic-ruijie_rg-x60-new-ubootmod-squashfs-sysupgrade.itb",
        ]
        _, tree = self._tree(names)
        collected = build.collect(tree, tree / "dist")
        self.assertEqual({path.name for path in collected}, set(names))

    def test_no_sysupgrade_fails(self) -> None:
        _, tree = self._tree(["zerowrt-mediatek-filogic-netcore_n60-pro-initramfs-kernel.bin"])
        with self.assertRaises(util.BuildError):
            build.collect(tree, tree / "dist")

    def test_non_zerowrt_prefix_fails(self) -> None:
        _, tree = self._tree(["openwrt-mediatek-filogic-netcore_n60-pro-squashfs-sysupgrade.bin"])
        with self.assertRaises(util.BuildError):
            build.collect(tree, tree / "dist")

    def test_is_firmware(self) -> None:
        self.assertTrue(build.is_firmware("zerowrt-mediatek-filogic-x-squashfs-sysupgrade.bin"))
        self.assertTrue(build.is_firmware("zerowrt-mediatek-filogic-x-preloader.bin"))
        self.assertFalse(build.is_firmware("profiles.json"))
        self.assertFalse(build.is_firmware("config.buildinfo"))


if __name__ == "__main__":
    unittest.main()
