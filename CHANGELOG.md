# Changelog

## 3.0.0 — 2026-11-08

- 全面改为 Python 流水线：`scripts/zerowrt.py` + `scripts/zerowrt_core/`。
- 源码切换为 `Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly` 的
  `openwrt-24.10-6.6` 分支，目标固定 `mediatek/filogic`。
- 支持 12 个设备 profile，每次工作流只编译一个设备。
- 基于 `defconfig/mt7975-ipailna-high-power.config` 生成单设备 `.config`，
  删除模板里的默认设备，保留 MTK WiFi/HNAT/TurboACC。
- 删除源码根部 `files/etc`；主机名 `ZeroWrt`；所有设备 LAN 统一
  `10.0.0.1`，可通过工作流覆盖。
- 版本字符串改为 `ZeroWrt-YYYYMMDD` / `ZeroWrt 标准版 @R... BY MinimaxFlora`。
- WiFi 默认 `ZeroWrt-2.4G` / `ZeroWrt-5G`，WPA2 `psk2`，密码 `1234567890`。
- 登录 banner 使用 `assets/banner`。
- 加入 WireGuard：`luci-proto-wireguard`、`wireguard-tools`、`kmod-wireguard`。
- 替换 PassWall、PassWall packages、OpenClash、Argon 主题、OTA。
- Argon 配置页已合并进 `luci-theme-argon`，不再单独克隆
  `luci-app-argon-config`。
- PassWall 只启用 Xray，关闭并删除 Sing-Box。
- Go 1.27 替换 `feeds/packages/lang/golang`。
- Argon 背景、favicon、SVG logo、PNG 图标来自 `assets/`；强制亮色；
  主色 `#EC4899`，暗色主色 `#BE185D`。
- OTA 默认索引 `https://ota.tatalvpai.vip/ota.json`，下载页域名
  `ota.tatalvpai.vip`。
- 12 个设备各生成一份完整 `configs/<device>.config`（已 `make defconfig`）；
  `config apply` 直接复制，不再每次执行 `make defconfig`。
- Release tag / Release 名统一为 `mediatek_filogic`；Release 只上传固件。
- 工具链缓存保留：tag `toolchain`，Release 名 `Toolchain_Cache`。
- 新增不联网单元测试与 Ruff 检查。
