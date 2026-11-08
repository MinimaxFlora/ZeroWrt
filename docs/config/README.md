# 配置预览

`netcore_n60-pro.seed.config` 是工作流在 `make defconfig` **之前**写出的
`.config`，由以下内容生成：

```text
源码 defconfig/mt7975-ipailna-high-power.config
  → 删除所有 CONFIG_TARGET_DEVICE_* / 旧目标选择
  → 只加入 Netcore N60 Pro
  → 追加 ZeroWrt 插件、WireGuard、PassWall Xray、DDNS
```

`netcore_n60-pro.final.config` 是在真实源码树上执行
`make defconfig` 后的最终 `.config`（9563 行，480 个 `CONFIG_PACKAGE_*=y`）。
它由 2026-11-08 的上游源码和本仓库代码实际生成，用于核对，不参与构建。

最终文件中关键项：

```ini
CONFIG_TARGET_MULTI_PROFILE=y
CONFIG_TARGET_PER_DEVICE_ROOTFS=y
CONFIG_TARGET_DEVICE_mediatek_filogic_DEVICE_netcore_n60-pro=y
CONFIG_PACKAGE_luci-proto-wireguard=y
CONFIG_PACKAGE_wireguard-tools=y
CONFIG_PACKAGE_kmod-wireguard=y
CONFIG_PACKAGE_luci-theme-argon=y
CONFIG_PACKAGE_luci-app-passwall=y
CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray=y
```

没有 `CONFIG_PACKAGE_luci-app-argon-config=y`（已合并进主题），也没有
`CONFIG_PACKAGE_sing-box=y` 或 `CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox=y`。

如需重新生成 seed：

```bash
python3 scripts/zerowrt.py config preview \
  --tree /builder/source \
  --device netcore_n60-pro \
  --out docs/config/netcore_n60-pro.seed.config
```

最终 `.config` 只能在完整源码树执行 `make defconfig` 后得到；LAN IP、WiFi、banner、
Argon 资源等定制不在 `.config` 里，而是在 `source customize` 阶段写入源码文件。
