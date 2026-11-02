<div align="center">

<img src="assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### MT798x 固件构建流水线，一条命令编译，一键在线升级。

![Target](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![Source](https://img.shields.io/badge/source-ImmortalWrt%2025.12-1793d1?style=flat-square)
![Device](https://img.shields.io/badge/device-Ruijie%20RG--X60%20New-E45A1B?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--3.0-4c9c2f?style=flat-square)

[Releases](../../releases) · [Issues](../../issues) · [构建说明](docs/BUILD.md)

</div>

> [!IMPORTANT]
> 本仓库是 **ZeroWrt 的 Python 重写版**。设备配置、补丁和固件定制流程来自
> [OpenWrt_MediaTek_Builder](https://github.com/MinimaxFlora/OpenWrt_MediaTek_Builder)，
> 构建依赖、LLVM、并行编译和工具链缓存来自
> [ZeroWrt](https://github.com/MinimaxFlora/ZeroWrt)。
> 构建时不再执行仓库里的 shell 脚本，所有步骤都由 `scripts/zerowrt.py` 完成。

---

## 这是什么

ZeroWrt 是一套面向 MT798x 路由器的自建固件流水线。源码来自公开的
[`chasey-dev/immortalwrt-mt798x-rebase`](https://github.com/chasey-dev/immortalwrt-mt798x-rebase)
`25.12` 分支，设备配置沿用 MediaTek Builder 的
[`configs/ruijie-rg-x60-new.config`](configs/ruijie-rg-x60-new.config)，
并在其中加入 **luci-app-ota**，让设备可以在 LuCI 里检查、下载、校验并安装新固件。

一次完整构建在 GitHub Actions 上大约 30–60 分钟（首次没有工具链缓存时更久），
产物包括：

```text
zerowrt-mediatek-filogic-ruijie_rg-x60-new-mtkuboot-squashfs-sysupgrade.bin
Packages.tar.gz
build.config
BUILD_INFO.txt
SHA256SUMS
ota.json
```

Release tag 使用设备 profile 名 `ruijie_rg-x60-new`。同一 tag 再次构建会覆盖旧资产，
OTA 索引则按 `build_date` 判断新旧。

## 支持设备

| 设备 | 源码 | 布局 | OTA key |
| --- | --- | --- | --- |
| 锐捷 RG-X60 New | immortalwrt-mt798x-rebase `25.12` | MTK U-Boot（mtkuboot） | `ruijie_rg-x60-new-mtkuboot` |

> **从旧 ZeroWrt 升级前请先确认分区布局。** 旧 ZeroWrt 使用 `ubootmod`，
> 这里使用 `mtkuboot`，两者镜像不能直接互刷。请从 U-Boot 恢复页按对应布局刷入，
> 第一次切换时不要保留配置。

## 功能

- **配置来自 `configs/`**：`ruijie-rg-x60-new.config` 原样保留，Python 只追加 OTA
  必需项并检查 `defconfig` 有没有丢掉关键包。
- **完整设备定制**：LAN IP、root 密码、WiFi SSID/密码、bash、ttyd 免登录、
  登录 banner、版本字符串、MTK WiFi 默认值。
- **补丁已刷新**：`0001`–`0005` 重新基于 `immortalwrt/luci` `openwrt-25.12`
  生成，`0006` 为 GCC 16 工具链补丁，两个 `900-*` 包补丁已对照
  libwebsockets 4.4.1 / elfutils 0.192 验证。
- **LLVM + GCC 16**：预装 Clang 工具链，主工具链使用配置选择的 GCC 16。
- **编译策略**：`nproc + 1` 并行、按可用内存限流、`IGNORE_ERRORS="n m"`，
  失败后自动串行 `V=s` 重试。
- **工具链缓存**：可从 `toolchain` Release 恢复 `build_dir/dl/staging_dir/tmp`，
  跳过最耗时的工具链编译。
- **OTA 更新**：构建时写入 `/etc/ota/build.json`，发布时生成
  `ota.json`/`history.json` 到 `gh-pages`，设备端使用 `luci-app-ota` 一键升级。
- **纯 Python**：workflow 只调用 CLI，不再维护大段 `sed`/`curl` shell。

## 快速开始

进入 **Actions → Build ZeroWrt → Run workflow**，填写：

| 输入 | 默认值 | 说明 |
| --- | --- | --- |
| `device` | `ruijie_rg-x60-new` | 设备 profile |
| `lan_ip` | `10.0.0.1` | 管理地址 / LAN IP |
| `root_password` | `password` | root 密码，至少 8 位；**首次登录请立即修改** |
| `wifi_name` | `ZeroWrt` | SSID 前缀，自动追加 `-2.4G` / `-5G` / `-6G` |
| `wifi_password` | `1234567890` | WiFi 密码，8–63 位安全字符 |
| `ota_url` | 空 | 留空时使用 `https://<owner>.github.io/<repo>/ota.json` |
| `ota_cname` | 空 | 自定义下载页域名，写入 `gh-pages` 的 `CNAME` |
| `cache_toolchain` | `true` | 有缓存时恢复工具链 |

构建成功后会自动：

1. 上传 Artifact（保留 14 天）；
2. 创建/更新 tag 为 `ruijie_rg-x60-new` 的 Release；
3. 把 `ota.json`、`history.json` 和下载页推送到 `gh-pages`。

### 启用 GitHub Pages

仓库 **Settings → Pages** 选择 **Deploy from a branch**，分支 `gh-pages`、目录 `/`。
如果 `ota_url` 留空，固件会检查：

```text
https://<owner>.github.io/<repo>/ota.json
```

使用自定义域名时，把域名填到 `ota_cname`，并在 DNS 添加指向
`<owner>.github.io` 的 CNAME（Cloudflare 请设为 DNS only）。

## 在设备上升级

固件内置 `luci-app-ota`：

**系统 → 在线升级 → 检查更新**，然后下载并安装。索引地址、是否允许不安全连接、
是否保留配置等都在 **在线升级 → 配置** 里。

安全策略：

- 索引必须是 `https`（除非显式允许不安全连接）；
- 索引条目必须带 SHA256，缺失直接拒绝；
- 下载完成后校验 SHA256，并用 `sysupgrade -T` 预检镜像；
- 校验失败的文件会被删除。

## 本地构建

构建依赖和编译步骤只支持 Linux（GitHub Actions 使用 Ubuntu 24.04）。
在 Linux 上：

```bash
export ZEROWRT_SOURCE_DIR=/builder/source
export ZEROWRT_DEVICE=ruijie_rg-x60-new

python3 scripts/zerowrt.py system free-disk --build-dir /builder
python3 scripts/zerowrt.py system install-deps
python3 scripts/zerowrt.py system install-llvm
python3 scripts/zerowrt.py source clone --dest "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py source feeds-update --tree "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py source feeds-install --tree "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py packages add --tree "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py source customize --tree "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py patches apply --tree "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py config apply --tree "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py ota embed --tree "$ZEROWRT_SOURCE_DIR" --api-url https://example.com/ota.json
python3 scripts/zerowrt.py build download --tree "$ZEROWRT_SOURCE_DIR" --jobs "$(nproc)"
python3 scripts/zerowrt.py build compile --tree "$ZEROWRT_SOURCE_DIR" --jobs "$(nproc)"
python3 scripts/zerowrt.py build collect --tree "$ZEROWRT_SOURCE_DIR" --out dist
python3 scripts/zerowrt.py ota index --tree "$ZEROWRT_SOURCE_DIR" --dist dist \
  --repo <owner>/<repo> --tag ruijie_rg-x60-new
```

完整参数、目录说明和补丁刷新方法见 [docs/BUILD.md](docs/BUILD.md)。

## 目录结构

```text
.
├── configs/ruijie-rg-x60-new.config   # 设备 .config（MediaTek Builder 原文件）
├── assets/                            # banner、logo
├── scripts/
│   ├── zerowrt.py                     # CLI 入口
│   ├── zerowrt_core/                  # sysops/source/packages/customize/config/
│   │                                  # patches/build/ota/cache/state
│   └── 000*.patch, 900-*.patch        # 已刷新/已验证的补丁
├── tests/                             # 不联网的单元测试
├── docs/BUILD.md                      # 构建与维护文档
└── .github/workflows/                 # build / toolchain / quality
```

## 补丁说明

| 补丁 | 作用 | 基线 |
| --- | --- | --- |
| `0001` | 状态页帮助/反馈按钮 | luci `openwrt-25.12` |
| `0002` | 帮助链接中文翻译 | luci `openwrt-25.12` |
| `0003` | 防火墙移除 flow offloading 设置 | luci `openwrt-25.12` |
| `0004` | 重启确认弹窗 | luci `openwrt-25.12` |
| `0005` | 状态页网络速率 | luci `openwrt-25.12` |
| `0006` | GCC 16 工具链支持 | rebase `25.12` |
| `900-fix-build-for-gcc-16` | libwebsockets 4.4.1 GCC 16 修复 | 包源码 |
| `900-fix-gcc16-null-dereference-with-lto` | elfutils 0.192 LTO 空指针修复 | 包源码 |

`0001`–`0005` 的 `index` 行和行号已按当前 LuCI 基线重新生成，应用时偏移为 0。
上游更新后如果补丁失效，构建会在 `patches apply` 阶段直接失败并打印 `git apply`
的上下文，而不是带着旧代码继续编译。

## 常见问题

**为什么不用 `scripts/feeds update -a` 再跑一次？**
补丁应用后再 `update` 会 `git pull`，可能覆盖补丁或因为本地修改失败。本流水线只在
最前面 update 一次，最后只 `install -a`，再清理与 `package/new` 重名的 feed 包。

**为什么 Docker 包被克隆了却没有进固件？**
`configs/ruijie-rg-x60-new.config` 没有选中 Docker。保留克隆是为了需要时只改一行
配置即可启用，不会增加默认镜像体积。

**工具链缓存什么时候需要重建？**
目标架构、libc 或 GCC 大版本变化后。缓存文件名带 `gcc-<major>`，但不同小版本仍可能
不兼容；换 GCC 后请重新运行 **Build Toolchain Cache**。

**OTA 检查提示“索引中没有适用于此设备的固件”？**
索引 key 是 `ruijie_rg-x60-new-mtkuboot`。确认 `ota.json` 的 `devices` 里存在该 key，
以及固件内 `/etc/ota/build.json` 的 `device` 与之一致。

## 致谢

设备配置、补丁和定制流程来自
[OpenWrt_MediaTek_Builder](https://github.com/MinimaxFlora/OpenWrt_MediaTek_Builder)；
Python 架构、依赖安装、LLVM、编译与 OTA 思路来自
[ZeroWrt](https://github.com/MinimaxFlora/ZeroWrt)；
源码来自 [chasey-dev](https://github.com/chasey-dev/immortalwrt-mt798x-rebase)、
[ImmortalWrt](https://github.com/immortalwrt)、
[OpenWrt](https://github.com/openwrt) 及各自上游。

## 许可

本项目以 **GPL-3.0** 发布，见 [LICENSE](LICENSE)。固件本身包含 OpenWrt、
ImmortalWrt 及大量第三方组件， redistributing 镜像时请同时遵守它们的许可证。
