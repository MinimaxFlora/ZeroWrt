from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from zerowrt_core import ota, util


class OtaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dist = self.root / "dist"
        self.dist.mkdir()
        self.image = self.dist / "zerowrt-mediatek-filogic-netcore_n60-pro-squashfs-sysupgrade.bin"
        self.image.write_bytes(b"firmware-image")
        (self.dist / "zerowrt-mediatek-filogic-netcore_n60-pro-initramfs-kernel.bin").write_bytes(b"initramfs")
        self.info = {
            "dist": "ZeroWrt",
            "device": "netcore_n60-pro",
            "profile": "netcore_n60-pro",
            "artifact": "netcore_n60-pro",
            "target": "mediatek/filogic",
            "board": "mediatek",
            "subtarget": "filogic",
            "device_vendor": "Netcore",
            "device_model": "N60 Pro",
            "device_variant": "",
            "version": "20261108",
            "build_date": 1762524000,
            "source_repo": "Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly",
            "source_commit": "abcdef0123456789",
        }

    def test_select_image_ignores_initramfs(self) -> None:
        self.assertEqual(ota.select_image(self.dist), self.image)

    def test_generate_index(self) -> None:
        index = ota.generate_index(
            self.dist,
            info=self.info,
            repo="owner/repo",
            tag="mediatek_filogic",
        )
        self.assertEqual(index["schema"], 2)
        entry = index["devices"]["netcore_n60-pro"]
        self.assertEqual(entry["sha256"], util.sha256_file(self.image))
        self.assertEqual(entry["size"], self.image.stat().st_size)
        self.assertEqual(entry["target"], "mediatek/filogic")
        self.assertIn("Netcore N60 Pro", entry["label"])
        self.assertIn(
            "https://github.com/owner/repo/releases/download/mediatek_filogic/",
            entry["url"],
        )
        self.assertTrue((self.dist / "ota.json").exists())

    def test_generate_index_merges_existing(self) -> None:
        existing = self.root / "ota.json"
        existing.write_text(
            json.dumps(
                {
                    "schema": 2,
                    "devices": {
                        "ruijie_rg-x60-new": {
                            "url": "https://example.com/a.bin",
                            "sha256": "0" * 64,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        index = ota.generate_index(
            self.dist,
            info=self.info,
            repo="owner/repo",
            tag="mediatek_filogic",
            existing=existing,
        )
        self.assertIn("ruijie_rg-x60-new", index["devices"])
        self.assertIn("netcore_n60-pro", index["devices"])

    def test_generate_index_rejects_corrupt_existing(self) -> None:
        existing = self.root / "ota.json"
        existing.write_text("{not-json", encoding="utf-8")
        with self.assertRaises(util.BuildError):
            ota.generate_index(
                self.dist,
                info=self.info,
                repo="owner/repo",
                tag="mediatek_filogic",
                existing=existing,
            )

    def test_publish_merges_live_index_and_history(self) -> None:
        site = self.root / "site"
        site.mkdir()
        (site / "index.html").write_text("page", encoding="utf-8")
        existing = self.root / "existing.json"
        existing.write_text(
            json.dumps({"schema": 2, "devices": {"other_device": {"version": "20260101"}}}),
            encoding="utf-8",
        )
        history = self.root / "history.json"
        history.write_text(
            json.dumps({"schema": 1, "releases": [{"version": "20260101", "device": "other_device", "build_date": 1}]}),
            encoding="utf-8",
        )
        index = ota.publish(
            dist=self.dist,
            info=self.info,
            repo="owner/repo",
            tag="mediatek_filogic",
            site=site,
            out=self.root / "merged",
            existing_source=existing,
            history_source=history,
        )
        self.assertIn("other_device", index["devices"])
        self.assertIn("netcore_n60-pro", index["devices"])
        merged_history = json.loads((self.root / "merged" / "history.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(merged_history["releases"]), 2)

    def test_publish_no_push(self) -> None:
        site = self.root / "site"
        site.mkdir()
        (site / "index.html").write_text("MinimaxFlora/ZeroWrt", encoding="utf-8")
        (site / "CNAME").write_text("old.example\n", encoding="utf-8")
        out = self.root / "out"
        index = ota.publish(
            dist=self.dist,
            info=self.info,
            repo="owner/repo",
            tag="mediatek_filogic",
            site=site,
            out=out,
        )
        self.assertIn("netcore_n60-pro", index["devices"])
        self.assertTrue((out / "ota.json").exists())
        self.assertTrue((out / "index.html").exists())
        self.assertFalse((out / "CNAME").exists())
        self.assertIn("owner/repo", (out / "index.html").read_text(encoding="utf-8"))

    def test_embed_metadata(self) -> None:
        tree = self.root / "tree"
        (tree / "package/base-files/files/etc").mkdir(parents=True)
        metadata = ota.embed(
            tree,
            info=self.info,
            api_url="https://example.com/ota.json",
        )
        self.assertEqual(metadata["device"], "netcore_n60-pro")
        build_json = json.loads((tree / "package/base-files/files/etc/ota/build.json").read_text(encoding="utf-8"))
        self.assertEqual(build_json["version"], "20261108")
        defaults = tree / "package/base-files/files/etc/uci-defaults/90-luci-app-ota"
        self.assertTrue(defaults.exists())
        self.assertIn("https://example.com/ota.json", defaults.read_text(encoding="utf-8"))
        self.assertTrue((tree / "version.date").exists())


if __name__ == "__main__":
    unittest.main()
