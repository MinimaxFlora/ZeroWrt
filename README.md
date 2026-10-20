# ZeroWrt

ZeroWrt 是基于 LEDE 源码（私有源码仓库的 `ruijie-rg-x60-new` 分支）通过 GitHub Actions 自动编译的定制固件。

- 固件名称：`ZeroWrt`
- 构建环境：Ubuntu 24.04
- IP、WiFi 名称、WiFi 密码、设备型号全部在 Actions 中设置
- 软件包和设备由 Python 脚本统一写入 `.config`，不再维护单独的配置文件
- 代码质量由 Ruff 检查和单元测试保证

## 一、Secrets

私有源码仓库地址和 Token **不会**出现在本仓库文件里，只通过 Secrets 注入：

| Secret | 必填 | 说明 |
| --- | --- | --- |
| `LEDE_REPO` | 是 | 私有源码仓库，格式 `owner/name` |
| `LEDE_TOKEN` | 是 | 能读取该私有仓库的 PAT（细粒度 Token 勾选 `Contents: Read`） |
| `LEDE_REF` | 否 | 分支/标签，缺省 `ruijie-rg-x60-new` |

设置位置：`Settings → Secrets and variables → Actions`。

> Token 通过 `git` 的 `http.extraheader` 在内存中传递，不写入 URL、不写入 `.git/config`，也不会打印到日志。

## 二、触发方式与参数

### 手动触发

`Actions → Build ZeroWrt → Run workflow`，可填写：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `ip` | `10.0.0.1` | 管理地址 / LAN IP |
| `wifi_name` | `ZeroWrt` | WiFi 名称前缀，自动生成 `-2.4G`、`-5G`、`-6G` |
| `wifi_password` | `ZeroWrt123` | WiFi 密码，8–63 位，仅字母/数字/`!@#$%^&*()_+.:=?-`；不经过命令行、不打印 |
| `device` | `ruijie_rg-x60-new` | 设备 profile（选择框，另有 `ruijie_rg-x60-pro`） |

例如 `wifi_name=MyNet` 时，实际 SSID 为：

```
MyNet-2.4G
MyNet-5G
MyNet-6G
```

### 推送到 main

修改以下路径会自动触发，使用上面的默认值：

```yaml
push:
  branches: [main]
  paths:
    - "scripts/**"
    - "assets/**"
    - ".github/workflows/**"
```

不会把手动触发改成唯一入口。

## 三、工作流做了什么

1. **准备构建空间**
   - 空闲空间达到 50 GiB 时不再删除预装组件，也不做磁盘合并；swap 不足时只调整 swap
   - 空间不足时才删除预装组件，并在需要时用 LVM 合并根分区与 `/mnt`
2. **安装依赖**：gcc、ncurses、python、lvm2、xfsprogs 等
3. **安装 LLVM**：Clang 23.0.1 到 `/opt/clang`
4. **拉取私有源码**
5. **更新 feeds**：删除 feeds 里的 Argon 主题/插件和 PassWall 冲突包
6. **核心定制**：版本、IP、主机名、WiFi 名称/密码
7. **添加第三方包与主题品牌化**
8. **生成 `.config`**：设备 profile 查表 + 固定软件包列表
9. **下载、编译、收集产物**

产物在本次 Run 的 **Artifacts** 中：`ZeroWrt-<run_number>`，包含固件、`SHA256SUMS`、`BUILD_INFO.txt`。

## 四、定制内容

| 项目 | 实现位置 | 说明 |
| --- | --- | --- |
| 固件名 `ZeroWrt` | `include/version.mk` | `VERSION_DIST`、`VERSION_MANUFACTURER` 改为 `ZeroWrt` |
| 发行描述 | `package/lean/default-settings/files/zzz-default-settings` | `DISTRIB_DESCRIPTION`、`OPENWRT_RELEASE` 中的 LEDE 改为 ZeroWrt |
| 管理 IP | `package/base-files/files/bin/config_generate`<br>`package/base-files/luci/bin/config_generate` | 写入 Actions 里的 `ip`，主机名默认 `ZeroWrt` |
| WiFi 名称与密码 | `package/kernel/mac80211/files/lib/wifi/mac80211.sh` | 2.4G/5G/6G 分别生成 SSID；WPA2/WPA3 密码 |
| Argon 主题 | `package/new/luci-theme-argon` | 固定 v2.4.8，默认登录背景、Logo、favicon 替换为 `assets/` 素材 |
| Argon 在线壁纸 | `luci-app-argon-config/root/etc/config/argon` | `online_wallpaper` 改为 `none` |
| 代理插件 | `package/new/passwall-*`、`package/new/openclash` | PassWall + OpenClash，保留 SSR Plus+ |
| 软件包列表 | `scripts/zerowrt_core/configgen.py` | 统一在 `PACKAGES` 中维护 |

替换品牌素材：覆盖 `assets/background.jpg`、`assets/logo.png` 后重新运行。

### 关于 Argon 版本

`luci-theme-argon` 固定 **v2.4.8**。3.x 把设置界面合并进主题包，会与独立的 `luci-app-argon-config` 产生同名文件冲突。v2.4.8 的登录页使用 `img/bg1.jpg`、Logo 使用 `img/argon.svg`，与本项目一致。

## 五、设备

设备由 Actions 的 `device` 参数选择，脚本在 `target/linux/*/**/image/*.mk` 中按 `define Device/<name>` 精确查找，并自动推导 board/subtarget。

当前只有：

```
ruijie_rg-x60-new   (mediatek/filogic)
ruijie_rg-x60-pro   (mediatek/filogic)
```

以后新增设备时：

1. 源码树里必须有对应的 `define Device/<name>` 定义
2. 在 [build.yml](.github/workflows/build.yml) 的 `device.options` 增加选项

如果名称写错，工作流会失败并列出源码树里包含 `rg-x60` 的设备名，便于排查。

## 六、软件包

包列表在 `scripts/zerowrt_core/configgen.py`：

```python
PACKAGES = [
    "CONFIG_PACKAGE_luci-theme-argon",
    "CONFIG_PACKAGE_luci-app-argon-config",
    "CONFIG_PACKAGE_luci-app-passwall",
    "CONFIG_PACKAGE_luci-app-openclash",
    "CONFIG_PACKAGE_luci-app-ssr-plus",
]
```

`luci-compat`、`lyaml` 等依赖由 OpenWrt 自动解析，不重复声明。

## 七、代码质量（QC）

- Ruff 配置：`pyproject.toml`（行宽 120，`E/F/W/I/UP/B/SIM`）
- 单元测试：`tests/test_zerowrt.py`（设置校验、IP/SSID/密码补丁、设备查找、`.config` 生成、Argon 品牌化、产物命名）
- 质量工作流：[.github/workflows/quality.yml](.github/workflows/quality.yml)，在 push / PR 时运行：

```bash
ruff check scripts tests
ruff format --check scripts tests
python -m unittest discover -s tests -v
```

本地运行：

```bash
python3 -m unittest discover -s tests -v
```

## 八、目录结构

```
.github/workflows/build.yml      # 编译工作流
.github/workflows/quality.yml    # Ruff + 单元测试
assets/                          # 登录背景、Logo
scripts/zerowrt.py               # CLI 入口
scripts/zerowrt_core/
  settings.py                    # 参数校验（IP、WiFi、设备）
  source.py                      # 源码补丁
  packages.py                    # 第三方包与品牌化
  configgen.py                   # 设备查找 + .config
  build.py                       # 下载、编译、收集
  sysops.py                      # 磁盘/依赖/LLVM
  images.py / util.py
tests/test_zerowrt.py
pyproject.toml
```
