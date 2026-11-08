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
- 12 个设备各生成一份 `configs/<device>.config`（`diffconfig.sh` 差异配置）；
  `config apply` 复制后执行 `make defconfig` 展开，不再手工填配置。
- 源码、PassWall、OpenClash、Argon、OTA、Go 全部固定 commit；Actions 固定 SHA；
  LLVM 下载校验 SHA256。
- feed update/install 失败立即终止；OTA 索引/历史损坏时不再静默清空；root 密码改为必填。
- 增加 diffconfig 回灌校验、dist 清理、覆盖率门禁和配置路径触发。
- Release tag / Release 名统一为 `mediatek_filogic`；Release 只上传固件。
- 工具链缓存保留：tag `toolchain`，Release 名 `Toolchain_Cache`。
- 新增不联网单元测试与 Ruff 检查。
