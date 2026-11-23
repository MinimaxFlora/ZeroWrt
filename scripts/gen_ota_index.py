#!/usr/bin/env python3
"""Generate (or update) the OTA update index for ZeroWrt.

luci-app-ota only needs a JSON index that maps a device key to a firmware
image URL, its SHA256 and a build timestamp. ``diy-script.sh`` writes the
matching ``ota-meta.json`` next to the build artifacts through
``luci-app-ota/tools/embed_ota_meta.py``; this script turns that file into an
``ota.json`` entry and merges it into an existing index, so several device
workflows can share one index.

Image selection:

* ``*-squashfs-combined-efi.img.gz``  -> ``<device>+efi`` (x86, EFI boot)
* ``*-squashfs-combined.img.gz``      -> ``<device>+bios`` (x86, legacy boot)
* ``*-squashfs-sysupgrade.bin``/``.itb`` -> ``<device>`` (routers)

The plain ``<device>`` key is used for router images. x86 builds only get the
``+efi`` / ``+bios`` keys that actually exist: advertising an EFI image under
the plain key would make a legacy-BIOS board flash a firmware it cannot boot.

Usage::

    python3 scripts/gen_ota_index.py --dir bin/targets/x86/64 \\
        --tag X86_64 --repo MinimaxFlora/ZeroWrt \\
        --merge https://ota.tatalvpai.vip/ota.json \\
        --changelog-file changelog.md --out bin/targets/x86/64/ota.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

IMAGE_SUFFIXES = (
    "-squashfs-combined-efi.img.gz",
    "-squashfs-combined.img.gz",
    "-squashfs-sysupgrade.bin",
    "-squashfs-sysupgrade.itb",
)


def log(message: str) -> None:
    print(f"[ota-index] {message}", flush=True)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_source(source: str) -> dict:
    """Load a JSON file from disk or https:// (returns {} on any failure)."""
    if not source:
        return {}

    try:
        if source.startswith(("http://", "https://")):
            # Cloudflare rejects the default urllib agent, so send our own.
            request = urllib.request.Request(
                source,
                headers={
                    "User-Agent": "ZeroWrt-OTA/1.0 (+https://github.com/MinimaxFlora/ZeroWrt)",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(request, timeout=25) as response:
                return json.loads(response.read().decode("utf-8"))
        path = Path(source)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - best effort merge source
        log(f"warning: cannot read merge source {source}: {exc}")

    return {}


def load_merge_sources(spec: str) -> dict:
    """Try every comma separated merge source, keep the first usable index."""
    for candidate in [part.strip() for part in (spec or "").split(",") if part.strip()]:
        data = load_json_source(candidate)
        if isinstance(data, dict) and data.get("schema") == 2 and isinstance(data.get("devices"), dict):
            log(f"merged existing index from {candidate} ({len(data['devices'])} device(s))")
            return data

    return {}


def find_meta(directory: Path) -> dict:
    for name in ("ota-meta.json", ".ota-meta.json"):
        candidate = directory / name
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8-sig"))
                if isinstance(data, dict) and data.get("device"):
                    return data
            except (OSError, json.JSONDecodeError) as exc:
                log(f"warning: cannot parse {candidate}: {exc}")

    return {}


def profile_from_image(directory: Path, meta: dict) -> dict:
    """Fall back to profiles.json when the metadata file is missing."""
    if meta.get("device"):
        return meta

    profiles = directory / "profiles.json"
    if profiles.exists():
        try:
            data = json.loads(profiles.read_text(encoding="utf-8-sig"))
            epoch = int(data.get("source_date_epoch") or 0)
            version = str(data.get("version_number") or "")
            for profile, value in (data.get("profiles") or {}).items():
                if value.get("images"):
                    return {
                        "device": profile,
                        "target": data.get("target") or "",
                        "version": version,
                        "build_date": epoch,
                    }
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    return {}


def build_date_from_env() -> int:
    import os

    for key in ("OTA_BUILD_DATE", "SOURCE_DATE_EPOCH"):
        value = os.environ.get(key, "")
        if value.isdigit():
            return int(value)

    return int(time.time())


def pick_images(directory: Path) -> list[tuple[str, Path]]:
    """Return (variant, path) pairs; variant is 'efi', 'bios' or ''."""
    picked: list[tuple[str, Path]] = []

    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue

        name = path.name

        if name.endswith("-squashfs-combined.img.gz"):
            picked.append(("bios", path))
        elif name.endswith("-squashfs-combined-efi.img.gz"):
            picked.append(("efi", path))
        elif name.endswith("-squashfs-sysupgrade.bin") or name.endswith("-squashfs-sysupgrade.itb"):
            picked.append(("", path))

    return picked


def human_label(meta: dict, device: str) -> str:
    label = str(meta.get("label") or "").strip()
    if label:
        return label

    product = str(meta.get("product") or "").strip()
    if product:
        return product

    # "x86_64" should read as "ZeroWrt x86_64", not "x86 64".
    if device.lower().startswith("x86"):
        return f"ZeroWrt {device}"

    return device.replace("_", " ")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the ZeroWrt OTA index")
    parser.add_argument("--dir", required=True, help="firmware directory produced by the build")
    parser.add_argument("--repo", default="MinimaxFlora/ZeroWrt", help="owner/repo that hosts the releases")
    parser.add_argument("--tag", required=True, help="release tag the images are uploaded to")
    parser.add_argument("--base-url", default="", help="override the download base URL")
    parser.add_argument("--merge", default="", help="existing index to merge into (path or URL)")
    parser.add_argument("--changelog", default="", help="changelog markdown for this build")
    parser.add_argument("--changelog-file", default="", help="file with the changelog markdown")
    parser.add_argument("--out", default="", help="output file (default: <dir>/ota.json)")
    parser.add_argument("--print", action="store_true", help="print the index as JSON")
    args = parser.parse_args(argv)

    directory = Path(args.dir)
    if not directory.is_dir():
        log(f"error: {directory} is not a directory")
        return 2

    meta = profile_from_image(directory, find_meta(directory))
    device = str(meta.get("device") or "")
    if not device:
        log("error: no device metadata and no profiles.json found")
        return 2

    images = pick_images(directory)
    if not images:
        log("error: no sysupgrade image found")
        return 2

    changelog = args.changelog
    if not changelog and args.changelog_file:
        changelog = Path(args.changelog_file).read_text(encoding="utf-8", errors="replace")

    base_url = args.base_url.rstrip("/") + "/" if args.base_url else \
        f"https://github.com/{args.repo}/releases/download/{args.tag}/"

    build_date = int(meta.get("build_date") or build_date_from_env())
    version = str(meta.get("version") or time.strftime("%Y%m%d"))
    target = str(meta.get("target") or "")
    label = human_label(meta, device)

    index = load_merge_sources(args.merge) if args.merge else {}
    if not isinstance(index, dict) or index.get("schema") != 2:
        index = {}

    devices = index.get("devices")
    if not isinstance(devices, dict):
        devices = {}

    # Drop the keys this build owns so a re-run never leaves stale entries.
    for key in list(devices):
        if key == device or key.startswith(device + "+"):
            del devices[key]

    entry_base = {
        "version": version,
        "build_date": build_date,
        "target": target,
        "device": device,
        "label": label,
    }

    for variant, path in images:
        entry = dict(entry_base)
        entry["url"] = base_url + path.name
        entry["sha256"] = sha256_of(path)
        entry["size"] = path.stat().st_size
        entry["file"] = path.name

        if variant:
            entry["variant"] = variant
            # "ZeroWrt x86_64 (EFI)" reads better on the download page.
            entry["label"] = f"{label} ({variant.upper()})"
            key = f"{device}+{variant}"
        else:
            key = device

        if changelog:
            entry["changelog"] = changelog

        devices[key] = entry
        log(f"{key} <- {path.name} ({entry['size']} bytes)")

    result = {
        "schema": 2,
        "generator": "ZeroWrt gen_ota_index.py",
        "generated": int(time.time()),
        "dist": str(meta.get("dist") or index.get("dist") or "ZeroWrt"),
        "devices": dict(sorted(devices.items())),
    }

    out = Path(args.out) if args.out else directory / "ota.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log(f"wrote {out} ({len(devices)} device(s))")

    if args.print:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
