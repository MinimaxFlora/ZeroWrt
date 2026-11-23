# ZeroWrt

简体中文 · [English](README.md)

基于 Lean's LEDE 源码、由 GitHub Actions 自动编译的 **x86_64** 固件，**内置在线升级（OTA）**。
成品镜像与更新索引发布在 [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases)，
下载站是 [ota.tatalvpai.vip](https://ota.tatalvpai.vip/)。

[![Build](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/Trigger-All-Workflows.yml/badge.svg)](https://github.com/MinimaxFlora/ZeroWrt/actions/workflows/Trigger-All-Workflows.yml)
[![Release](https://img.shields.io/github/v/release/MinimaxFlora/ZeroWrt?label=release)](https://github.com/MinimaxFlora/ZeroWrt/releases)

## 这个仓库是什么

这里是**编译配置**，不是 OpenWrt 源码副本。构建时工作流会拉取
[coolsnowwolf/lede](https://github.com/coolsnowwolf/lede)，执行
[`diy-script.sh`](diy-script.sh) 打补丁、加软件源，再按配置编译并发布到 Release。

- 源码：`coolsnowwolf/lede`（`master`），Linux **7.3.x**
- 目标：`x86/64`（generic，EFI），产物 `*-squashfs-combined-efi.img.gz`
- 构建：GitHub Actions，每周定时 + 手动触发
- 默认地址 `10.0.0.1`，用户名 `root`，密码 `password`（首次登录后请立刻改掉）

## 包含什么

| 分类 | 内容 |
| --- | --- |
| 代理 / 分流 | PassWall、PassWall2（nftables TProxy）、nikki（mihomo-meta）、sing-box、Xray-core、shadowsocks-rust、ShadowsocksR-libev、simple-obfs、v2ray-plugin、microsocks、ipt2socks、dns2socks、Haproxy、geoview |
| DNS | mosdns、smartdns、chinadns-ng、v2ray-geoip / geosite，分流开箱可用 |
| 服务 | OpenList2、Lucky、frpc、ZeroTier、WireGuard、Samba4、SQM（CAKE）、DDNS（Cloudflare / GoDaddy / FreeDNS）、USB 打印机、AirConnect |
| 存储 | DiskMan、btrfs / XFS / exFAT / F2FS 工具、parted、smartmontools、zram-swap |
| 系统 | ttyd（局域网免登录）、Argon 与 Brutal 主题（默认 Brutal）、nano、yq、coreutils、ramfree |
| 升级 | **luci-app-ota**：检查、SHA256 校验下载、`sysupgrade -T` 预检、保留配置安装，另带命令行 `ota` |

以上插件均编译了简体中文语言包。

## 下载与安装

1. 到 [Releases](https://github.com/MinimaxFlora/ZeroWrt/releases/tag/X86_64) 或
   [下载站](https://ota.tatalvpai.vip/) 取最新镜像。
2. 写入硬盘或 U 盘（EFI 启动）：

   ```sh
   # Linux / macOS
   gunzip -c zerowrt-x86-64-generic-squashfs-combined-efi.img.gz | sudo dd of=/dev/sdX bs=4M status=progress
   ```

   Windows 下用 balenaEtcher 或 Rufus（DD 模式）写解压后的 `.img`。

3. 启动设备，浏览器打开 <http://10.0.0.1/>，SSH 用 `root` / `password`。
4. 磁盘比镜像大时扩容：**系统 → Disk Man** 选中根分区执行扩容（或 `cfdisk` + `resize2fs` /
   `mkfs.f2fs`），然后重启。

刷机前请用 Release 里的 `sha256sums` 校验镜像。

## 在线升级（OTA）

固件内置 [luci-app-ota](https://github.com/MinimaxFlora/luci-app-ota) 和默认索引地址，
装好之后不需要 U 盘就能升级：

- LuCI → **系统 → OTA Firmware Update（在线升级）**
- 页面读取 `/etc/ota/build.json` 的构建时间与索引里的条目比较
- 下载完成后强制校验 SHA256，并用 `sysupgrade -T` 预检镜像，不合格直接丢弃
- 安装默认保留配置（`sysupgrade` 保留设置）

命令行等价操作：

```sh
ota info                  # 本机固件信息 + 上次检查结果
ota check                 # 拉取索引并比较版本
ota download              # 后台开始下载
ota status                # 以 JSON 输出进度
ota apply --keep 1        # 安装，保留配置
```

索引在 <https://ota.tatalvpai.vip/ota.json>（schema 2，一台设备一个 key；x86 用 `x86_64+efi`）。
GitHub 下载慢可以在 **在线升级 → 配置** 里换加速站，默认 `gh-proxy.tatalvpai.vip`。

### OTA 是怎么接起来的

每次构建都会把自己的身份写进固件，并生成一条索引：

| 产物 | 由谁生成 | 作用 |
| --- | --- | --- |
| `/etc/ota/build.json` | `diy-script.sh` 调 `luci-app-ota/tools/embed_ota_meta.py` | 设备 key、目标平台、构建时间 |
| `/etc/uci-defaults/90-luci-app-ota` | `diy-script.sh` | 默认索引地址（仅在未配置时写入，用户改过的值优先） |
| `ota.json`（Release 附件） | [`scripts/gen_ota_index.py`](scripts/gen_ota_index.py) | 合并所有设备的索引 |
| `ota.json`（站点） | [Zerowrt-Website](https://github.com/MinimaxFlora/Zerowrt-Website) 的定时工作流 | 设备实际拉取的那份 |

设备 key 必须两边一致：x86 是 `x86_64` 加 `+efi` 启动变体，路由器用 profile 名
（例如 `ruijie_rg-x60-new`）。

## 自己编译

1. Fork 本仓库。
2. 改 [`configs/x86_64.config`](configs/x86_64.config)（软件包、目标平台）或
   [`diy-script.sh`](diy-script.sh)（源码补丁、额外软件源）。
3. 运行 **Actions → Trigger-All-Workflows → Run workflow**（每周五 18:00 UTC 也会自动跑）。
4. 产物发布到 `X86_64` 这个 Release tag，构建日志在 Actions 运行记录里。

说明：

- 工具链缓存按源码/目标区分，第一次构建慢，之后快很多。
- `diy-script.sh` 在 OpenWrt 源码树里执行，同时设置主机名、LAN 地址、默认密码、登录横幅，
  并把默认主题换成 Brutal。
- 加新设备 = 加一份 config + 一个调用 `Build-Release.yml` 的工作流，传入 `CONFIG_FILE`、
  `FIRMWARE_TAG`、`OTA_DEVICE`、`OTA_TARGET`。

## 目录结构

```
.github/workflows/Build-Release.yml   # 真正的构建：拉源码 → 配置 → 编译 → 发布
.github/workflows/X86_64.yml          # x86_64 入口（config 与 OTA 标识）
.github/workflows/Trigger-All-Workflows.yml
configs/x86_64.config                 # x86_64 的内核/软件包
diy-script.sh                         # 补丁、软件源、OTA 元数据、品牌信息
scripts/feeds.conf.default            # Lean 的软件源
scripts/gen_ota_index.py              # 由固件目录生成/合并 ota.json
images/                               # 主题背景图
```

## 常见问题

**只有 EFI 镜像？** 对。x86 只出 `combined-efi`，Release 里没有传统 BIOS 镜像，请用 UEFI 启动。

**磁盘比镜像大。** 首次启动后用 DiskMan 扩容 overlay 分区（或 `cfdisk` + `resize2fs` /
`mkfs.f2fs`）。

**怎么改 LAN 地址？** LuCI → 网络 → 接口 → LAN，或 `uci set network.lan.ipaddr=...`。

**OTA 提示「索引中没有适用于此设备的固件」。** 说明设备 key 没有对上：看 OTA 页面里的
*Device key*，确认它在 <https://ota.tatalvpai.vip/ota.json> 里存在；也可以在
在线升级 → 配置里手动指定。

## 致谢

基于 [coolsnowwolf/lede](https://github.com/coolsnowwolf/lede)。软件包来自 PassWall、
[nikkinikki-org/OpenWrt-nikki](https://github.com/nikkinikki-org/OpenWrt-nikki)、
[sbwml](https://github.com/sbwml)（mosdns、openlist2、diskman、airconnect、golang/rust）、
[gdy666/luci-app-lucky](https://github.com/gdy666/luci-app-lucky)、
[jerrykuku/luci-theme-argon](https://github.com/jerrykuku/luci-theme-argon) 与
[luci-theme-brutal](https://github.com/MinimaxFlora/luci-theme-brutal)。各组件的许可证随上游，
本仓库的脚本按现状提供，不附带任何担保。
