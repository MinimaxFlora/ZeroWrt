<div align="center">

**English** · [简体中文](docs/readme/README_zh-CN.md) · [繁體中文](docs/readme/README_zh-TW.md) · [日本語](docs/readme/README_ja.md) · [한국어](docs/readme/README_ko.md) · [Türkçe](docs/readme/README_tr.md) · [Русский](docs/readme/README_ru.md) · [Tiếng Việt](docs/readme/README_vi.md) · [ไทย](docs/readme/README_th.md) · [Deutsch](docs/readme/README_de.md) · [Español](docs/readme/README_es.md) · [Français](docs/readme/README_fr.md) · [Українська](docs/readme/README_uk.md) · [Polski](docs/readme/README_pl.md) · [Português (Brasil)](docs/readme/README_pt-BR.md) · [العربية](docs/readme/README_ar.md) · [فارسی](docs/readme/README_fa.md) · [Bahasa Indonesia](docs/readme/README_id.md) · [Italiano](docs/readme/README_it.md) · [Ελληνικά](docs/readme/README_el.md) · [മലയാളം](docs/readme/README_ml.md)

<img src="assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### Custom firmware built from LEDE, with one-click online updates.

**One command builds it, one click updates it.**

[![Build](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![Kernel](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![Target](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[Download page](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [Build logs](https://github.com/MinimaxFlora/ZeroWrt/actions) · [Issues](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>System → Online upgrade → Check for updates</code>

</div>

> [!IMPORTANT]
> **Official sources only.** Firmware is published in this repository's
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) and on
> [ota.kejizero.xyz](https://ota.kejizero.xyz/). A similar repository name or a
> copied README does not make a build official.

---

ZeroWrt is a small custom firmware for OpenWrt-class routers, compiled from a
private LEDE tree by GitHub Actions. Every build is produced from source,
published with `SHA256SUMS` and `BUILD_INFO.txt`, and listed in an update index
so the device can upgrade itself from LuCI.

The interesting part is not another package list — it is the loop: the build
publishes the image and the index, and the router sees the new version the next
time it checks.

## Features

- **One-click updates** — LuCI reads the index, downloads with resume and progress, verifies SHA256 and the image with `sysupgrade -T`, then flashes and reboots.
- **Honest version checks** — the build timestamp decides "newer", with a version-string fallback; a date that cannot be determined is shown as unknown instead of being invented.
- **Configuration from the workflow** — LAN IP, hostname and the three Wi-Fi SSIDs and passwords are inputs, not hand-edited files.
- **Argon 3 branding** — background, login logo, favicon and palette (`#2E9D72` / `#4CAF86`) are replaced at build time.
- **Proxy stack included** — PassWall (Xray only) and OpenClash, vendored from [openwrt_helloworld](https://github.com/MinimaxFlora/openwrt_helloworld) so the build depends on one checkout instead of four upstream repositories.
- **Gated pipeline** — `ruff` and 18 unit tests run on every pull request.

## Supported devices

| Device | Target | Images |
| --- | --- | --- |
| Ruijie RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`, `-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI and legacy BIOS builds |

Release tags are the device name (`ruijie_rg-x60-new`, `x86_64`). Each device
keeps its own release, so the index and the download page can list them side by side.

## Download

- **Download page** — <https://ota.kejizero.xyz/> shows the current build, the changelog and the SHA256.
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> holds the images and `SHA256SUMS`.
- **On the device** — *System → Online upgrade* does the same thing without a browser download.

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## Flashing

**A. From OpenWrt or ImmortalWrt**
*System → Backup / Flash firmware*, upload the `-squashfs-sysupgrade.bin`, and do
not keep the configuration when you cross a major version.

**B. From stock firmware**
Install the bootloader recovery first (the usual U-Boot web page for this board),
then upload the same image there. Do not flash the stock web UI.

**C. Recovery**
Boot the `-initramfs-kernel.bin` from the bootloader to get a temporary system,
then flash the sysupgrade image from it.

Default address `10.0.0.1`, user `root`, password `password`. Change it on first login.

## Online upgrade

The firmware ships with `luci-app-ota`:

- the index defaults to `https://ota.kejizero.xyz/ota.json` and can be changed under *System → Online upgrade → Configuration*;
- the SHA256 is mandatory: an entry without one is rejected, and a mismatch deletes the download;
- plain `http` is refused unless *allow insecure connections* is enabled;
- the device key is resolved from `/etc/ota/build.json`, the device tree model, `board_name` and the architecture, in that order, and both spellings of a board name (`vendor,device` and `vendor_device`) are accepted.

## Building

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

Builds are started by hand: *Actions → Build ZeroWrt → Run workflow*. There is no
`push` trigger, so merging code never starts a six-hour compile. The pipeline is
documented in [docs/BUILD.md](docs/BUILD.md): secrets, inputs, the toolchain cache and every step.

## FAQ

**Where is the source?** The LEDE tree is private. This repository holds the pipeline, the branding assets and the tests.

**Why is there no `factory` image?** These boards are flashed through their bootloader recovery page, which accepts the sysupgrade image directly.

**Can I point it at my own index?** Yes — set `api_url` to any compatible JSON and host it wherever you like.

## Credits

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [hanwckf](https://github.com/hanwckf) | [Yuzhii0718](https://github.com/Yuzhii0718) |
| :-: | :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/27666983"/> | <img width="100" src="https://avatars.githubusercontent.com/u/107190140"/> |
| [sbwml](https://github.com/sbwml) | [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> | <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## License

The scripts, branding assets and documentation in this repository are released under **GPL-2.0** — see [LICENSE](LICENSE).

The firmware itself bundles OpenWrt, LEDE and many other upstream components, each under its own licence. Redistributing an image means honouring those licences too; GPL-2.0 in particular requires you to make the corresponding source available.

## Disclaimer

Flashing firmware can brick a device. Back up the stock firmware and your
configuration, and understand the recovery path before you start. The firmware
is provided as is, without warranty.

---

Maintainer notes: [docs/BUILD.md](docs/BUILD.md) · Other languages: [docs/readme](docs/readme)
