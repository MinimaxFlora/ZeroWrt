<div align="center">

[English](../../README.md) · **简体中文** · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Українська](README_uk.md) · [Polski](README_pl.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Bahasa Indonesia](README_id.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md) · [മലയാളം](README_ml.md)

<img src="../../assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### 基于 LEDE 的定制固件，内置网页一键在线升级。

**一条命令出固件，点一下完成升级。**

[![构建](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/build.yml)
![内核](https://img.shields.io/badge/kernel-6.18-1793d1?style=flat-square)
![LuCI](https://img.shields.io/badge/LuCI-openwrt--25.12-E45A1B?style=flat-square)
![平台](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--2.0-4c9c2f?style=flat-square)

[下载页](https://ota.kejizero.xyz/) · [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) · [构建日志](https://github.com/MinimaxFlora/ZeroWrt/actions) · [问题反馈](https://github.com/MinimaxFlora/ZeroWrt/issues)

<code>系统 → 在线升级 → 检查更新</code>

</div>

> [!IMPORTANT]
> **只从官方来源下载。** 固件只发布在本仓库的
> [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases) 和
> [ota.kejizero.xyz](https://ota.kejizero.xyz/)。相似的仓库名或被复制的 README
> 都不能证明那份固件来自这里。

---

ZeroWrt 是面向 OpenWrt 类路由器的定制固件，由 GitHub Actions 从一份私有的 LEDE
源码树自动编译。每次构建都从源码产出，连同 `SHA256SUMS` 和 `BUILD_INFO.txt` 一起
发布，并写进更新索引，设备可以自己从 LuCI 升级。

真正有意思的不是又一份软件包清单，而是这条链路：构建产出镜像和
索引，路由器下次检查时就能看到新版本。

## 特性

- **网页一键升级** — LuCI 读取索引，带断点续传和进度下载，校验 SHA256 并用 `sysupgrade -T` 预检镜像，然后写入并重启。
- **不糊弄的版本判断** — 以构建时间戳判断新旧，没有时间戳才退回比版本号；无法确定的日期显示为"未知"，不会凭空编一个。
- **配置由工作流注入** — 管理 IP、主机名和三组 Wi-Fi 名称/密码都是构建参数，不是手改文件。
- **Argon 3 品牌化** — 登录背景、登录 Logo、网站图标和配色（`#2E9D72` / `#4CAF86`）在构建时替换。
- **内置代理插件** — PassWall（仅 Xray）和 OpenClash，由构建脚本自动同步。
- **有门槛的流水线** — 每个 PR 都要过 `ruff` 和 18 个单元测试。

## 支持的设备

| 设备 | 平台 | 镜像 |
| --- | --- | --- |
| 锐捷 RG-X60 New | `mediatek/filogic` | `-squashfs-sysupgrade.bin`、`-initramfs-kernel.bin` |
| x86_64 | `x86/64` | EFI 与传统 BIOS 两种 |

Release 的 tag 就是设备名（`ruijie_rg-x60-new`、`x86_64`）。每台设备保留自己的
release，索引和下载页可以把它们并排列出来。

## 下载

- **下载页** — <https://ota.kejizero.xyz/> 显示当前版本、更新日志和 SHA256。
- **GitHub Releases** — <https://github.com/MinimaxFlora/ZeroWrt/releases> 存放镜像和 `SHA256SUMS`。
- **在设备上** — *系统 → 在线升级* 可以直接升级，不用先在电脑上下载。

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

## 刷机

**A. 已经是 OpenWrt / ImmortalWrt**
*系统 → 备份/刷写固件*，上传 `-squashfs-sysupgrade.bin`；跨大版本时不要保留配置。

**B. 原厂固件**
先装好引导的不死 U-Boot（这块板子通常是网页恢复页），再在那里上传同一个镜像。
不要拿原厂后台直接刷。

**C. 救砖**
从引导里启动 `-initramfs-kernel.bin` 得到一个临时系统，再在里面刷 sysupgrade 镜像。

默认地址 `10.0.0.1`，用户名 `root`，密码 `password`，第一次登录请立刻修改。

## 在线升级

固件内置 `luci-app-ota`：

- 索引默认是 `https://ota.kejizero.xyz/ota.json`，可以在 *系统 → 在线升级 → 配置* 里改；
- SHA256 是必填项，没有就拒绝下载，校验不通过直接删掉；
- 默认拒绝明文 `http`，除非打开"允许不安全的连接"；
- 设备标识依次从 `/etc/ota/build.json`、设备树 model、`board_name` 和架构推导，并且同时接受 `vendor,device` 和 `vendor_device` 两种写法。

## 构建

```bash
gh workflow run build.yml -f device=ruijie_rg-x60-new
```

构建只能手动触发：*Actions → Build ZeroWrt → Run workflow*，没有 `push` 触发器，合并代码不会顺带跑一次六小时的编译。完整流程（Secrets、参数、ccache、每一步在做什么）见 [docs/BUILD.md](../BUILD.md)。

## 常见问题

**源码在哪？** LEDE 源码树是私有的。本仓库放的是流水线、品牌素材和测试。

**为什么没有 `factory` 镜像？** 这块板子通过引导的网页恢复页刷机，它直接接受 sysupgrade 镜像。

**能换成我自己的索引吗？** 可以，把 `api_url` 指向任何兼容格式的 JSON，自己找地方托管即可。

## 鸣谢

| [OpenWrt](https://github.com/openwrt) | [coolsnowwolf](https://github.com/coolsnowwolf) | [hanwckf](https://github.com/hanwckf) | [Yuzhii0718](https://github.com/Yuzhii0718) |
| :-: | :-: | :-: | :-: |
| <img width="100" src="https://avatars.githubusercontent.com/u/2528830"/> | <img width="100" src="https://avatars.githubusercontent.com/u/31687149"/> | <img width="100" src="https://avatars.githubusercontent.com/u/27666983"/> | <img width="100" src="https://avatars.githubusercontent.com/u/107190140"/> |
| [sbwml](https://github.com/sbwml) | [jerrykuku](https://github.com/jerrykuku) | [Openwrt-Passwall](https://github.com/Openwrt-Passwall) | [vernesong](https://github.com/vernesong) |
| <img width="100" src="https://avatars.githubusercontent.com/u/16485166"/> | <img width="100" src="https://avatars.githubusercontent.com/u/9485680"/> | <img width="100" src="https://avatars.githubusercontent.com/u/253070042"/> | <img width="100" src="https://avatars.githubusercontent.com/u/42875168"/> |

## 许可证

本仓库的脚本、品牌素材与文档以 **GPL-2.0** 发布，见 [LICENSE](../../LICENSE)。

固件本身包含 OpenWrt、LEDE 以及大量上游组件，各自遵循原有许可证。分发固件镜像时同样要遵守这些许可证；特别是 GPL-2.0 要求提供对应的源码。

## 免责声明

刷机有变砖风险。动手之前请备份原厂固件和自己的配置，并先搞清楚救砖路径。固件按
现状提供，不附带任何担保。

---

维护者文档：[docs/BUILD.md](../BUILD.md) · 其他语言：[docs/readme](.)
