from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from zerowrt_core import util


class UtilTest(unittest.TestCase):
    def test_download_rejects_non_http_scheme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(util.BuildError):
            util.download("file:///etc/passwd", Path(tmp) / "x")

    def test_sha256_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data"
            path.write_bytes(b"abc")
            self.assertEqual(
                util.sha256_file(path),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )

    def test_remove_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tree"
            path.mkdir()
            (path / "file").write_text("x", encoding="utf-8")
            self.assertTrue(util.remove_path(path))
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
