<div align="center">

<img src="assets/logo.png" width="88" alt="ZeroWrt" />

# ZeroWrt

### MT798x MediaTek Filogic 固件构建流水线

![Target](https://img.shields.io/badge/target-mediatek%2Ffilogic-2E9D72?style=flat-square)
![Source](https://img.shields.io/badge/source-immortalwrt--mt798x--6.6-1793d1?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--3.0-4c9c2f?style=flat-square)

[Releases](../../releases) · [Issues](../../issues) · [构建说明](docs/BUILD.md)

</div>

> [!IMPORTANT]
> 本仓库是 **ZeroWrt 的 Python 重写版**。安装编译依赖、清理/扩容磁盘、安装 LLVM
> 等 Runner 准备逻辑保留；固件定制、设备配置、插件替换、OTA 和产物发布全部重写为
> Python。工作流只调用 `scripts/zerowrt.py`。

## 这是什么

ZeroWrt 面向 **MediaTek Filogic（MT7986）** 路由器，源码固定为：

| 项目 | 值 |
| --- | --- |
| 源码仓库 | [`Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly`](https://github.com/Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly) |
| 分支 | `openwrt-24.10-6.6`（默认固定在 commit `6e1f514b`） |
| 目标 | `mediatek/filogic` |
| 配置来源 | `configs/<设备>.config`（`./scripts/diffconfig.sh` 生成的差异配置） |
| 发布 tag / Release | `mediatek_filogic` |

每次工作流只编译 **一个设备**。`config apply` 把 `configs/<设备>.config` 复制成
源码树的 `.config`，再执行一次 `make defconfig` 展开默认值；仓库里每个配置约 380 行，
不需要手工维护完整 `.config`。

## 支持设备

| 设备 | 布局 | 默认 LAN IP |
| --- | --- | --- |
| `netcore_n60-pro` — Netcore N60 Pro | Standard | `10.0.0.1` |
| `ruijie_ew-6000gx-pro` — Ruijie EW-6000GX Pro | Standard | `10.0.0.1` |
| `ruijie_ew-6000gx-pro-stock` — Ruijie EW-6000GX Pro | Stock | `10.0.0.1` |
| `ruijie_ew-6000gx-pro-expand` — Ruijie EW-6000GX Pro | Expand | `10.0.0.1` |
| `ruijie_ew-6000gx-pro-ubootmod` — Ruijie EW-6000GX Pro | U-Boot Mod | `10.0.0.1` |
| `ruijie_rg-x60-new` — Ruijie RG-X60 New | Standard | `10.0.0.1` |
| `ruijie_rg-x60-new-stock` — Ruijie RG-X60 New | Stock | `10.0.0.1` |
| `ruijie_rg-x60-new-expand` — Ruijie RG-X60 New | Expand | `10.0.0.1` |
| `ruijie_rg-x60-new-ubootmod` — Ruijie RG-X60 New | U-Boot Mod | `10.0.0.1` |
| `supergateway_s20l` — Super Gateway S20L | Standard | `10.0.0.1` |
| `supergateway_s20m` — Super Gateway S20M | Standard | `10.0.0.1` |
| `supergateway_s20p` — Super Gateway S20P | Standard | `10.0.0.1` |

> 所有设备默认 LAN IP 都是 `10.0.0.1`，可在工作流里修改。源码 `config_generate`
> 里的锐捷/非锐捷两个默认值都会被替换成同一个地址。

## 固件定制

| 项目 | 实现 |
| --- | --- |
| 删除 vendor 覆盖 | 删除源码根部 `files/etc`（避免旧 banner 覆盖 base-files） |
| 主机名 | `package/base-files/files/bin/config_generate` → `ZeroWrt` |
| LAN IP | 锐捷/非锐捷两个默认值统一为 `10.0.0.1`，可由 `lan_ip` 覆盖 |
| 发行版名 | `include/version.mk` 的 `VERSION_DIST` / `VERSION_MANUFACTURER` → `ZeroWrt` |
| 版本字符串 | `openwrt_release` → `DISTRIB_DESCRIPTION='ZeroWrt-YYYYMMDD'`、`DISTRIB_REVISION=' By MinimaxFlora'`；`os-release` → `ZeroWrt 标准版 @RYYYYMMDD BY MinimaxFlora` |
| 登录 banner | `assets/banner` → `package/base-files/files/etc/banner` |
| WiFi | `package/mtk/applications/mtwifi-cfg/files/mtwifi.sh`：`ZeroWrt-2.4G` / `ZeroWrt-5G`，`psk2`，默认密码 `1234567890` |
| Argon 主题 | 替换主题；配置页已合并进主题；背景 `assets/bg1.webp`；favicon/logo/图标由 `assets/favicon.ico` 生成；强制亮色；主色 `#EC4899`，暗色主色 `#BE185D` |
| LuCI 帮助与反馈 | 状态页加入项目主页、问题反馈、捐赠地址按钮，并补齐 `zh_Hans` 翻译 |
| 防火墙 zones | 删除 `Routing/NAT Offloading` / `Flow offloading type` 区块 |
| WireGuard | `luci-proto-wireguard` + `wireguard-tools` + `kmod-wireguard` |
| 设备配置 | 复制 `configs/<设备>.config`（diffconfig）后执行 `make defconfig` |
| 插件 | 3cat、ACME、Argon 主题、ARP Bind、Commands、DDNS、OpenClash、PassWall、RamFree、TTYD、UPnP、OTA、WireGuard |
| PassWall | 只启用 Xray，显式关闭 Sing-Box（MTK 镜像体积考虑） |
| DDNS | 阿里云、Cloudflare、DNSPod、FreeDNS、GoDaddy |
| OTA | [`MinimaxFlora/luci-app-ota`](https://github.com/MinimaxFlora/luci-app-ota) |
| Go | 替换为 [`sbwml/packages_lang_golang`](https://github.com/sbwml/packages_lang_golang) `27.x`（Xray 需要 Go 1.27） |

## 插件替换

在 `./scripts/feeds update -a && ./scripts/feeds install -a` 之后执行：

| 替换 | 来源 | 位置 |
| --- | --- | --- |
| PassWall | `Openwrt-Passwall/openwrt-passwall` | `package/new/openwrt-passwall` |
| PassWall 依赖 | `Openwrt-Passwall/openwrt-passwall-packages` | `package/new/openwrt-passwall-packages` |
| OpenClash | `vernesong/OpenClash` | `package/new/OpenClash` |
| Argon 主题（含配置页） | `jerrykuku/luci-theme-argon` | `package/new/luci-theme-argon` |
| OTA | `MinimaxFlora/luci-app-ota` | `package/new/luci-app-ota` |
| Go 1.27 | `sbwml/packages_lang_golang` | 替换 `feeds/packages/lang/golang` |

外部包都固定到 commit（见 `packages.py`），不会跟随分支头漂移；更新时改常量并重新生成 configs。

`package/new` 里出现的同名包会从 `feeds/` 和 `package/feeds/` 中删除，避免 buildroot
静默选到旧版本。`openwrt-passwall-packages` 中的 `sing-box` 会在克隆后删除，feed 里的
`sing-box` 也会一并移除。旧的独立 `luci-app-argon-config` feed 包会被删除，配置页使用
`luci-theme-argon` 内置版本。

## 使用工作流

进入 **Actions → Build ZeroWrt → Run workflow**：

| 输入 | 默认值 | 说明 |
| --- | --- | --- |
| `device` | `netcore_n60-pro` | 只编译一个设备 |
| `lan_ip` | `10.0.0.1` | 所有设备统一的 LAN IP，可修改 |
| `root_password` | 必填 | 至少 8 位，不提供默认密码 |
| `wifi_name` | `ZeroWrt` | 自动追加 `-2.4G` / `-5G` |
| `wifi_password` | `1234567890` | 8–63 位 |
| `ota_url` | `https://ota.tatalvpai.vip/ota.json` | 默认 OTA 索引地址 |
| `ota_cname` | `ota.tatalvpai.vip` | OTA 下载页域名 |
| `cache_toolchain` | `true` | 有缓存时恢复工具链 |

构建成功后：

1. 上传 Artifact（仅固件，保留 14 天）；
2. 更新 tag / Release 名均为 `mediatek_filogic` 的 Release；
3. 把 `ota.json`、`history.json` 和下载页推送到 `gh-pages`。

## 产物

Release 和 Artifact **只包含固件**，不会上传：

`config.buildinfo`、`feeds.buildinfo`、`profiles.json`、`sha256sums`、
`version.buildinfo`、`*.manifest`、`mt7981-ram-ddr3-bl2.bin`、
`mt7981-ram-ddr4-bl2.bin`、`mt7986-ram-ddr3-bl2.bin`、`mt7986-ram-ddr4-bl2.bin`、
`mt7988-ram-comb-bl2.bin`。

典型文件：

```text
zerowrt-mediatek-filogic-netcore_n60-pro-initramfs-kernel.bin
zerowrt-mediatek-filogic-netcore_n60-pro-squashfs-sysupgrade.bin
zerowrt-mediatek-filogic-ruijie_rg-x60-new-ubootmod-bl31-uboot.fip
zerowrt-mediatek-filogic-ruijie_rg-x60-new-ubootmod-initramfs-recovery.itb
zerowrt-mediatek-filogic-ruijie_rg-x60-new-ubootmod-preloader.bin
zerowrt-mediatek-filogic-ruijie_rg-x60-new-ubootmod-squashfs-sysupgrade.itb
```

## 工具链缓存

`Build Toolchain Cache` 工作流：

- tag：`toolchain`
- Release 名：`Toolchain_Cache`
- 资产：`toolchain_<libc>_<arch>_gcc-<major>.tar.zst`

固件构建在 `make download` 前恢复缓存；没有缓存时只警告，工具链照常编译。

## 本地开发

构建依赖和编译步骤只支持 Linux（与 GitHub Actions 的 Ubuntu 24.04 一致）。
在 Linux 上：

```bash
export ZEROWRT_SOURCE_DIR=/builder/source
export ZEROWRT_DEVICE=netcore_n60-pro
export ZEROWRT_ROOT_PASSWORD='change-me-please'

python3 scripts/zerowrt.py system free-disk --build-dir /builder
python3 scripts/zerowrt.py system install-deps
python3 scripts/zerowrt.py system install-llvm
python3 scripts/zerowrt.py source clone --dest "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py source feeds-update --tree "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py source feeds-install --tree "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py packages add --tree "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py source customize --tree "$ZEROWRT_SOURCE_DIR" --assets assets
python3 scripts/zerowrt.py config apply --tree "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py ota embed --tree "$ZEROWRT_SOURCE_DIR" \
  --api-url https://example.com/ota.json
python3 scripts/zerowrt.py build download --tree "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py build compile --tree "$ZEROWRT_SOURCE_DIR"
python3 scripts/zerowrt.py build collect --tree "$ZEROWRT_SOURCE_DIR" --out dist
```

单元测试不需要 Linux、不需要联网、不调用 `make`/`apt`：

```bash
python -m unittest discover -v
python -m ruff check scripts tests
```

## 目录结构

```text
.
├── assets/                         # banner、Argon 背景、favicon
├── configs/                        # 12 个设备的 diffconfig 差异配置
├── docs/
│   ├── BUILD.md                    # 构建与维护文档
│   └── release-notes/              # Release 正文
├── scripts/
│   ├── zerowrt.py                  # CLI 入口
│   └── zerowrt_core/
│       ├── build.py                # 下载/编译/只收集固件
│       ├── cache.py                # toolchain Release 缓存
│       ├── config.py               # 复制 configs/<设备>.config / 批量生成
│       ├── customize.py            # 版本/IP/WiFi/banner/Argon
│       ├── luci.py                 # 状态页帮助反馈 + zh_Hans 翻译
│       ├── ota.py                  # OTA 元数据、索引、gh-pages
│       ├── packages.py             # 插件替换与 feed 去重
│       ├── profiles.py             # 12 个设备
│       ├── settings.py             # 输入校验
│       ├── source.py               # clone/feeds
│       ├── state.py                # .zerowrt-info.json
│       ├── sysops.py               # 依赖/扩容/LLVM
│       └── util.py                 # 通用工具
├── tests/                          # 不联网单元测试
└── .github/workflows/              # build / toolchain / quality
```

## 常见问题

**为什么 Release 里只有固件？**
`build collect` 只匹配 initramfs-kernel、squashfs-sysupgrade、U-Boot Mod 的
`bl31-uboot.fip` / `preloader.bin` / `initramfs-recovery.itb`。manifests、buildinfo、
profiles.json、sha256sums 和 DDR bl2 都不会进入 `dist/`。

**为什么 tag 和 Release 都叫 `mediatek_filogic`？**
同一 Release 会累积不同设备的固件；每次只上传本次设备。OTA 索引按设备 key 合并，
不会覆盖其它设备。

**为什么 PassWall 没有 Sing-Box？**
`sing-box` 源码已删除，`.config` 里显式
`# CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox is not set`，并检查
`CONFIG_PACKAGE_sing-box` 没有变成 `=y`。

**为什么所有设备都是 10.0.0.1？**
上游 `config_generate` 原本按 board 分成锐捷 `192.168.110.1` 和非锐捷 `192.168.6.1`
两支。ZeroWrt 把两个 LAN 默认值都替换成统一的 `10.0.0.1`，工作流 `lan_ip` 可覆盖；
非 LAN 接口的 `192.168.$((addr_offset++)).1` 不动。

**WireGuard 在哪里配置？**
固件包含 `luci-proto-wireguard`、`wireguard-tools` 和 `kmod-wireguard`。在
**网络 → 接口 → 添加新接口 → 协议 WireGuard VPN** 中配置。

**Argon 配置页还需要单独装 `luci-app-argon-config` 吗？**
不需要。新版 Argon 已把配置页合并进 `luci-theme-argon`，本仓库不再克隆独立包，并会
删除 feed 里的旧 `luci-app-argon-config`。

## 致谢

源码来自 [Yuzhii0718](https://github.com/Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly)、
[ImmortalWrt](https://github.com/immortalwrt)、[OpenWrt](https://github.com/openwrt)；
插件来自 [Openwrt-Passwall](https://github.com/Openwrt-Passwall)、
[vernesong/OpenClash](https://github.com/vernesong/OpenClash)、
[jerrykuku](https://github.com/jerrykuku)、
[sbwml](https://github.com/sbwml) 和
[MinimaxFlora](https://github.com/MinimaxFlora)。

## 许可

GPL-3.0，见 [LICENSE](LICENSE)。固件包含 OpenWrt、ImmortalWrt 及第三方组件，
分发镜像时请同时遵守它们的许可证。
