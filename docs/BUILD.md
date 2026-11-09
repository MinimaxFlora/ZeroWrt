# 构建与维护

本文档面向维护者：说明每个构建步骤、固件定制点、设备配置的生成与使用，
以及 OTA 与工具链缓存的工作方式。

## 1. 源码与目标

| 项目 | 值 |
| --- | --- |
| 源码仓库 | `Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly` |
| 分支 | `openwrt-24.10-6.6`（默认固定在 commit `6e1f514b`） |
| 目标 | `mediatek/filogic` |
| 内核 | 6.6 |
| 设备配置 | `configs/<device>.config`（`diffconfig.sh` 差异配置） |
| 重新生成 | `scripts/zerowrt_core/config.py` 的 `config generate` |
| Release tag | `mediatek_filogic` |

源码是公开仓库，不需要 `SOURCE_TOKEN`。源码默认固定到 commit
`6e1f514b99156ca05921defcb0d1f31df3157c4d`；临时升级可用
`ZEROWRT_SOURCE_REF=<branch-or-sha>` 覆盖，正式发布前应把新 commit 写回
`profiles.SOURCE_REF`。需要写权限的是 `GITHUB_TOKEN`（Actions 自动提供），用于
Release 和 `gh-pages`。

## 2. 工作流顺序

`build.yml` 的顺序不是随意的：

1. **free-disk**：删除 runner 上无用的 SDK，必要时用 LVM 合并 `/` 与 `/mnt`，
   创建 swap。根分区已经足够大时跳过清理。
2. **install-deps**：安装 OpenWrt 编译依赖、`ccache`、`lvm2`、`xfsprogs`、
   Python/Pillow 等。
3. **install-llvm**：下载 sbwml 的 Clang 到 `/opt/clang`，校验固定 SHA256 后写入
   `GITHUB_PATH`。
4. **source clone**：克隆源码，校验关键文件，写入 `.zerowrt-info.json`
   （仓库、分支、commit、构建日期、设备）。
5. **feeds update**：`./scripts/feeds update -a`，确认 `feeds/luci`、`feeds/packages`。
6. **feeds install**：`./scripts/feeds install -a`，确认 `luci-compat`、`lyaml`、
   `ttyd`、`3proxy` 已安装。
7. **packages add**：见第 3 节。必须在 `feeds install` 之后，因为替换包需要
   `luci.mk` 和 feed 符号链接已经存在。
8. **source customize**：删除 `files/etc`、版本、IP、banner、root 密码、WiFi、
   Argon。见第 4 节。
9. **config apply**：复制 `configs/<device>.config`（diffconfig）为源码树 `.config`，
   执行 `make defconfig` 展开默认值并校验唯一设备/关键包。见第 5 节。
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

| 目录 | 仓库 | 固定 commit |
| --- | --- | --- |
| `openwrt-passwall` | `Openwrt-Passwall/openwrt-passwall` | `f19da543` |
| `openwrt-passwall-packages` | `Openwrt-Passwall/openwrt-passwall-packages` | `da712cf0` |
| `OpenClash` | `vernesong/OpenClash` | `e553e82e` |
| `luci-theme-argon` | `jerrykuku/luci-theme-argon` | `c6d63bd6` |
| `luci-app-ota` | `MinimaxFlora/luci-app-ota` | `5f66f5dc` |

Go 1.27 不放在 `package/new`，而是替换 feed 目录：

```text
feeds/packages/lang/golang  <-  sbwml/packages_lang_golang @ cd8953c3
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
工作流 **不再提供默认密码**，`root_password` 必填（8–128 位），空值会在
`source customize` 前直接失败。

### 4.7 LuCI 帮助与反馈

`luci.py` 在 `source customize` 阶段修改：

```text
feeds/luci/modules/luci-mod-status/htdocs/luci-static/resources/view/status/include/10_system.js
feeds/luci/modules/luci-base/po/zh_Hans/base.po
```

状态页加入：

- `Project Website` → `https://github.com/MinimaxFlora/ZeroWrt`
- `Issue Feedback` → `https://github.com/MinimaxFlora/ZeroWrt/issues`
- `Donation Address` → `https://pay.kejizero.xyz`

按钮样式通过 `<style id="zerowrt-support-style">` 注入，重复渲染不会重复添加；
外部链接带 `rel="noopener noreferrer"`。`base.po` 增加四条带源码行号的
`zh_Hans` 翻译，并补齐 `Project-Id-Version` / `MIME-Version` 头。

### 4.8 防火墙 zones

`luci.py` 同时修改：

```text
feeds/luci/applications/luci-app-firewall/htdocs/luci-static/resources/view/firewall/zones.js
```

删除完整区块：

```text
/* Netfilter flow offload support */
if (L.hasSystemFeature('offloading')) { ... }
```

删除后校验 `offloading_type`、`flow_offloading`、`Routing/NAT Offloading`
都不再出现；重复执行不会破坏文件。

### 4.9 OTA 与 24.10 ucode 兼容

`luci-app-ota` 的 `/usr/bin/ota` 使用 `fs.statvfs()` 做下载前剩余空间检查，
但 OpenWrt 24.10 的 `ucode-mod-fs` 没有导出 `statvfs`，脚本会在启动时直接报
`Module does not export statvfs`，于是 `ubus call luci.ota info` 返回
`no output from /usr/bin/ota`。

