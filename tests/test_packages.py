from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from zerowrt_core import packages, util


class PackagesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tree = Path(self.tmp.name)
        self._make("package/new/foo/Makefile", "PKG_NAME:=foo\n$(eval $(call BuildPackage,foo))\n")
        self._make(
            "package/new/v2ray-geodata/Makefile",
            "PKG_NAME:=v2ray-geodata\n"
            "$(eval $(call BuildPackage,v2ray-geoip))\n"
            "$(eval $(call BuildPackage,v2ray-geosite))\n",
        )
        self._make("feeds/foo/Makefile", "PKG_NAME:=foo\n")
        self._make("feeds/luci/applications/foo/Makefile", "PKG_NAME:=foo\n")
        self._make("package/feeds/luci/foo/Makefile", "PKG_NAME:=foo\n")
        self._make("feeds/unrelated/Makefile", "PKG_NAME:=unrelated\n")

    def _make(self, relative: str, text: str) -> None:
        path = self.tree / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_declared_names_follow_buildpackage(self) -> None:
        names = packages.declared_package_names(self.tree / "package/new/v2ray-geodata")
        self.assertEqual(names, {"v2ray-geodata", "v2ray-geoip", "v2ray-geosite"})

    def test_new_package_names(self) -> None:
        names = packages.new_package_names(self.tree)
        self.assertIn("foo", names)
        self.assertIn("v2ray-geosite", names)

    def test_prune_removes_feed_and_installed_copies(self) -> None:
        removed = packages.prune_feed_conflicts(self.tree)
        self.assertFalse((self.tree / "feeds/foo").exists())
        self.assertFalse((self.tree / "feeds/luci/applications/foo").exists())
        self.assertFalse((self.tree / "package/feeds/luci/foo").exists())
        self.assertTrue((self.tree / "feeds/unrelated/Makefile").exists())
        self.assertEqual(len(removed), 3)

    def test_prune_is_safe_without_package_new(self) -> None:
        other = self.tree / "other"
        other.mkdir()
        self.assertEqual(packages.prune_feed_conflicts(other), [])

    def test_shared_multi_package_name_is_pruned(self) -> None:
        self._make("feeds/packages/net/v2ray-geodata/Makefile", "PKG_NAME:=v2ray-geodata\n")
        packages.prune_feed_conflicts(self.tree)
        self.assertFalse((self.tree / "feeds/packages/net/v2ray-geodata").exists())


class SingBoxCronetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tree = Path(self.tmp.name)
        self.helloworld = self.tree / "package" / "new" / "helloworld"
        self.makefile = self.helloworld / "sing-box" / "Makefile"
        self.makefile.parent.mkdir(parents=True)
        self.makefile.write_text(
            "DEPENDS:=+ca-bundle\n"
            "DEPENDS+= +kmod-netlink-diag +kmod-tun +SING_BOX_BUILD_NAIVE_OUTBOUND:libcronet\n"
            "DEPENDS+= +SING_BOX_TINY_BUILD_NAIVE_OUTBOUND:libcronet\n",
            encoding="utf-8",
        )

    def test_optional_dependency_is_removed_without_provider(self) -> None:
        packages._fix_sing_box_cronet(self.tree, self.helloworld)
        text = self.makefile.read_text(encoding="utf-8")
        self.assertNotIn("libcronet", text)
        self.assertIn("+kmod-tun", text)

    def test_provider_keeps_dependency(self) -> None:
        provider = self.tree / "package" / "new" / "libcronet" / "Makefile"
        provider.parent.mkdir(parents=True)
        provider.write_text("PKG_NAME:=libcronet\n", encoding="utf-8")
        packages._fix_sing_box_cronet(self.tree, self.helloworld)
        self.assertIn("libcronet", self.makefile.read_text(encoding="utf-8"))

    def test_unexpected_reference_fails(self) -> None:
        self.makefile.write_text(
            "DEPENDS+= +SING_BOX_BUILD_NAIVE_OUTBOUND:libcronet\n"
            "TARGET_LDFLAGS += -lother-libcronet\n",
            encoding="utf-8",
        )
        with self.assertRaises(util.BuildError):
            packages._fix_sing_box_cronet(self.tree, self.helloworld)


if __name__ == "__main__":
    unittest.main()
