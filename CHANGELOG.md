# Changelog

## 2.0.0 — 2026-11-02

Python rewrite of the ZeroWrt/MediaTek builder pipeline.

- Build source moved to `chasey-dev/immortalwrt-mt798x-rebase` `25.12`.
- Device selection is the MediaTek Builder config `configs/ruijie-rg-x60-new.config`
  (MTK U-Boot / mtkuboot layout).
- The shell `diy-script.sh` is replaced by Python modules:
  `customize.py`, `packages.py`, `patches.py`.
- Added `luci-app-ota` to the image, build metadata (`/etc/ota/build.json`),
  a schema-2 `ota.json`, `history.json`, and gh-pages publishing.
- LuCI patches `0001`–`0005` refreshed against `immortalwrt/luci`
  `openwrt-25.12`; GCC 16 patch `0006` retained.
- Added `SHA256SUMS`, `BUILD_INFO.txt`, `Packages.tar.gz` and
  `build.config` to the release artifacts.
- Added a memory-aware `nproc + 1` compile policy with serial `V=s` fallback.
- Keep the feed's versioned `golang1.27` instead of replacing it with the
  unversioned sbwml checkout (fixes `golang1.27/host` build-dependency warnings).
- Disable sing-box NaiveProxy outbound until a `libcronet` provider exists
  (the current `openwrt_package` Makefile references a package it does not ship).
- Added an optional toolchain cache in the `toolchain` release and a
  `Build Toolchain Cache` workflow.
- Unit tests and Ruff checks run on every pull request.
