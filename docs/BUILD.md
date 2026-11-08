# 构建与维护

本文档面向维护者：说明每个构建步骤、固件定制点、设备配置如何从高功率模板生成，
以及 OTA 与工具链缓存的工作方式。

## 1. 源码与目标

| 项目 | 值 |
| --- | --- |
| 源码仓库 | `Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly` |
| 分支 | `openwrt-24.10-6.6` |
| 目标 | `mediatek/filogic` |
| 内核 | 6.6 |
| 设备配置模板 | `defconfig/mt7975-ipailna-high-power.config` |
| 配置生成 | `scripts/zerowrt_core/config.py` |
| Release tag | `mediatek_filogic` |

源码是公开仓库，不需要 `SOURCE_TOKEN`。需要写权限的是 `GITHUB_TOKEN`
（Actions 自动提供），用于 Release 和 `gh-pages`。

## 2. 工作流顺序

`build.yml` 的顺序不是随意的：

1. **free-disk**：删除 runner 上无用的 SDK，必要时用 LVM 合并 `/` 与 `/mnt`，
   创建 swap。根分区已经足够大时跳过清理。
2. **install-deps**：安装 OpenWrt 编译依赖、`ccache`、`lvm2`、`xfsprogs`、
   Python/Pillow 等。
3. **install-llvm**：下载 sbwml 的 Clang 到 `/opt/clang`，写入 `GITHUB_PATH`。
4. **source clone**：克隆源码，校验关键文件，写入 `.zerowrt-info.json`
   （仓库、分支、commit、构建日期、设备）。
5. **feeds update**：`./scripts/feeds update -a`，确认 `feeds/luci`、`feeds/packages`。
6. **feeds install**：`./scripts/feeds install -a`，确认 `luci-compat`、`lyaml`、
   `ttyd`、`3proxy` 已安装。
7. **packages add**：见第 3 节。必须在 `feeds install` 之后，因为替换包需要
   `luci.mk` 和 feed 符号链接已经存在。
8. **source customize**：删除 `files/etc`、版本、IP、banner、root 密码、WiFi、
   Argon。见第 4 节。
9. **config apply**：从高功率模板生成单设备 `.config`，追加插件，执行
   `make defconfig` 并逐项校验。见第 5 节。
10. **ota embed**：写 `/etc/ota/build.json`、`/etc/uci-defaults/90-luci-app-ota`
    和 `version.date`。
11. **cache restore**（可选）：从 `toolchain` Release 恢复
    `build_dir/dl/staging_dir/tmp`。
12. **build download**：`make -jN download`，失败后串行重试。
13. **build compile**：`make -j(nproc+1) IGNORE_ERRORS="n m"`，失败后
    `make -j1 ... V=s`。
14. **build collect**：只收集固件，见第 7 节。
15. **Release**：tag 和 Release 名都是 `mediatek_filogic`，正文来自
    `docs/release-notes/mediatek_filogic.md`。
16. **ota publish**：把 `ota.json`、`history.json` 和下载页推送到 `gh-pages`。

## 3. 插件替换

在 `package/new` 下克隆：

| 目录 | 仓库 | 分支 |
| --- | --- | --- |
| `openwrt-passwall` | `Openwrt-Passwall/openwrt-passwall` | `main` |
| `openwrt-passwall-packages` | `Openwrt-Passwall/openwrt-passwall-packages` | `main` |
| `OpenClash` | `vernesong/OpenClash` | `master` |
| `luci-theme-argon` | `jerrykuku/luci-theme-argon` | `master` |
| `luci-app-ota` | `MinimaxFlora/luci-app-ota` | `main` |

Go 1.27 不放在 `package/new`，而是替换 feed 目录：

```text
feeds/packages/lang/golang  <-  sbwml/packages_lang_golang @ 27.x
```

`openwrt-passwall-packages/sing-box` 克隆后立即删除，`feeds/packages/net/sing-box`
和对应的 `package/feeds` 链接也删除。PassWall 仍可在 menuconfig 里看到 Sing-Box
选项，但 `.config` 显式关闭，且源码不存在时不会被编进镜像。

### 3.1 feed 去重

`packages.py` 会扫描 `package/new` 下所有 `Makefile`，收集：

- `PKG_NAME`
- `LUCI_NAME`
- `BuildPackage,<name>`
- Makefile 所在目录名

然后删除：

