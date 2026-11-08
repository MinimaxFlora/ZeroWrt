from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zerowrt_core import source, util


class SourceTest(unittest.TestCase):
    def _tree(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        tree = Path(tmp.name)
        (tree / "scripts").mkdir(parents=True)
        (tree / "scripts" / "feeds").write_text("#!/bin/sh\n", encoding="utf-8")
        (tree / "feeds" / "luci").mkdir(parents=True)
        (tree / "feeds" / "packages").mkdir(parents=True)
        return tree

    def test_update_feeds_fails_on_nonzero(self) -> None:
        tree = self._tree()
        with mock.patch.object(source.util, "run", return_value=(1, "")), self.assertRaises(util.BuildError):
            source.update_feeds(tree)

    def test_install_feeds_fails_on_nonzero(self) -> None:
        tree = self._tree()
        with mock.patch.object(source.util, "run", return_value=(1, "")), self.assertRaises(util.BuildError):
            source.install_feeds(tree)

    def test_update_feeds_reports_missing_feed(self) -> None:
        tree = self._tree()
        (tree / "feeds" / "luci").rmdir()
        with mock.patch.object(source.util, "run", return_value=(0, "")), self.assertRaises(util.BuildError):
            source.update_feeds(tree)


if __name__ == "__main__":
    unittest.main()
