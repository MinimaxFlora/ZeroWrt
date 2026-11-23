# ZeroWrt

[简体中文](README_zh.md) · English

Lean's LEDE based OpenWrt firmware, built from source by GitHub Actions for **x86_64**, with an
**online update (OTA) page** baked in. Prebuilt images and update metadata are published to
[Releases](https://github.com/MinimaxFlora/ZeroWrt/releases); the download site is
[ota.tatalvpai.vip](https://ota.tatalvpai.vip/).

[![Build](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/Trigger-All-Workflows.yml/badge.svg)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/Trigger-All-Workflows.yml)
[![Release](https://img.shields.io/github/v/release/MinimaxFlora/ZeroWrt?label=release)](https://github.com/MinimaxFlora/ZeroWrt/releases)

## What this repository is

This is the **build configuration**, not a copy of the OpenWrt tree. A workflow clones
[coolsnowwolf/lede](https://github.com/coolsnowwolf/lede) at build time, applies
[`diy-script.sh`](diy-script.sh), drops in the selected packages, compiles, and uploads the result
to a release.

- Base: `coolsnowwolf/lede` (`master`), Linux **7.3.x**
- Target: `x86/64` (generic, EFI), image `*-squashfs-combined-efi.img.gz`
- Build time: GitHub Actions, weekly schedule plus manual dispatch
- Default address `10.0.0.1`, user `root`, password `password`
  (change it right after the first login)

## Features

| Area | What is included |
| --- | --- |
| Proxy / routing | PassWall, PassWall2 (nftables TProxy), nikki (mihomo-meta), sing-box, Xray-core, shadowsocks-rust, ShadowsocksR-libev, simple-obfs, v2ray-plugin, microsocks, ipt2socks, dns2socks, Haproxy, geoview |
| DNS | mosdns, smartdns, chinadns-ng, v2ray-geoip / geosite — split DNS works out of the box |
| Services | OpenList2, Lucky, frpc, ZeroTier, WireGuard, Samba4, SQM (CAKE), DDNS (Cloudflare / GoDaddy / FreeDNS), USB printer, AirConnect |
| Storage | DiskMan, btrfs / XFS / exFAT / F2FS tools, parted, smartmontools, zram-swap |
| System | ttyd (no login prompt on the LAN), Argon and Brutal themes (Brutal is the default), nano, yq, coreutils, ramfree |
| Update | **luci-app-ota**: check, download with SHA256 verification, `sysupgrade -T` pre-check, install with settings kept — plus a CLI (`ota`) |

Chinese translations are compiled in for every app listed above.

## Download and install

1. Grab the latest image from [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases/tag/X86_64)
   or from the [download site](https://ota.tatalvpai.vip/).
2. Write it to disk or a USB stick (EFI boot):

   ```sh
   # Linux / macOS
   gunzip -c zerowrt-x86-64-generic-squashfs-combined-efi.img.gz | sudo dd of=/dev/sdX bs=4M status=progress
   ```

   On Windows use balenaEtcher or Rufus (DD mode) with the decompressed `.img`.

3. Boot the device. LuCI is at <http://10.0.0.1/>, SSH as `root` / `password`.
4. Grow the overlay if the disk is larger than the image: open **System → Disk Man**, select the
   root partition and use *Expand* (or `cfdisk` + `resize2fs` / `mkfs.f2fs`), then reboot.

Verify the download against the `sha256sums` published with each release before flashing.

## Online update (OTA)

The firmware ships [luci-app-ota](https://github.com/MinimaxFlora/luci-app-ota) and a default index
URL, so a fresh install can update itself without a USB stick:

- LuCI → **System → OTA Firmware Update**
- The page compares build timestamps from `/etc/ota/build.json` with the index entry
- Download is verified (SHA256) and pre-checked with `sysupgrade -T`; a bad image is discarded
- Install keeps the configuration by default (`sysupgrade`, settings preserved)

Command line equivalent:

```sh
ota info                  # local firmware + last check result
ota check                 # fetch the index and compare versions
ota download              # start the background download
ota status                # progress as JSON
ota apply --keep 1        # flash, keeping settings
```

The index lives at <https://ota.tatalvpai.vip/ota.json> (schema 2, one key per device; x86 uses
`x86_64+efi`). If GitHub is slow, pick an acceleration site under **OTA → Configuration**; the
default is `gh-proxy.tatalvpai.vip`.

### How the OTA wiring works

Every build writes its own identity into the image and publishes an index entry:

| Piece | Written by | Purpose |
| --- | --- | --- |
| `/etc/ota/build.json` | `diy-script.sh` via `luci-app-ota/tools/embed_ota_meta.py` | device key, target, build timestamp |
| `/etc/uci-defaults/90-luci-app-ota` | `diy-script.sh` | default index URL (only when unset; user changes win) |
| `ota.json` (release asset) | [`scripts/gen_ota_index.py`](scripts/gen_ota_index.py) | merged index for all devices |
| `ota.json` (site) | [Zerowrt-Website](https://github.com/MinimaxFlora/Zerowrt-Website) workflow | what devices actually fetch |

The device key must match between `build.json` and the index — for x86 that is `x86_64` with an
`+efi` boot variant, routers use the profile name (for example `ruijie_rg-x60-new`).

## Build it yourself

1. Fork this repository.
2. Edit [`configs/x86_64.config`](configs/x86_64.config) (packages, target) or
   [`diy-script.sh`](diy-script.sh) (source tweaks, extra repositories).
3. Run **Actions → Trigger-All-Workflows → Run workflow** (it also runs every Friday at 18:00 UTC).
4. The job publishes to the `X86_64` release tag; build logs are attached to the run.

Notes:

- The toolchain cache is keyed per source/target, so the first run is slow and later ones fast.
- `diy-script.sh` runs inside the OpenWrt tree; it also sets the hostname, LAN address, default
  password, banner, and swaps in the Brutal theme.
- Adding a device means adding a config plus a workflow that calls `Build-Release.yml` with
  `CONFIG_FILE`, `FIRMWARE_TAG`, `OTA_DEVICE` and `OTA_TARGET`.

## Repository layout

```
.github/workflows/Build-Release.yml   # the actual build: clone → configure → compile → release
.github/workflows/X86_64.yml          # x86_64 entry point (config + OTA identity)
.github/workflows/Trigger-All-Workflows.yml
configs/x86_64.config                 # kernel/packages for x86_64
diy-script.sh                         # patches, package sources, OTA metadata, branding
scripts/feeds.conf.default            # Lean's package feeds
scripts/gen_ota_index.py              # builds/merges ota.json from a firmware directory
images/                               # theme background
```

## FAQ

**Only an EFI image?** Yes. ZeroWrt x86 builds the `combined-efi` image; there is no legacy BIOS
image in the release, so boot the target with UEFI enabled.

**The disk is bigger than the image.** Expand the overlay partition with DiskMan (or `cfdisk` +
`resize2fs`/`mkfs.f2fs`) after the first boot.

**How do I change the LAN address?** LuCI → Network → Interfaces → LAN, or
`uci set network.lan.ipaddr=...`.

**OTA says "no firmware for this device".** The index key does not match. Open the OTA page and
read *Device key*, then check that the same key exists in
<https://ota.tatalvpai.vip/ota.json>; you can also set it manually under OTA → Configuration.

## Credits

Built on [coolsnowwolf/lede](https://github.com/coolsnowwolf/lede). Packages come from
PassWall, [nikkinikki-org/OpenWrt-nikki](https://github.com/nikkinikki-org/OpenWrt-nikki),
[sbwml](https://github.com/sbwml) (mosdns, openlist2, diskman, airconnect, golang/rust),
[gdy666/luci-app-lucky](https://github.com/gdy666/luci-app-lucky),
[jerrykuku/luci-theme-argon](https://github.com/jerrykuku/luci-theme-argon) and
[luci-theme-brutal](https://github.com/MinimaxFlora/luci-theme-brutal). Each component keeps its
own license; the scripts in this repository are provided as-is, without warranty.
