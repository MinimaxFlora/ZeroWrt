## MediaTek Filogic Firmware

面向 MediaTek Filogic 平台的第三方 OpenWrt / ZeroWrt 固件项目，致力于为不同品牌、不同型号的 Filogic 设备提供稳定、易用、功能丰富的固件。

### ✨ 项目特性

- 基于 OpenWrt / ImmortalWrt 生态构建，内核 6.6
- 支持多款 MediaTek Filogic 平台路由设备
- 集成 Argon 主题及简体中文界面
- 集成 OpenClash、PassWall 等代理工具
- 集成 SmartDNS、ChinaDNS-NG、Dnsmasq-Full
- 集成 MediaTek TurboACC、HNAT 网络加速
- 支持 EQOS-MTK、SQM Cake、UPnP、DDNS、ACME
- 支持 WireGuard 等网络功能
- 支持 ext4、NTFS3、exFAT、Btrfs 文件系统
- 提供 zram 内存优化支持

### 📦 固件版本

根据不同设备及硬件布局，提供多种固件类型：

- **Standard**：标准固件版本
- **Stock**：适配原厂分区布局的固件
- **Expand**：扩展存储空间版本
- **U-Boot Mod**：适用于特定设备的修改版 U-Boot 固件

并非所有设备都提供以上全部版本，请根据设备型号选择对应固件。

### 📡 设备支持

本项目面向 MediaTek Filogic 平台，支持以下设备：

- Netcore N60 Pro
- Ruijie EW-6000GX Pro（Standard / Stock / Expand / U-Boot Mod）
- Ruijie RG-X60 New（Standard / Stock / Expand / U-Boot Mod）
- Super Gateway S20L / S20M / S20P

具体设备型号、硬件版本及对应固件文件，请查看本次 Release 附件。

> 同一 Release 会累积不同设备的固件。每次构建只上传本次选择的设备，不会删除其它设备已经发布的文件。

### 🧩 默认设置

- 管理地址：所有设备统一 `10.0.0.1`，可由构建输入覆盖
- 主机名：`ZeroWrt`
- WiFi：`ZeroWrt-2.4G` / `ZeroWrt-5G`，WPA2-PSK，默认密码 `1234567890`（可由构建输入覆盖）
- root 密码：构建时必填（8–128 位），不提供默认密码
- 主题：Argon 强制亮色，主色 `#EC4899`
- WireGuard：已集成 LuCI 协议页、`wireguard-tools` 和内核模块

### 🚀 在线升级

固件内置 `luci-app-ota`。进入 **系统 → 在线升级** 即可检查、下载、校验并安装新固件。更新索引为 `https://ota.tatalvpai.vip/ota.json`，下载页域名为 `ota.tatalvpai.vip`。

### ⚠️ 刷机须知

1. 刷机前请确认设备型号、硬件版本及对应固件文件。
2. 不同设备的 Flash 布局、分区结构及启动方式可能不同，请勿混刷。
3. Stock / Expand / U-Boot Mod 版本的分区布局不同，切换布局前请确认恢复方式。
4. 刷机前请备份原厂固件及重要配置。
5. 涉及 U-Boot、Bootloader 或分区布局修改的操作，请提前确认恢复方式。
6. 因错误刷入固件导致的设备损坏，需要用户自行承担风险。

### 🙏 致谢

感谢 OpenWrt、ImmortalWrt 以及 MediaTek Filogic 社区开发者的贡献，也感谢所有参与测试、反馈和改进的用户。

**项目定位：MediaTek Filogic 多设备固件，而非单一设备专用固件。**