- `feeds/**` 中声明了同名包的目录；
- `package/feeds/**` 中同名的符号链接；
- 删除 feed 目录后变成悬空的符号链接。

这一步是必须的：buildroot 会同时扫描 `feeds/` 和 `package/new`，同名包不会报错，
而是静默选其中一个。

### 3.2 Argon 配置页

新版 Argon 已把配置页合并进 `luci-theme-argon`。本仓库：

- 只克隆 `luci-theme-argon`；
- 删除主题仓库里的 `compat/` 兼容包；
- 删除 feed 里的旧 `luci-app-argon-config` 目录和符号链接；
- `.config` 只选 `luci-theme-argon`，配置页由主题提供。

这样不会出现两个 Argon 配置页，也不会因为旧 feed 包覆盖主题文件。

## 4. 固件定制

### 4.1 删除 files/etc

源码根部的 `files/etc` 会覆盖 `package/base-files/files`。本仓库先删除
`files/etc`（上游当前只有 `banner`），再写：

```text
package/base-files/files/etc/banner
```

### 4.2 主机名与 LAN IP

修改：

```text
package/base-files/files/bin/config_generate
```

- `hostname='ImmortalWrt'` → `hostname='ZeroWrt'`。
- 上游 LAN IP 有两支：锐捷 `192.168.110.1`，其它 `192.168.6.1`。
- ZeroWrt 把这两个默认值都替换成统一地址，默认 `10.0.0.1`：

```sh
case "$board" in
    ruijie,ew-6000gx-pro*|ruijie,rg-x60*)
        ipad=${ipaddr:-"10.0.0.1"}
    ;;
    *)
        ipad=${ipaddr:-"10.0.0.1"}
    ;;
esac
```

`lan_ip` 工作流输入可覆盖为其它地址；两个 LAN 默认值始终一起替换。非 LAN 接口的
`192.168.$((addr_offset++)).1` 保持原样。

### 4.3 版本

`include/version.mk`：

```make
VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),ZeroWrt)
VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),ZeroWrt)
```

不修改 `VERSION_NUMBER`。镜像前缀由 `VERSION_DIST_SANITIZED` 决定，结果是
`zerowrt-mediatek-filogic-<device>-...`。

`package/base-files/files/etc/openwrt_release`：

```sh
DISTRIB_DESCRIPTION='ZeroWrt-YYYYMMDD'
DISTRIB_REVISION=' By MinimaxFlora'
```

`package/base-files/files/usr/lib/os-release`：

```sh
OPENWRT_RELEASE="ZeroWrt 标准版 @RYYYYMMDD BY MinimaxFlora"
```

日期取 `.zerowrt-info.json` 的 `build_date`，按 `Asia/Shanghai` 格式化。

### 4.4 WiFi

修改：

```text
package/mtk/applications/mtwifi-cfg/files/mtwifi.sh
```

- `ssid="ImmortalWrt-2.4G"` → `ssid="ZeroWrt-2.4G"`
- `ssid="ImmortalWrt-5G"` → `ssid="ZeroWrt-5G"`
- `encryption=none` → `encryption=psk2`，并追加 `key='1234567890'`
- SSID 传给 UCI 时加单引号，避免名称含空格时被拆开

默认密码是 `1234567890`，可通过工作流 `wifi_password` 修改。

### 4.5 Argon

替换的是 `package/new/luci-theme-argon`：

| 文件 | 来源 |
| --- | --- |
| `htdocs/luci-static/argon/img/bg1.webp` | `assets/bg1.webp` |
| `htdocs/luci-static/argon/favicon.ico` | `assets/favicon.ico` |
| `htdocs/luci-static/argon/img/argon.svg` | 由 favicon 生成，内嵌 PNG data URI |
| `htdocs/luci-static/argon/icon/android-icon-192x192.png` | favicon → 192×192 |
| `htdocs/luci-static/argon/icon/apple-icon-144x144.png` | favicon → 144×144 |
| `htdocs/luci-static/argon/icon/favicon-16x16.png` | favicon → 16×16 |
| `htdocs/luci-static/argon/icon/favicon-32x32.png` | favicon → 32×32 |

`root/etc/config/argon`：

```uci
option mode 'light'
option primary '#EC4899'
option dark_primary '#BE185D'
option dark_primary_mode 'custom'
```

`mode 'light'` 是强制亮色；`dark_primary` 仍然写入，用户手动切到暗色时使用。

### 4.6 root 密码

