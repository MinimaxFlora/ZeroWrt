from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from zerowrt_core import cache, util


class CacheTest(unittest.TestCase):
    def test_asset_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp)
            (staging / "toolchain-aarch64_cortex-a53_gcc-14.3.0_musl").mkdir()
            name = cache.asset_name(staging)
            self.assertEqual(name, "toolchain_musl_aarch64_cortex-a53_gcc-14.tar.zst")

    def test_asset_name_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(util.BuildError):
            cache.asset_name(Path(tmp))


if __name__ == "__main__":
    unittest.main()
