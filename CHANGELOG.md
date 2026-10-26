# 更新日志

本文件的所有内容都基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式，
版本号大致遵循[语义化版本](https://semver.org/lang/zh-CN/)。

> **关于历史**：这个文件是从 2026-10-27 开始维护的。在此之前本仓库没有维护 changelog，
> 更早的变更请查看[提交记录](https://github.com/MinimaxFlora/ZeroWrt/commits/main)和
> [Actions 构建日志](https://github.com/MinimaxFlora/ZeroWrt/actions)。

## [Unreleased]

### Added

- **释放内存插件** —— `luci-app-ramfree`（`sbwml/luci-app-ramfree`），克隆到 `package/new/luci-app-ramfree`，两种设备都装。
- **mosdns（仅 x86_64）** —— `luci-app-mosdns` 及其依赖 `mosdns`、`geo2txt`（`sbwml/luci-app-mosdns@v5`），
  克隆到 `package/new/luci-app-mosdns`。`ruijie_rg-x60-new` 不含此插件。
- **自定义登录 banner** —— 新增 `assets/banner`，构建时整体替换 `package/base-files/files/etc/banner`，
  改横幅只需改这一个文件。
- 仓库治理文件：`SECURITY.md`、`CONTRIBUTING.md`、`CHANGELOG.md`、Issue/PR 模板、Dependabot 配置。

### Fixed

- **x86_64 目标构建失败** —— `.config` 里写的是 profile 形式的 `CONFIG_TARGET_x86_64_Generic`，
  但 `target/linux/x86/image/64.mk` 定义的是 `Device/generic`（小写），Kconfig 实际符号为
  `CONFIG_TARGET_x86_64_DEVICE_generic`。符号不存在，`make defconfig` 直接丢弃该选项，构建随即失败。
  现在 device 名从源码树真实解析，不再硬编码；顺带支持了 `x86_generic` 目标。
- **feeds 与 `package/new` 重复包** —— 清理逻辑现在会从 `packages.PACKAGE_DIR_NAMES` 派发，
  并按**目录名 + Makefile 实际 BuildPackage 包名**双路匹配。此前 `net/v2ray-geodata`、
  `luci-app-passwall2`、`luci-app-mosdns`、`luci-app-ramfree` 等一批 feed 副本未被删除，
  会造成 duplicate package；`v2ray-geodata` 之所以漏掉，是因为它从同名目录里 BuildPackage 出的是
  `v2ray-geoip` / `v2ray-geosite`，只比目录名识别不到。
- 删除 feed 包时要求目录必须含 `Makefile`，避免误删 LuCI 应用的同名静态资源目录（如 `htdocs/.../mosdns`）。

### Changed

- `package/new` 下的外部仓库统一为**一个仓库一个目录，与 `helloworld/` 平级**；
  mosdns 仓库的落点由 `package/new/mosdns` 调整为 `package/new/luci-app-mosdns`。
- "我们拥有哪些包"的清单收敛到 `scripts/zerowrt_core/packages.py` 的 `PACKAGE_DIR_NAMES`，
  feeds 清理与 `package/` 清理共用这一份，不再各自维护导致漂移。
- 单元测试增至 29 个，新增 `FeedConflictTest` 覆盖上述重复包场景。

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