`package/base-files/files/etc/shadow` 的 root 条目用
`openssl passwd -5 -stdin` 生成 SHA-256 crypt。密码不会出现在命令行或日志里。
默认 `password`，工作流输入可覆盖；首次登录请修改。

## 5. 单设备 .config

### 5.1 模板

基础文件是源码里的：

```text
defconfig/mt7975-ipailna-high-power.config
```

它提供 MTK WiFi、HNAT、TurboACC 等高功率配置，但也默认选中：

- `mediatek/mt7986` 旧目标；
- GL.iNet、TP-Link、Xiaomi 等设备；
- Ruijie 的 8 个布局。

### 5.2 删除与添加

`config.py` 删除所有 `CONFIG_TARGET_DEVICE_*`、`CONFIG_TARGET_MULTI_PROFILE`、
`CONFIG_TARGET_PER_DEVICE_ROOTFS`、`CONFIG_TARGET_PROFILE`、`CONFIG_TARGET_BOARD`、
`CONFIG_TARGET_SUBTARGET`、`CONFIG_TARGET_ARCH_PACKAGES` 和
`CONFIG_TARGET_mediatek*` 选择，但保留 `CONFIG_TARGET_ROOTFS_*`、内核分区等镜像选项。

然后只添加：

```ini
CONFIG_TARGET_mediatek=y
CONFIG_TARGET_mediatek_filogic=y
CONFIG_TARGET_MULTI_PROFILE=y
CONFIG_TARGET_PER_DEVICE_ROOTFS=y
CONFIG_TARGET_DEVICE_mediatek_filogic_DEVICE_<device>=y
CONFIG_TARGET_DEVICE_PACKAGES_mediatek_filogic_DEVICE_<device>=""
```

`CONFIG_TARGET_MULTI_PROFILE=y` 和 `CONFIG_TARGET_PER_DEVICE_ROOTFS=y` 不是多选设备，
而是让 Kconfig 暴露 “Target Devices” 菜单和按设备 rootfs；实际设备仍然只有一行
`CONFIG_TARGET_DEVICE_...=y`。

### 5.3 插件选择

```ini
CONFIG_PACKAGE_luci-app-3cat=y
CONFIG_PACKAGE_luci-app-acme=y
CONFIG_PACKAGE_luci-theme-argon=y
CONFIG_PACKAGE_luci-app-arpbind=y
CONFIG_PACKAGE_luci-app-commands=y
CONFIG_PACKAGE_luci-app-ddns=y
CONFIG_PACKAGE_luci-app-openclash=y
CONFIG_PACKAGE_luci-app-passwall=y
CONFIG_PACKAGE_luci-app-ramfree=y
CONFIG_PACKAGE_luci-app-ttyd=y
CONFIG_PACKAGE_luci-app-upnp=y
CONFIG_PACKAGE_luci-app-ota=y
CONFIG_PACKAGE_luci-i18n-ota-zh-cn=y

CONFIG_PACKAGE_luci-proto-wireguard=y
CONFIG_PACKAGE_wireguard-tools=y
CONFIG_PACKAGE_kmod-wireguard=y

CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray=y
# CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox is not set
# CONFIG_PACKAGE_sing-box is not set

CONFIG_PACKAGE_ddns-scripts-aliyun=y
CONFIG_PACKAGE_ddns-scripts-cloudflare=y
CONFIG_PACKAGE_ddns-scripts-dnspod=y
CONFIG_PACKAGE_ddns-scripts-freedns=y
CONFIG_PACKAGE_ddns-scripts-godaddy=y
```

DDNS 使用 feed 中的实际包名
`ddns-scripts-aliyun` / `-cloudflare` / `-dnspod` / `-freedns` / `-godaddy`，
不是旧配置里的 `ddns-scripts_aliyun` 兼容名。

### 5.4 defconfig 校验

`make defconfig` 后检查：

- 本次设备是唯一被选中的 `CONFIG_TARGET_DEVICE_*_DEVICE_*=y`；
- `mediatek/filogic` 目标存在；
- 12 个插件、OTA、DDNS、WireGuard、MTK 加速包都存在；
- `CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox` 和
  `CONFIG_PACKAGE_sing-box` 没有变成 `=y`。

任何一项缺失都会直接失败，并打印 `defconfig.log` 末尾，避免带着错误配置编译数小时。