`ota_compat.py` 在克隆 OTA 源码后删除该可选预检查，保留下载器的实际写入校验：

```text
package/new/luci-app-ota/root/usr/bin/ota
```

补丁后验证 `statvfs` 不再出现，且 `const size` 仍传给 `ota-download`。

## 5. 设备配置

### 5.1 已生成配置

`configs/` 下每个设备一份 **`./scripts/diffconfig.sh` 差异配置**，约 380 行：

```text
configs/netcore-n60-pro.config
configs/ruijie-rg-x60-new.config
configs/ruijie-rg-x60-new-stock.config
configs/ruijie-rg-x60-new-expand.config
configs/ruijie-rg-x60-new-ubootmod.config
configs/ruijie-ew-6000gx-pro.config
configs/ruijie-ew-6000gx-pro-stock.config
configs/ruijie-ew-6000gx-pro-expand.config
configs/ruijie-ew-6000gx-pro-ubootmod.config
configs/supergateway-s20l.config
configs/supergateway-s20m.config
configs/supergateway-s20p.config
```

`config apply` 先复制再展开：

```text
configs/<device>.config  ->  源码树/.config
make defconfig           ->  展开为 9000+ 行的完整配置
```

这样仓库里不用存 12 份 9000 多行的 `.config`，只需要维护差异项。

### 5.2 生成方式

配置由 `config generate` 批量生成，对每个设备执行：

```text
源码 defconfig/mt7975-ipailna-high-power.config
  → 删除所有 CONFIG_TARGET_DEVICE_* / 旧目标选择
  → 只加入当前设备
  → 追加 ZeroWrt 插件、WireGuard、PassWall Xray、DDNS
  → make defconfig
  → 校验唯一设备/关键包
  → ./scripts/diffconfig.sh > configs/<device>.config
  → 复制 diffconfig 再 make defconfig，确认逐项一致
```

模板本身提供 MTK WiFi、HNAT、TurboACC 等高功率配置，但也默认选中：

- `mediatek/mt7986` 旧目标；
- GL.iNet、TP-Link、Xiaomi 等设备；
- Ruijie 的多个布局。

生成时会删除这些设备选择，只保留当前设备。目标块固定为：

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

### 5.4 config apply 校验

复制 diffconfig 并执行 `make defconfig` 后检查：

- 文件中只有当前设备这一行 `CONFIG_TARGET_DEVICE_*_DEVICE_*=y`；
- `mediatek/filogic` 目标和 `CONFIG_TARGET_MULTI_PROFILE` /
  `CONFIG_TARGET_PER_DEVICE_ROOTFS` 存在；
- 12 个插件、OTA、DDNS、WireGuard、MTK 加速包都存在；
- `CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox` 和
  `CONFIG_PACKAGE_sing-box` 没有变成 `=y`。

任何一项不满足都会直接失败，不会把错误配置带进编译。

### 5.5 重新生成

源码、feeds 或插件变化后，在 Linux 源码树执行：

```bash
python3 scripts/zerowrt.py config generate \
  --tree /builder/source \
  --out configs
```

生成结果提交到仓库后再运行 `Build ZeroWrt`。

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

### 6.3 Pages 与 Cloudflare

`gh-pages` 由 GitHub Pages 托管，同时 `ota.tatalvpai.vip` 实际指向 Cloudflare
Pages 项目 `zerowrt-ota`。Cloudflare Pages 是 **Direct Upload / ad hoc** 部署，
不会因为 `gh-pages` 有新提交而自动更新，所以构建末尾必须显式部署：

```text
gh-pages 最新内容
  → npx wrangler@4.158.0 pages deploy
  → Cloudflare Pages 项目 zerowrt-ota（production branch: gh-pages）
```

`build.yml` 的 **Deploy OTA page to Cloudflare Pages** 步骤使用仓库 Secrets
`CLOUDFLARE_API_TOKEN` 和 `CLOUDFLARE_ACCOUNT_ID`。也可以手动运行
`Deploy OTA Pages` workflow 同步当前 `gh-pages`。

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

设备名必须与上游 `Device/` 名完全一致。新增设备后需要执行
`config generate` 生成对应的 `configs/<device>.config`，否则 `config apply` 会报
缺少配置文件或选中了其它设备。

## 10. 代码质量

```bash
python -m unittest discover -v
python -m ruff check scripts tests
python -m ruff format --check scripts tests
mypy scripts
coverage run -m unittest discover
coverage report --fail-under=70
```

测试不联网、不调用 `make`/`apt`，覆盖：

- 12 个设备注册与默认 IP；
- 设置校验；
- 高功率模板的设备剥离与生成配置的唯一设备检查；
- 单设备选择与 Sing-Box 关闭；
- Argon 资源生成与配置；
- LuCI 帮助与反馈按钮与 zh_Hans 翻译；
- WiFi/banner/版本/密码；
- feed 同名包清理、feed 失败终止；
- 固件产物过滤、`dist` 清理；
- OTA 元数据、索引合并、损坏索引拒绝与本地发布；
- 工具链缓存资产名；
- workflow YAML 解析与 Action SHA 固定检查。
