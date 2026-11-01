# 更新日志

本文件的所有内容都基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式，
版本号大致遵循[语义化版本](https://semver.org/lang/zh-CN/)。

> **关于历史**：这个文件是从 2026-10-27 开始维护的。在此之前本仓库没有维护 changelog，
> 更早的变更请查看[提交记录](https://github.com/MinimaxFlora/ZeroWrt/commits/main)和
> [Actions 构建日志](https://github.com/MinimaxFlora/ZeroWrt/actions)。

## [Unreleased]

### Changed

- **RG-X60 New 换基线**：源码换成
  [`Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly`](https://github.com/Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly)
  的 `openwrt-24.10-6.6` 分支，固件改成 **ubootmod** 布局（`Device/ruijie_rg-x60-new-ubootmod`），
  产物是 `-squashfs-sysupgrade.itb` + `preloader.bin` / `bl31-uboot.fip`。
  Release tag 仍沿用 `ruijie_rg-x60-new`；跨基线不能在线升级，需要从 U-Boot 恢复页全新刷机。
- **源码树收敛到一份公开仓库**，不再需要 `LEDE_REPO` / `LEDE_TOKEN` / `LEDE_REF` 三个 Secret，
  `source clone` 直接按 `profiles.py` 匿名拉取。
- **设备映射收敛到 `scripts/zerowrt_core/profiles.py`**，删掉 `configgen.DEVICE_ALIASES` 与
  `configgen.DEVICE_PACKAGES`；workflow 不再暴露 `device` 参数。
- **版本字符串改为直接写模板**：`openwrt_release` / `os-release` 是 `%D %V %C` 模板，脚本现在直接
  写成 `DISTRIB_DESCRIPTION='ZeroWrt-<日期>'`、`DISTRIB_REVISION=' By MinimaxFlora'`、
  `OPENWRT_RELEASE="ZeroWrt 标准版 @R<日期> BY MinimaxFlora"` 这样的字面量。
- **WiFi 默认值改写 `package/mtk/applications/mtwifi-cfg/files/mtwifi.sh`**：两个默认 SSID 换成
  配置值，`encryption=none` 改成 `psk2` + `key`。
- `BUILD_INFO.txt` 增加 `profile`、`layout`、`source repo/ref/commit`。

### Added

- **释放内存插件** —— `luci-app-ramfree`（`sbwml/luci-app-ramfree`），克隆到 `package/new/luci-app-ramfree`。
- **自定义登录 banner** —— 新增 `assets/banner`，构建时整体替换 `package/base-files/files/etc/banner`，
  改横幅只需改这一个文件。源码树根部的 `files/` 覆盖层会在替换前删除，否则 ImmortalWrt 自带的那份会盖回去。
- 仓库治理文件：`SECURITY.md`、`CONTRIBUTING.md`、`CHANGELOG.md`、Issue/PR 模板、Dependabot 配置。
- 单元测试覆盖 `files/` 清理、`mtwifi.sh` 改写、OTA 索引补丁与 sing-box 选择。

### Fixed

- **PassWall 内核改回 sing-box**：PassWall 的 Makefile 对 aarch64 默认同时打开 Xray、Sing-Box 和
  SmartDNS，现在显式打开 Sing-Box、关闭另外两个，并在 `defconfig` 后校验，避免镜像里塞进两个内核
  和一个多余的 DNS 服务。
- **feeds 与 `package/new` 重复包** —— 清理逻辑现在会从 `packages.PACKAGE_DIR_NAMES` 派发，
  并按**目录名 + Makefile 实际 BuildPackage 包名**双路匹配。此前 `net/v2ray-geodata`、
  `luci-app-passwall2`、`luci-app-ramfree` 等一批 feed 副本未被删除，会造成 duplicate package；
  `v2ray-geodata` 之所以漏掉，是因为它从同名目录里 BuildPackage 出的是 `v2ray-geoip` /
  `v2ray-geosite`，只比目录名识别不到。
- 删除 feed 包时要求目录必须含 `Makefile`，避免误删 LuCI 应用的同名静态资源目录（如 `htdocs/.../sing-box`）。
- **OTA 索引不再漏掉 ubootmod 镜像**：`luci-app-ota` 的 `tools/gen_ota_index.py` 会把文件名里带
  `uboot` 的镜像全部排除，正好命中了 `-squashfs-sysupgrade.itb`；同时它没有规则阻止选中
  `preloader.bin`。现在 `packages ota` 在克隆后把 `BAD_TOKENS` 里的 `"uboot"` 换成
  `"preloader"` / `"bl31"`，只排除引导文件，上游布局变了会直接失败。
- **Argon 的 `wget-any` 警告**：`luci-theme-argon` 的 `LUCI_DEPENDS` 同时写了
  `+USE_APK:wget-any` 和 `+!USE_APK:wget`。OpenWrt 的包元数据扫描先按 `:` 切分再校验依赖名，
  两条都会被检查，而 `wget-any` 只在 apk 世界里由 `uclient-fetch` 提供，24.10 中不存在，
  于是每次构建都打印 `has a dependency on 'wget-any', which does not exist`。`packages.py`
  现在把它改成 `+wget-ssl`（主题的 rpcd 脚本要用 `wget` 访问 https），警告消失。
- **LAN 地址不再跟随设备**：`config_generate` 里每个 `ipad=${ipaddr:-"..."}` 默认值都会改成
  配置的 IP（默认 `10.0.0.1`），包括 ImmortalWrt 给 `ruijie,rg-x60*` 分支写死的
  `192.168.110.1`；校验步骤现在会检查所有分支的默认值，残留任何一个都会让构建失败。
- **工具链缓存资产名去掉设备前缀**：恢复为 `toolchain_<libc>_<arch>_gcc-<major>.tar.zst`
  （例如 `toolchain_musl_aarch64_cortex-a53_gcc-13.tar.zst`）；固件构建只认这种命名的资产，
  带设备前缀的旧缓存会被忽略。

### Removed

- **x86_64 支持** —— 移除 `x86_64` profile、LEDE 源码树、x86 的内核固定、mac80211 默认 WiFi 和
  `luci-app-mosdns`（它本来就只给 x86），以及 workflow 的 `device` 选择参数。现在只构建
  `ruijie_rg-x60-new`。

## [0.1.0] — 初始版本

流水线从零建立时的基线。

### Added

- 构建流水线，支持 `ruijie_rg-x60-new`（`mediatek/filogic`）与 x86_64（`x86/64`）两种设备。
- 一键在线升级：LuCI 读取索引、断点续传下载、强制 SHA256 校验、`sysupgrade -T` 预检后刷写重启。
- 版本判定以构建时间戳为准，带版本号兜底；无法判定时显示 unknown 而不是编造结果。
- 工作流参数化：LAN IP、主机名、2.4G/5G/6G 三套 SSID 与密码均为输入项。
- Argon 3 品牌化：登录背景、登录 Logo、favicon、主题配色（`#2E9D72` / `#4CAF86`）。
- 代理套件 PassWall（Xray 核心）与 OpenClash，由 [openwrt_helloworld](https://github.com/MinimaxFlora/openwrt_helloworld) 单仓库提供。
- toolchain 缓存：单独 workflow 编译一次工具链并发布到 `toolchain` release，固件构建直接恢复。
- 产物附带 `SHA256SUMS` 与 `BUILD_INFO.txt`，并发布到 OTA 索引页与 Cloudflare Pages。

---

[Unreleased]: https://github.com/MinimaxFlora/ZeroWrt/compare/main...HEAD
[0.1.0]: https://github.com/MinimaxFlora/ZeroWrt/releases
