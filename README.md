# ZeroWrt

ZeroWrt 是基于 LEDE 源码（私有源码仓库的 `ruijie-rg-x60-new` 分支）通过 GitHub Actions 自动编译的定制固件。

- 固件名称：`ZeroWrt`
- 默认管理地址：`http://10.0.0.1`
- 默认 WiFi：`ZeroWrt-2.4G`、`ZeroWrt-5G`（两个频段不同名）
- 构建环境：Ubuntu 24.04
- 所有源码修改逻辑均由 Python 完成（`scripts/zerowrt_core/`），工作流只负责调用

## 一、必须配置的 Secrets

仓库地址与 Token **不会**出现在 ZeroWrt 仓库的任何文件里，全部通过 GitHub Secrets 注入：

| Secret | 必填 | 说明 |
| --- | --- | --- |
| `LEDE_REPO` | 是 | 私有源码仓库，格式 `owner/name`（不要写进本仓库文件） |
| `LEDE_TOKEN` | 是 | 能读取该私有仓库的 PAT（细粒度 Token 勾选 `Contents: Read` 即可；经典 Token 勾选 `repo`） |
| `LEDE_REF` | 否 | 默认分支/标签，缺省为 `ruijie-rg-x60-new` |

设置位置：`Settings → Secrets and variables → Actions → New repository secret`。

> 工作流通过 `git` 的 `http.extraheader` 在内存中传递 Token，不写入 URL、不写入 `.git/config`、不打印到日志。私有仓库名也只出现在 Secret 中。

## 二、触发编译

- 推送到 `main` 分支（修改 `scripts/`、`configs/`、`assets/`、工作流时会自动触发）
- 或在 `Actions → Build ZeroWrt → Run workflow` 手动触发

工作流没有额外输入参数，IP、WiFi 名称等都在代码/配置中固定。

编译完成后在本次 Run 的 **Artifacts** 中下载 `ZeroWrt-<run_number>`，包含：

```
ZeroWrt-<版本>-<设备>-squashfs-sysupgrade.bin
SHA256SUMS
BUILD_INFO.txt
```

## 三、工作流做了什么

顺序与 `sbwml/actions` 的 `free-disk`、`openwrt-build-setup`、`install-llvm` 三个 action 对齐，但全部本地实现：

1. **合并磁盘 / 释放空间**（`system free-disk`）
   - 删除 Android SDK、JVM、dotnet、swift、aws、chromium 等无关组件
   - 重建 4 GiB swap
   - 用 LVM 把根分区与 `/mnt` 合并成约 130 GiB 的 `/builder`（失败时自动降级为 `/mnt` 绑定挂载）
2. **安装依赖**（`system install-deps`）
3. **安装 LLVM**（`system install-llvm`，Clang 23.0.1 到 `/opt/clang`）
4. **拉取私有源码**（`source clone`）
5. **更新 feeds 并剔除冲突包**（`source feeds`）
   - 删除 feeds 中的 `luci-theme-argon`、`luci-app-argon-config`、`luci-app-passwall`
   - 删除 feeds 中与 PassWall 自带核心重名的 `xray-core`、`sing-box`、`chinadns-ng` 等
6. **核心定制**（`source customize`）
7. **第三方包与主题品牌化**（`packages add`）
8. **生成 `.config`**（`config generate`）
9. **下载源码、编译、收集产物**

## 四、固件定制清单

| 需求 | 实现位置 | 说明 |
| --- | --- | --- |
| 固件名 `ZeroWrt` | `include/version.mk` | `VERSION_DIST`、`VERSION_MANUFACTURER` 的 `OpenWrt` 改为 `ZeroWrt` |
| 发行描述 `ZeroWrt` | `package/lean/default-settings/files/zzz-default-settings` | `DISTRIB_DESCRIPTION`、`OPENWRT_RELEASE` 中的 `LEDE` 改为 `ZeroWrt` |
| 管理 IP `10.0.0.1` | `package/base-files/files/bin/config_generate`<br>`package/base-files/luci/bin/config_generate` | 默认 LAN 地址由 `192.168.1.1` 改为 `10.0.0.1`，主机名默认 `ZeroWrt` |
| WiFi 名称 | `package/kernel/mac80211/files/lib/wifi/mac80211.sh` | 2.4G 为 `ZeroWrt-2.4G`，5G 为 `ZeroWrt-5G`，6G 为 `ZeroWrt-6G` |
| 保留 ShadowSocksR Plus+ | `include/target.mk` | 不删除 LEDE 默认的 SSR Plus+，并在配置中显式选中 |
| 改用 PassWall | `package/new/passwall-luci`、`package/new/passwall-packages` | 来自 `Openwrt-Passwall`（原 `xiaorouji` 仓库已迁移） |
| 改用 OpenClash | `package/new/openclash` | 来自 `vernesong/OpenClash` |
| Argon 主题 | `package/new/luci-theme-argon` | 固定 `v2.4.8`，见下方说明 |
| Argon 设置插件 | `package/new/luci-app-argon-config` | 关闭在线壁纸、替换 Logo |
| 登录背景 | `assets/background.jpg` | 覆盖 `argon/img/bg1.jpg`（如模板引用 WebP 则同时生成 `bg1.webp`） |
| 品牌 Logo | `assets/logo.png` | 渲染进 `argon/img/argon.svg`，并生成 favicon/ICO/各尺寸图标 |
| 在线壁纸 | `luci-app-argon-config/root/etc/config/argon` | `option online_wallpaper 'bing'` → `'none'` |

