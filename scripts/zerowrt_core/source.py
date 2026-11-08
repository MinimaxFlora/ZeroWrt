"""Source tree handling: clone the MT798x tree, update feeds and verify them."""

from __future__ import annotations

import os
import time
from pathlib import Path

from . import profiles, state, util


def _verify_tree(tree: Path) -> None:
    tree = Path(tree)
    required = {
        "rules.mk": tree / "rules.mk",
        "include/version.mk": tree / "include" / "version.mk",
        "target/linux/mediatek/image/filogic.mk": tree / "target/linux/mediatek/image/filogic.mk",
        "defconfig/mt7975-ipailna-high-power.config": tree / "defconfig/mt7975-ipailna-high-power.config",
        "package/base-files/files/bin/config_generate": tree / "package/base-files/files/bin/config_generate",
        "package/mtk/applications/mtwifi-cfg/files/mtwifi.sh": (
            tree / "package/mtk/applications/mtwifi-cfg/files/mtwifi.sh"
        ),
    }
    missing = [name for name, path in required.items() if not path.exists()]
    if missing:
        raise util.BuildError(
            f"{tree} does not look like the expected ImmortalWrt MT798x tree; missing:\n  - " + "\n  - ".join(missing)
        )


def clone_source(
    tree: Path,
    *,
    device: str,
    ref: str | None = None,
    repo: str | None = None,
) -> dict:
    """Clone the source tree and record its identity in ``.zerowrt-info.json``."""
    profile = profiles.require(device)
    source = profiles.source(profile)
    repo = (repo or os.environ.get("ZEROWRT_SOURCE_REPO") or source.repo).strip()
    ref = (ref or os.environ.get("ZEROWRT_SOURCE_REF") or source.ref).strip()

    util.header(f"Cloning {source.label}")
    util.log(f"repository: {repo}")
    util.log(f"reference: {ref}")
    sha = util.clone(repo, Path(tree), ref=ref, token=None, depth=1)
    _verify_tree(Path(tree))
    util.log(f"checked out commit {sha[:12]}")

    build_date = int(time.time())
    data = {
        "dist": "ZeroWrt",
        "profile": profile.name,
        "artifact": profile.name,
        "source": profile.source,
        "source_label": source.label,
        "source_repo": repo,
        "source_ref": ref,
        "source_commit": sha,
        "board": profile.board,
        "subtarget": profile.subtarget,
        "target": profile.target,
        "device": profile.device,
        "dt_model": "",
        "device_vendor": profile.vendor,
        "device_model": profile.model,
        "device_variant": profile.variant,
        "layout": profile.layout,
        "default_lan_ip": profile.lan_ip,
        "build_date": build_date,
        "version": state.version_for(build_date),
    }
    state.write(Path(tree), data)
    return data


def update_feeds(tree: Path) -> None:
    tree = Path(tree)
    feeds = tree / "scripts" / "feeds"
    if not feeds.exists():
        raise util.BuildError(f"feeds script not found: {feeds}")

    util.header("Updating OpenWrt feeds")
    code, _ = util.run(
        [str(feeds), "update", "-a"],
        cwd=tree,
        check=False,
        log_path=tree / "feeds-update.log",
    )
    missing = [name for name in ("luci", "packages") if not (tree / "feeds" / name).exists()]
    if missing:
        tail = ""
        log_path = tree / "feeds-update.log"
        if log_path.exists():
            tail = "\n".join(util.read_text(log_path).splitlines()[-40:])
        raise util.BuildError("feed update did not provide: " + ", ".join(missing) + "\n" + tail)
    if code != 0:
        tail = ""
        log_path = tree / "feeds-update.log"
        if log_path.exists():
            tail = "\n".join(util.read_text(log_path).splitlines()[-40:])
        raise util.BuildError(f"feeds update failed ({code})\n{tail}")


def install_feeds(tree: Path) -> None:
    tree = Path(tree)
    feeds = tree / "scripts" / "feeds"
    if not feeds.exists():
        raise util.BuildError(f"feeds script not found: {feeds}")

    util.header("Installing OpenWrt feeds")
    code, _ = util.run(
        [str(feeds), "install", "-a"],
        cwd=tree,
        check=False,
        log_path=tree / "feeds-install.log",
    )
    if code != 0:
        tail = ""
        log_path = tree / "feeds-install.log"
        if log_path.exists():
            tail = "\n".join(util.read_text(log_path).splitlines()[-40:])
        raise util.BuildError(f"feeds install failed ({code})\n{tail}")

    required = {
        "luci-compat": tree / "package/feeds/luci/luci-compat",
        "lyaml": tree / "package/feeds/packages/lyaml",
        "ttyd": tree / "package/feeds/packages/ttyd",
        "3proxy": tree / "package/feeds/packages/3proxy",
    }
    missing = [name for name, path in required.items() if not path.exists()]
    if missing:
        tail = ""
        log_path = tree / "feeds-install.log"
        if log_path.exists():
            tail = "\n".join(util.read_text(log_path).splitlines()[-40:])
        raise util.BuildError("feeds install did not provide: " + ", ".join(missing) + "\n" + tail)

    util.log("feeds installed")