Netcore N60 Pro 的 `make defconfig` 前配置预览见
[`docs/config/netcore_n60-pro.seed.config`](config/netcore_n60-pro.seed.config)，
在真实源码树上执行 `make defconfig` 后的最终配置见
[`docs/config/netcore_n60-pro.final.config`](config/netcore_n60-pro.final.config)。

## 6. OTA

### 6.1 固件内元数据

`ota embed` 写：

```json
{
  "dist": "ZeroWrt",
  "version": "20261108",
  "device": "netcore_n60-pro",
  "model": "",
  "target": "mediatek/filogic",
  "build_date": 1762524000,
  "product": "Netcore N60 Pro"
}
```

写入位置：

```text
package/base-files/files/etc/ota/build.json
```

同时写 `version.date`，并生成首次启动默认索引地址：

```text
package/base-files/files/etc/uci-defaults/90-luci-app-ota
```

### 6.2 索引

`ota publish` 生成 schema 2：

```json
{
  "schema": 2,
  "dist": "ZeroWrt",
  "devices": {
    "netcore_n60-pro": {
      "version": "20261108",
      "build_date": 1762524000,
      "url": "https://github.com/<owner>/<repo>/releases/download/mediatek_filogic/<image>",
      "sha256": "...",
      "size": 0,
      "file": "<image>",
      "target": "mediatek/filogic",
      "device": "netcore_n60-pro",
      "label": "Netcore N60 Pro"
    }
  }
}
```

`publish` 会：

1. clone `gh-pages`（不存在则创建）；
2. 复制 `luci-app-ota/site`，删除上游 `CNAME`（除非显式传 `--cname`）；
3. 合并已有 `ota.json` 的其它设备条目；
4. 追加 `history.json`；
5. 用 `GITHUB_TOKEN` 推回。

### 6.3 Pages

Settings → Pages → Deploy from a branch → `gh-pages` / `/`。
默认索引地址：`https://ota.tatalvpai.vip/ota.json`。

## 7. 产物过滤

`build.py` 只匹配：

```text
*-initramfs-kernel.bin
*-squashfs-sysupgrade.bin
*-squashfs-sysupgrade.itb
*-initramfs-recovery.itb
*-bl31-uboot.fip
*-preloader.bin
```

不会收集：

```text
config.buildinfo
feeds.buildinfo
profiles.json
sha256sums
version.buildinfo
*.manifest
mt7981-ram-ddr3-bl2.bin
mt7981-ram-ddr4-bl2.bin
mt7986-ram-ddr3-bl2.bin
mt7986-ram-ddr4-bl2.bin
mt7988-ram-comb-bl2.bin
```

还会检查：

- 至少有一个 `squashfs-sysupgrade`；
- 每个文件名以 `zerowrt-` 开头（防止 `VERSION_DIST` 没生效）。

## 8. 工具链缓存

`toolchain.yml` 编译 `make toolchain/compile`，然后：

```bash
python3 scripts/zerowrt.py cache save \
  --tree /builder/source \
  --repo <owner>/<repo>
```

资产名从 `staging_dir/toolchain-*` 推导：

```text
toolchain_<libc>_<arch>_gcc-<major>.tar.zst
```

- tag：`toolchain`
- Release 名：`Toolchain_Cache`
- `build.yml` 的 `cache restore` 只取与 `.config` 中 GCC 大版本匹配的最新资产；
- 没有缓存时只警告，工具链照常编译。

## 9. 新增设备

1. 确认设备在 `target/linux/mediatek/image/filogic.mk` 中有 `define Device/<name>`；
2. 在 `scripts/zerowrt_core/profiles.py` 添加 `DeviceProfile`；
3. 在 `.github/workflows/build.yml` 的 `device.options` 添加选项；
4. 运行单元测试。

设备名必须与上游 `Device/` 名完全一致，否则 `config apply` 会在 `defconfig` 后报
“another device is selected” 或缺少目标。

## 10. 代码质量

```bash
python -m unittest discover -v
python -m ruff check scripts tests
```

测试不联网、不调用 `make`/`apt`，覆盖：

- 12 个设备注册与默认 IP；
- 设置校验；
- 高功率模板的设备剥离与保留镜像选项；
- 单设备选择与 Sing-Box 关闭；
- Argon 资源生成与配置；
- WiFi/banner/版本/密码；
- feed 同名包清理；
- 固件产物过滤；
- OTA 元数据、索引合并与本地发布；
- 工具链缓存资产名。
