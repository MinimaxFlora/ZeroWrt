from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from zerowrt_core import ota_compat, util


class OtaCompatTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tree = Path(self.tmp.name)
        self.path = self.tree / ota_compat.OTA_BIN
        self.path.parent.mkdir(parents=True)
        self.path.write_text(
            "#!/usr/bin/ucode\n"
            "import { readfile, writefile, popen, stat, statvfs, mkdir, unlink } from 'fs';\n"
            "const size = to_int(remote.size, 0);\n"
            "\n"
            "\tif (size > 0) {\n"
            "\t\tconst vfs = statvfs(DL_DIR);\n"
            "\n"
            "\t\tif (vfs != null && to_int(vfs.freesize, 0) > 0) {\n"
            "\t\t\tconst need = size + 8 * 1024 * 1024;\n"
            "\t\t}\n"
            "\t}\n"
            "\n"
            "\t// Start from a clean slate\n"
            "\tsafe_unlink(IMAGE);\n",
            encoding="utf-8",
        )

    def test_patch_removes_statvfs(self) -> None:
        ota_compat.patch(self.tree)
        text = self.path.read_text(encoding="utf-8")
        self.assertNotIn("statvfs", text)
        self.assertIn("Free-space preflight omitted", text)
        self.assertIn("const size = to_int", text)
        ota_compat.patch(self.tree)
        self.assertEqual(text, self.path.read_text(encoding="utf-8"))

    def test_missing_backend_fails(self) -> None:
        self.path.unlink()
        with self.assertRaises(util.BuildError):
            ota_compat.patch(self.tree)


if __name__ == "__main__":
    unittest.main()