替换品牌素材：直接覆盖 `assets/background.jpg` 与 `assets/logo.png` 后重新运行工作流即可。Logo 建议使用 256×256 或更高分辨率的方形 PNG（当前素材为 64×64）。

### 关于 Argon 版本

`luci-theme-argon` 固定使用 **v2.4.8**。3.x 版本把 Argon 设置界面合并进了主题包，与独立的 `luci-app-argon-config` 会安装同名文件（`/etc/config/argon`、菜单、rpcd 脚本）而产生冲突。v2.4.8 是最后一个与独立设置插件配套的版本，其登录页正是 `img/bg1.jpg`、Logo 为 `img/argon.svg`，与本项目需求一致。

如需改用其它版本，可在工作流 `env` 中设置：

```yaml
env:
  ARGON_THEME_REF: v3.0.0
```

若检测到主题已内置设置界面，构建脚本会自动跳过独立插件并打印警告，避免同名文件冲突。

## 五、设备

`configs/zerowrt.config` 中已经固定为 `ruijie_rg-x60`：

```ini
CONFIG_TARGET_mediatek=y
CONFIG_TARGET_mediatek_filogic=y
CONFIG_TARGET_mediatek_filogic_DEVICE_ruijie_rg-x60=y
```

当前源码树只有 `ruijie-rg-x60-new` 分支，使用这三行即可直接编译。以后新增其它设备时，只改这三行（换成新的 `DEVICE_*`）即可，无需改脚本。

如果删除这三行，脚本会退回自动识别：在 `target/linux/*/**/image/*.mk` 中查找 `rg-x60` 设备，同时存在普通版与 Pro 版时优先选择普通版；找不到时工作流会失败并列出所有包含 `ruijie` 的设备名。

## 六、软件包配置

`configs/zerowrt.config` 会被合并进最终 `.config`（同名项以该文件为准）。当前内容为：

```ini
CONFIG_TARGET_mediatek=y
CONFIG_TARGET_mediatek_filogic=y
CONFIG_TARGET_mediatek_filogic_DEVICE_ruijie_rg-x60=y

CONFIG_PACKAGE_luci-app-passwall=y
CONFIG_PACKAGE_luci-app-openclash=y
CONFIG_PACKAGE_luci-app-ssr-plus=y

CONFIG_PACKAGE_luci-theme-argon=y
CONFIG_PACKAGE_luci-app-argon-config=y
```

其余依赖（如 `luci-compat`）由 OpenWrt 的依赖解析自动补全，不在配置中重复声明。

需追加插件时直接加一行，例如：

```ini
CONFIG_PACKAGE_luci-app-filetransfer=y
```

其他可覆盖的环境变量（写在工作流 `env:` 中）：

| 变量 | 默认值 |
| --- | --- |
| `ARGON_THEME_REPO` / `ARGON_THEME_REF` | `jerrykuku/luci-theme-argon` / `v2.4.8` |
| `ARGON_CONFIG_REPO` / `ARGON_CONFIG_REF` | `jerrykuku/luci-app-argon-config` / `master` |
| `PASSWALL_REPO` / `PASSWALL_REF` | `Openwrt-Passwall/openwrt-passwall` / `main` |
| `PASSWALL_PACKAGES_REPO` / `PASSWALL_PACKAGES_REF` | `Openwrt-Passwall/openwrt-passwall-packages` / `main` |
| `OPENCLASH_REPO` / `OPENCLASH_REF` | `vernesong/OpenClash` / `master` |

## 七、本地校验

脚本只依赖 Python 3 标准库（可选 Pillow 用于生成 WebP/多尺寸图标）。可在本地运行单元测试：

```bash
python3 -m unittest discover -s tests -v
```

查看命令帮助：

```bash
python3 scripts/zerowrt.py --help
python3 scripts/zerowrt.py system --help
```

完整编译在 GitHub Actions 的 Ubuntu 24.04 环境中执行；本地无需 Linux 环境即可修改配置与素材。

## 八、目录结构

```
.github/workflows/build.yml    # 编译工作流
assets/                        # 品牌素材（登录背景、Logo）
configs/zerowrt.config         # .config 覆盖项
scripts/zerowrt.py             # CLI 入口
scripts/zerowrt_core/          # 磁盘、源码、软件包、配置、构建、图像处理
tests/                         # 单元测试
```
