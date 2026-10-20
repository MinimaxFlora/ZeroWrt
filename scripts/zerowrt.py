#!/usr/bin/env python3
"""ZeroWrt build CLI.

Every firmware customisation is implemented in Python so the GitHub Actions
workflow only needs to call these subcommands.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from zerowrt_core import build, configgen, packages, settings, source, sysops, util  # noqa: E402

DEFAULT_TREE = Path(os.environ.get("LEDE_DIR") or "/builder/lede")
DEFAULT_ASSETS = Path(__file__).resolve().parent.parent / "assets"


def _jobs(value: str | None) -> int:
    if value:
        return max(1, int(value))
    return max(1, os.cpu_count() or 2)


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
    sysops.install_llvm(strict=args.strict)


def cmd_source_clone(args: argparse.Namespace) -> None:
    ref = (args.ref or os.environ.get("LEDE_REF") or source.DEFAULT_REF).strip()
    sha = source.clone_lede(Path(args.dest), ref=ref)
    github_env = os.environ.get("GITHUB_ENV")
    if github_env:
        with open(github_env, "a", encoding="utf-8") as handle:
            handle.write(f"LEDE_COMMIT={sha}\n")
            handle.write(f"LEDE_REF={ref}\n")


def cmd_source_feeds(args: argparse.Namespace) -> None:
    source.update_feeds(Path(args.tree))


def cmd_source_customize(args: argparse.Namespace) -> None:
    current = settings.BuildSettings.from_environment()
    build_settings = settings.BuildSettings(
        ip=args.ip or current.ip,
        wifi_name=args.wifi_name or current.wifi_name,
        wifi_password=current.wifi_password if args.wifi_password is None else args.wifi_password,
        device=current.device,
    ).validated()
    util.log(
        f"LAN IP {build_settings.ip}, WiFi {build_settings.ssid('2g')} / "
        f"{build_settings.ssid('5g')}, device {build_settings.device}"
    )
    source.apply_core_customisations(Path(args.tree), build_settings)


def cmd_packages_add(args: argparse.Namespace) -> None:
    packages.add_external_packages(Path(args.tree))
    packages.apply_argon_branding(Path(args.tree), Path(args.assets))


def cmd_config_generate(args: argparse.Namespace) -> None:
    device = args.device or settings.BuildSettings.from_environment().device
    configgen.generate(Path(args.tree), device)


def cmd_build_download(args: argparse.Namespace) -> None:
    build.download_sources(Path(args.tree), _jobs(args.jobs))


def cmd_build_compile(args: argparse.Namespace) -> None:
    build.compile_firmware(Path(args.tree), _jobs(args.jobs))


def cmd_build_collect(args: argparse.Namespace) -> None:
    build.collect(Path(args.tree), Path(args.out))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zerowrt",
        description="ZeroWrt firmware build helper",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    system = sub.add_parser("system", help="prepare the GitHub Actions runner")
    system_sub = system.add_subparsers(dest="system_command", required=True)

    free_disk = system_sub.add_parser("free-disk", help="remove unused software and merge disks")
    free_disk.add_argument("--build-dir", default="/builder")
    free_disk.add_argument("--swap-gb", type=int, default=4)
    free_disk.add_argument("--reserve-gb", type=int, default=2)
    free_disk.add_argument(
        "--min-free-gb",
        type=float,
        default=50.0,
        help="skip cleanup/merge when this much space is already free",
    )
    free_disk.set_defaults(func=cmd_system_free_disk)

    deps = system_sub.add_parser("install-deps", help="install OpenWrt build dependencies")
    deps.add_argument("--docker", action="store_true", help="also install Docker")
    deps.set_defaults(func=cmd_system_install_deps)

    llvm = system_sub.add_parser("install-llvm", help="install the Clang toolchain")
    llvm.add_argument("--strict", action="store_true", help="fail when the download fails")
    llvm.set_defaults(func=cmd_system_install_llvm)

    src = sub.add_parser("source", help="LEDE source tree operations")
    src_sub = src.add_subparsers(dest="source_command", required=True)

    clone = src_sub.add_parser("clone", help="clone the private LEDE tree")
    clone.add_argument("--dest", default=str(DEFAULT_TREE))
    clone.add_argument("--ref", default=None)
    clone.set_defaults(func=cmd_source_clone)

    feeds = src_sub.add_parser("feeds", help="update feeds and drop conflicting packages")
    feeds.add_argument("--tree", default=str(DEFAULT_TREE))
    feeds.set_defaults(func=cmd_source_feeds)

    customize = src_sub.add_parser("customize", help="apply version, IP and WiFi patches")
    customize.add_argument("--tree", default=str(DEFAULT_TREE))
    customize.add_argument("--ip", default=None, help="LAN IP (default: ZEROWRT_IP or 10.0.0.1)")
    customize.add_argument("--wifi-name", default=None, help="WiFi name prefix (default: ZEROWRT_WIFI_NAME)")
    customize.add_argument(
        "--wifi-password",
        default=None,
        help="WiFi password, 8-63 characters (default: ZEROWRT_WIFI_PASSWORD)",
    )
    customize.set_defaults(func=cmd_source_customize)

    pkg = sub.add_parser("packages", help="add external packages and theme branding")
    pkg_sub = pkg.add_subparsers(dest="packages_command", required=True)
    add = pkg_sub.add_parser("add", help="clone Argon, PassWall and OpenClash")
    add.add_argument("--tree", default=str(DEFAULT_TREE))
    add.add_argument("--assets", default=str(DEFAULT_ASSETS))
    add.set_defaults(func=cmd_packages_add)

    config = sub.add_parser("config", help="generate .config")
    config_sub = config.add_subparsers(dest="config_command", required=True)
    generate = config_sub.add_parser("generate", help="write .config and run defconfig")
    generate.add_argument("--tree", default=str(DEFAULT_TREE))
    generate.add_argument("--device", default=None, help="device profile (default: ZEROWRT_DEVICE or ruijie_rg-x60)")
    generate.set_defaults(func=cmd_config_generate)

    build_cmd = sub.add_parser("build", help="download, compile and collect")
    build_sub = build_cmd.add_subparsers(dest="build_command", required=True)

    download = build_sub.add_parser("download")
    download.add_argument("--tree", default=str(DEFAULT_TREE))
    download.add_argument("--jobs", default=None)
    download.set_defaults(func=cmd_build_download)

    compile_ = build_sub.add_parser("compile")
    compile_.add_argument("--tree", default=str(DEFAULT_TREE))
    compile_.add_argument("--jobs", default=None)
    compile_.set_defaults(func=cmd_build_compile)

    collect = build_sub.add_parser("collect")
    collect.add_argument("--tree", default=str(DEFAULT_TREE))
    collect.add_argument("--out", default="dist")
    collect.set_defaults(func=cmd_build_collect)

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
        # GitHub Actions annotation for a clearer summary.
        first = str(exc).splitlines()[0] if str(exc) else "build failed"
        print(f"::error::{first}", flush=True)
        return 1
    except KeyboardInterrupt:
        print("::error::interrupted", flush=True)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
