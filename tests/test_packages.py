from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from zerowrt_core import packages


class PackagesTest(unittest.TestCase):
    def test_declared_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "luci-app-demo"
            directory.mkdir()
            (directory / "Makefile").write_text(
                "PKG_NAME:=luci-app-demo\n"
                "define Package/$(PKG_NAME)\nendef\n"
                "$(eval $(call BuildPackage,$(PKG_NAME)))\n",
                encoding="utf-8",
            )
            names = packages.declared_package_names(directory)
            self.assertIn("luci-app-demo", names)

    def test_prune_feed_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            source = tree / "package" / "new" / "xray-core"
            source.mkdir(parents=True)
            (source / "Makefile").write_text("PKG_NAME:=xray-core\n", encoding="utf-8")
            feed = tree / "feeds" / "packages" / "net" / "xray-core"
            feed.mkdir(parents=True)
            (feed / "Makefile").write_text("PKG_NAME:=xray-core\n", encoding="utf-8")
            link = tree / "package" / "feeds" / "packages" / "xray-core"
            link.parent.mkdir(parents=True)
            try:
                link.symlink_to(feed)
            except OSError:
                self.skipTest("creating symlinks is not permitted on this platform")

            removed = packages.prune_feed_conflicts(tree)
            self.assertFalse(feed.exists())
            self.assertFalse(link.exists())
            self.assertTrue(removed)

    def test_new_package_names_scans_nested_makefiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            nested = tree / "package" / "new" / "repo" / "luci-app-demo"
            nested.mkdir(parents=True)
            (nested / "Makefile").write_text("PKG_NAME:=luci-app-demo\n", encoding="utf-8")
            self.assertIn("luci-app-demo", packages.new_package_names(tree))


if __name__ == "__main__":
    unittest.main()
