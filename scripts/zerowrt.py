#!/usr/bin/env python3
"""ZeroWrt build CLI.

The GitHub Actions workflow only calls these subcommands.  All firmware
customisation, package replacement, configuration and OTA work is implemented
in Python; the reusable runner preparation (disk, apt dependencies, LLVM) lives
in :mod:`zerowrt_core.sysops`.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from zerowrt_core import (  # noqa: E402
    build,
    cache,
    config,
    customize,
    ota,
    packages,
    profiles,
    settings,
    source,
    state,
    sysops,
    util,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TREE = Path(os.environ.get("ZEROWRT_SOURCE_DIR") or "/builder/source")
DEFAULT_ASSETS = REPO_ROOT / "assets"


def _jobs(value: str | None) -> int:
    if value:
        return max(1, int(value))
    return max(1, os.cpu_count() or 2)


def _settings(args: argparse.Namespace) -> settings.BuildSettings:
    current = settings.BuildSettings.from_environment()
    return current.with_overrides(
        device=getattr(args, "device", None),
        lan_ip=getattr(args, "lan_ip", None),
        root_password=getattr(args, "root_password", None),
        wifi_name=getattr(args, "wifi_name", None),
        wifi_password=getattr(args, "wifi_password", None),
        dist_name=getattr(args, "dist_name", None),
        ota_url=getattr(args, "ota_url", None),
    )


def _export_env(values: dict[str, str]) -> None:
    path = os.environ.get("GITHUB_ENV")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def cmd_system_free_disk(args: argparse.Namespace) -> None:
    sysops.free_disk(
        str(Path(args.build_dir)),
        reserve_gb=args.reserve_gb,
        swap_size_gb=args.swap_gb,
        min_free_gb=args.min_free_gb,
    )


def cmd_system_install_deps(args: argparse.Namespace) -> None:
    sysops.install_deps(docker=args.docker)


def cmd_system_install_llvm(args: argparse.Namespace) -> None:
    sysops.install_llvm(version=args.version, strict=args.strict)


def cmd_source_clone(args: argparse.Namespace) -> None:
    device = args.device or os.environ.get("ZEROWRT_DEVICE") or profiles.DEFAULT_DEVICE
    info = source.clone_source(Path(args.dest), device=device, ref=args.ref)
    _export_env(
        {
            "ZEROWRT_SOURCE_REPO": info["source_repo"],
            "ZEROWRT_SOURCE_REF": info["source_ref"],
            "ZEROWRT_SOURCE_COMMIT": info["source_commit"],
            "ZEROWRT_BUILD_DATE": str(info["build_date"]),
            "ZEROWRT_DEVICE": info["device"],
        }
    )


def cmd_source_feeds_update(args: argparse.Namespace) -> None:
    source.update_feeds(Path(args.tree))


def cmd_source_feeds_install(args: argparse.Namespace) -> None:
    source.install_feeds(Path(args.tree))


def cmd_source_customize(args: argparse.Namespace) -> None:
    build_settings = _settings(args)
    util.log(
        f"device {build_settings.device}, LAN {build_settings.effective_ip()}, "
        f"WiFi {build_settings.ssid('2g')} / {build_settings.ssid('5g')}"
    )
    customize.apply(
        Path(args.tree),
        build_settings,
        assets=Path(args.assets),
        repo_root=REPO_ROOT,
    )


def cmd_packages_add(args: argparse.Namespace) -> None:
    packages.add_external_packages(Path(args.tree))


def cmd_config_apply(args: argparse.Namespace) -> None:
    device = args.device or os.environ.get("ZEROWRT_DEVICE") or profiles.DEFAULT_DEVICE
    dist_name = args.dist_name or os.environ.get("ZEROWRT_DIST") or settings.DEFAULT_DIST_NAME
    config.apply(
        Path(args.tree),
        device=device,
        dist_name=dist_name,
    )


def cmd_config_preview(args: argparse.Namespace) -> None:
    text = config.preview(Path(args.tree), device=args.device)
    if args.out:
        util.write_text(Path(args.out), text)
        util.log(f"seed .config written to {args.out}")
    else:
        sys.stdout.write(text)


def cmd_config_generate(args: argparse.Namespace) -> None:
    generated = config.generate_all(Path(args.tree), Path(args.out))
    util.log(f"generated {len(generated)} device config(s) in {args.out}")


def cmd_ota_embed(args: argparse.Namespace) -> None:
    tree = Path(args.tree)
    info = state.read(tree)
    api_url = args.api_url or os.environ.get("ZEROWRT_OTA_URL") or settings.DEFAULT_OTA_URL
    metadata = ota.embed(
        tree,
        info=info,
        api_url=api_url,
        download_proxy=args.download_proxy,
        emit=Path(args.emit) if args.emit else None,
    )
    util.log(f"OTA metadata for {metadata['device']} {metadata['version']}")


def cmd_ota_index(args: argparse.Namespace) -> None:
    tree = Path(args.tree)
    info = state.read(tree)
    tag = args.tag or profiles.RELEASE_TAG
    if (not args.repo or not tag) and not args.url_base:
        raise util.BuildError("ota index needs --repo/--tag or --url-base")
    ota.generate_index(
        Path(args.dist),
        info=info,
        repo=args.repo,
        tag=tag,
        existing=Path(args.existing) if args.existing else None,
        history=Path(args.history) if args.history else None,
        changelog=args.changelog,
        url_base=args.url_base,
    )


def cmd_ota_publish(args: argparse.Namespace) -> None:
    tree = Path(args.tree)
    info = state.read(tree)
    repo = args.repo or os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        raise util.BuildError("ota publish needs --repo or GITHUB_REPOSITORY")
    tag = args.tag or profiles.RELEASE_TAG
    ota.publish(
        dist=Path(args.dist),
        info=info,
        repo=repo,
        tag=tag,
        site=Path(args.site) if args.site else None,
        cname=args.cname,
        out=Path(args.out) if args.out else None,
        existing_source=Path(args.existing) if args.existing else None,
        history_source=Path(args.history) if args.history else None,
    )


def cmd_build_download(args: argparse.Namespace) -> None:
    build.download_sources(Path(args.tree), _jobs(args.jobs))


def cmd_build_compile(args: argparse.Namespace) -> None:
    build.compile_firmware(Path(args.tree), _jobs(args.jobs))


def cmd_build_collect(args: argparse.Namespace) -> None:
    build.collect(Path(args.tree), Path(args.out))


def cmd_cache_restore(args: argparse.Namespace) -> None:
    repo = args.repo or os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        raise util.BuildError("cache restore needs --repo or GITHUB_REPOSITORY")
    cache.restore(Path(args.tree), repo=repo, release=args.release, optional=not args.required)


def cmd_cache_save(args: argparse.Namespace) -> None:
    repo = args.repo or os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        raise util.BuildError("cache save needs --repo or GITHUB_REPOSITORY")
    cache.save(Path(args.tree), repo=repo, release=args.release)


def _add_tree(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--tree", default=str(DEFAULT_TREE), help="path to the OpenWrt source tree")


def _add_build_settings(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--device", default=None, help="device profile (default: ZEROWRT_DEVICE)")
    parser.add_argument(
        "--lan-ip",
        default=None,
        help="LAN IP override; empty uses the unified default 10.0.0.1",
    )
    parser.add_argument(
        "--root-password",
        default=None,
        help="root password written to /etc/shadow (default: ZEROWRT_ROOT_PASSWORD or 'password')",
    )
    parser.add_argument("--wifi-name", default=None, help="WiFi name prefix (default: ZeroWrt)")
    parser.add_argument("--wifi-password", default=None, help="WiFi password, 8-63 characters")
    parser.add_argument("--dist-name", default=None, help="distribution name (default: ZeroWrt)")
    parser.add_argument("--ota-url", default=None, help="default OTA index URL baked into the image")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zerowrt",
        description="ZeroWrt firmware build helper (MT798x, Python)",
    )
    parser.add_argument("--version", action="version", version="zerowrt 3.0.0")
    sub = parser.add_subparsers(dest="command", required=True)

    system = sub.add_parser("system", help="prepare the GitHub Actions runner")
    system_sub = system.add_subparsers(dest="system_command", required=True)

    free_disk = system_sub.add_parser("free-disk", help="remove unused software and merge disks")
    free_disk.add_argument("--build-dir", default="/builder")
    free_disk.add_argument("--swap-gb", type=int, default=4)
    free_disk.add_argument("--reserve-gb", type=int, default=6)
    free_disk.add_argument("--min-free-gb", type=float, default=50.0)
    free_disk.set_defaults(func=cmd_system_free_disk)

    deps = system_sub.add_parser("install-deps", help="install OpenWrt build dependencies")
    deps.add_argument("--docker", action="store_true", help="also install Docker")
    deps.set_defaults(func=cmd_system_install_deps)

    llvm = system_sub.add_parser("install-llvm", help="install the Clang toolchain")
    llvm.add_argument("--version", default=sysops.CLANG_VERSION)
    llvm.add_argument("--strict", action="store_true", help="fail when the download fails")
    llvm.set_defaults(func=cmd_system_install_llvm)

    src = sub.add_parser("source", help="upstream source tree operations")
    src_sub = src.add_subparsers(dest="source_command", required=True)

    clone = src_sub.add_parser("clone", help="clone the upstream source tree")
    clone.add_argument("--dest", default=str(DEFAULT_TREE))
    clone.add_argument("--device", default=None, help="device profile (default: ZEROWRT_DEVICE)")
    clone.add_argument("--ref", default=None, help="branch/tag override")
    clone.set_defaults(func=cmd_source_clone)

    feeds_update = src_sub.add_parser("feeds-update", help="fetch every OpenWrt feed")
    _add_tree(feeds_update)
    feeds_update.set_defaults(func=cmd_source_feeds_update)

    feeds_install = src_sub.add_parser("feeds-install", help="install feeds")
    _add_tree(feeds_install)
    feeds_install.set_defaults(func=cmd_source_feeds_install)

    customize_cmd = src_sub.add_parser("customize", help="apply version, IP, WiFi, banner and Argon")
    _add_tree(customize_cmd)
    _add_build_settings(customize_cmd)
    customize_cmd.add_argument("--assets", default=str(DEFAULT_ASSETS))
    customize_cmd.set_defaults(func=cmd_source_customize)

    pkg = sub.add_parser("packages", help="add external packages")
    pkg_sub = pkg.add_subparsers(dest="packages_command", required=True)
    pkg_add = pkg_sub.add_parser("add", help="clone PassWall, OpenClash, Argon, OTA and Go")
    _add_tree(pkg_add)
    pkg_add.set_defaults(func=cmd_packages_add)

    config_cmd = sub.add_parser("config", help="install or generate per-device diffconfigs")
    config_sub = config_cmd.add_subparsers(dest="config_command", required=True)
    config_apply = config_sub.add_parser("apply", help="copy one device diffconfig and run make defconfig")
    _add_tree(config_apply)
    config_apply.add_argument("--device", default=None, help="device profile (default: ZEROWRT_DEVICE)")
    config_apply.add_argument("--dist-name", default=None, help="distribution name (default: ZeroWrt)")
    config_apply.set_defaults(func=cmd_config_apply)

    config_preview = config_sub.add_parser(
        "preview",
        help="print the pre-defconfig .config for one device without running make",
    )
    _add_tree(config_preview)
    config_preview.add_argument("--device", default=profiles.DEFAULT_DEVICE)
    config_preview.add_argument("--out", default="", help="write to this file instead of stdout")
    config_preview.set_defaults(func=cmd_config_preview)

    config_generate = config_sub.add_parser(
        "generate",
        help="generate diffconfig fragments under configs/ for every device",
    )
    _add_tree(config_generate)
    config_generate.add_argument("--out", default="configs")
    config_generate.set_defaults(func=cmd_config_generate)

    ota_cmd = sub.add_parser("ota", help="embed OTA metadata, build the index and publish it")
    ota_sub = ota_cmd.add_subparsers(dest="ota_command", required=True)

    ota_embed = ota_sub.add_parser("embed", help="write /etc/ota/build.json into the image")
    _add_tree(ota_embed)
    ota_embed.add_argument("--api-url", default=None, help="default update index URL")
    ota_embed.add_argument("--download-proxy", default="", help="default GitHub download proxy")
    ota_embed.add_argument("--emit", default="", help="also write the metadata to this file")
    ota_embed.set_defaults(func=cmd_ota_embed)

    ota_index = ota_sub.add_parser("index", help="write ota.json for the collected artifacts")
    _add_tree(ota_index)
    ota_index.add_argument("--dist", default="dist")
    ota_index.add_argument("--repo", default="", help="GitHub repository owner/name")
    ota_index.add_argument("--tag", default="", help=f"release tag (default: {profiles.RELEASE_TAG})")
    ota_index.add_argument("--existing", default="", help="existing ota.json to merge")
    ota_index.add_argument("--history", default="", help="history.json to update")
    ota_index.add_argument("--changelog", default="", help="override the generated changelog")
    ota_index.add_argument("--url-base", default="", help="asset URL prefix instead of GitHub Releases")
    ota_index.set_defaults(func=cmd_ota_index)

    ota_publish = ota_sub.add_parser("publish", help="render ota.json and the download page")
    _add_tree(ota_publish)
    ota_publish.add_argument("--dist", default="dist")
    ota_publish.add_argument("--repo", default="", help="GitHub repository owner/name")
    ota_publish.add_argument("--tag", default="", help=f"release tag (default: {profiles.RELEASE_TAG})")
    ota_publish.add_argument("--site", default="", help="static download page directory")
    ota_publish.add_argument(
        "--cname",
        default=settings.DEFAULT_OTA_CNAME,
        help=f"custom domain written to CNAME (default: {settings.DEFAULT_OTA_CNAME})",
    )
    ota_publish.add_argument("--out", default="", help="output directory")
    ota_publish.add_argument("--existing", default="", help="existing ota.json to merge")
    ota_publish.add_argument("--history", default="", help="existing history.json to append")
    ota_publish.set_defaults(func=cmd_ota_publish)

    build_cmd = sub.add_parser("build", help="download, compile and collect")
    build_sub = build_cmd.add_subparsers(dest="build_command", required=True)
    download = build_sub.add_parser("download")
    _add_tree(download)
    download.add_argument("--jobs", default=None)
    download.set_defaults(func=cmd_build_download)

    compile_ = build_sub.add_parser("compile")
    _add_tree(compile_)
    compile_.add_argument("--jobs", default=None)
    compile_.set_defaults(func=cmd_build_compile)

    collect = build_sub.add_parser("collect")
    _add_tree(collect)
    collect.add_argument("--out", default="dist")
    collect.set_defaults(func=cmd_build_collect)

    cache_cmd = sub.add_parser("cache", help="toolchain cache in a GitHub release")
    cache_sub = cache_cmd.add_subparsers(dest="cache_command", required=True)
    cache_restore = cache_sub.add_parser("restore", help="restore build_dir/dl/staging_dir/tmp")
    _add_tree(cache_restore)
    cache_restore.add_argument("--repo", default="")
    cache_restore.add_argument("--release", default=cache.DEFAULT_RELEASE)
    cache_restore.add_argument("--required", action="store_true", help="fail when no cache exists")
    cache_restore.set_defaults(func=cmd_cache_restore)

    cache_save = cache_sub.add_parser("save", help="pack and upload the toolchain cache")
    _add_tree(cache_save)
    cache_save.add_argument("--repo", default="")
    cache_save.add_argument("--release", default=cache.DEFAULT_RELEASE)
    cache_save.set_defaults(func=cmd_cache_save)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except util.BuildError as exc:
        util.header("Build failed")
        for line in str(exc).splitlines():
            print(line, flush=True)
        first = str(exc).splitlines()[0] if str(exc) else "build failed"
        print(f"::error::{first}", flush=True)
        return 1
    except KeyboardInterrupt:
        print("::error::interrupted", flush=True)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
