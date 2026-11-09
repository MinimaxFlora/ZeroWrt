"""Compatibility patch for luci-app-ota on the 24.10 ucode runtime.

The pinned OTA source imports ``statvfs`` from the ucode ``fs`` module.  The
OpenWrt 24.10 ``ucode-mod-fs`` package does not export that symbol, so the whole
``/usr/bin/ota`` script aborts before printing any JSON.  Remove only the
optional free-space preflight; the downloader still checks the actual write.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import util

OTA_BIN = Path("package/new/luci-app-ota/root/usr/bin/ota")
OLD_IMPORT = "import { readfile, writefile, popen, stat, statvfs, mkdir, unlink } from 'fs';"
NEW_IMPORT = "import { readfile, writefile, popen, stat, mkdir, unlink } from 'fs';"
FREE_SPACE_COMMENT = "\t// Free-space preflight omitted: 24.10 ucode fs lacks the required API.\n"


def patch(tree: Path) -> None:
    tree = Path(tree)
    path = tree / OTA_BIN
    if not path.is_file():
        raise util.BuildError(f"OTA backend not found: {path}")

    text = util.read_text(path)
    if "statvfs" not in text:
        util.log("OTA: ucode statvfs compatibility already applied")
        return

    if OLD_IMPORT not in text:
        raise util.BuildError(f"{OTA_BIN}: unexpected fs import; cannot remove statvfs")
    text = text.replace(OLD_IMPORT, NEW_IMPORT, 1)

    pattern = re.compile(
        r"\n\tif \(size > 0\) \{\n.*?\n\t\}\n\n(?=\t// Start from a clean slate)",
        re.S,
    )
    text, count = pattern.subn("\n" + FREE_SPACE_COMMENT, text, count=1)
    if count != 1:
        raise util.BuildError(f"{OTA_BIN}: free-space preflight block was not found")

    util.write_text(path, text)
    final = util.read_text(path)
    if "statvfs" in final:
        raise util.BuildError(f"{OTA_BIN}: statvfs is still referenced")
    util.log("OTA: removed unsupported statvfs free-space preflight")
