# Building ZeroWrt

Maintainer documentation: secrets, workflow inputs, what every step does and
which files carry the customisations.

Back to the [README](../README.md) · [other languages](readme)

---

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
| `wifi_password` | `1234567890` | WiFi 密码，8–63 位，仅字母/数字/`!@#$%^&*()_+.:=?-`；不经过命令行、不打印 |
| `device` | `ruijie_rg-x60-new` | 设备选择：`ruijie_rg-x60-new` 或 `x86_64` |

例如 `wifi_name=MyNet` 时，实际 SSID 为：

```
MyNet-2.4G
MyNet-5G
MyNet-6G
```

### 只有手动触发

`build.yml` **没有** `push` 触发器：合并代码、改脚本、改素材都不会自动编译。
要出固件只能到 `Actions → Build ZeroWrt → Run workflow` 手动点，参数用上面的默认值即可。

这样做的原因：一次完整编译要 5~6 小时，改一行文档顺带触发一次编译没有意义；
而且编排类改动（runner、action 版本、步骤顺序）应该先自己确认，再决定要不要出固件。

静态检查（`quality.yml`）仍然在 `scripts/**`、`tests/**` 变更时自动跑，它只要几十秒。

## 三、工作流做了什么

1. **准备构建空间**
   - 与 sbwml 的 `free-disk` 行为一致：`/mnt` 独立时清理预装组件、创建 swap，并用 LVM 把根分区与 `/mnt` 合并成一个约 130 GiB 的卷
   - 只有 `/mnt` 与根分区是同一块盘、且根分区已有 50 GiB 空闲时，才跳过清理；swap 不足时只调整 swap
2. **安装依赖**：对齐 sbwml 的 `openwrt-build-setup` 包列表，并补充 lvm2、xfsprogs、python3-pil 等；Docker 默认不装（当前配置没有 docker 插件），需要时运行 `system install-deps --docker`
3. **安装 LLVM**：Clang 23.0.1 到 `/opt/clang`，与 `install-llvm` 使用同一版本
4. **拉取私有源码**
5. **更新 feeds**：删除 feeds 里的 Argon 主题/插件和 PassWall 冲突包
6. **核心定制**：版本、IP、主机名、WiFi 名称/密码
7. **添加第三方包与主题品牌化**
8. **生成 `.config`**：设备/profile 选择 + 固定软件包列表
9. **恢复工具链缓存**：从 `toolchain` release 下载 tar.zst，解压后 touch `staging_dir`/`tmp`，跳过 40 分钟的工具链编译
10. **下载、编译、收集产物**：编译使用 `nproc + 1` 个并行任务和 `IGNORE_ERRORS="n m"`
11. **发布 Release**：tag 和 release 名称都使用设备名（`ruijie_rg-x60-new` / `x86_64`），上传 `dist/*`

产物在本次 Run 的 **Artifacts** 中：`ZeroWrt-<run_number>`，包含固件、`SHA256SUMS`、`BUILD_INFO.txt`。构建成功后还会自动创建/更新以设备命名的 Release；同一设备再次构建会删除旧 release/tag 后重新发布。

固件文件保留 OpenWrt 原始命名，例如：

```
zerowrt-mediatek-filogic-ruijie_rg-x60-new-squashfs-sysupgrade.bin
```

`VERSION_DIST=ZeroWrt` 已经让前缀变成 `zerowrt`，不再额外重命名为 `ZeroWrt-20261020-...`。

## 四、定制内容

| 项目 | 实现位置 | 说明 |
| --- | --- | --- |
| 固件名 `ZeroWrt` | `include/version.mk` | 只把 `VERSION_DIST`、`VERSION_MANUFACTURER` 的 `OpenWrt` 改为 `ZeroWrt`；`VERSION_NUMBER` 设为构建日期仅用于登录页显示 |
| 发行描述 | `package/lean/default-settings/files/zzz-default-settings` | `DISTRIB_DESCRIPTION`、`OPENWRT_RELEASE` 中的 LEDE 改为 ZeroWrt |
| 内核版本 `6.18` | `target/linux/mediatek/Makefile`、`target/linux/x86/Makefile` | `KERNEL_PATCHVER`、`KERNEL_TESTING_PATCHVER` 改为 `6.18` |
| 管理 IP | `package/base-files/files/bin/config_generate`<br>`package/base-files/luci/bin/config_generate` | 写入 Actions 里的 `ip`，主机名默认 `ZeroWrt` |
| WiFi 名称与密码 | `package/kernel/mac80211/files/lib/wifi/mac80211.sh` | 2.4G/5G/6G 分别生成 SSID；WPA2/WPA3 密码 |
| Argon 主题 | `package/new/luci-theme-argon` | 跟踪 `master`（3.x），登录背景、登录 Logo、网站图标全部替换为 `assets/` 素材 |
| Argon 外观 | 主题包内 `root/etc/config/argon` | 亮色模式、主色 `#2E9D72`、暗色主色 `#4CAF86`、在线壁纸 `none` |
| 网站图标 | `package/new/luci-theme-argon/.../icon/*`、`package/base-files/files/www/favicon.ico` | 主题 favicon + `/favicon.ico` 都使用 ZeroWrt Logo；`branding.js` 指向新的 `favicon-zerowrt.png`，模板链接加 `?v=zerowrt` 避免浏览器缓存 |
| 移除 SSR Plus+ | `include/target.mk`、`feeds/helloworld` | 删除默认 SSR Plus+ 插件及默认包引用 |
| 代理插件 | `package/new/helloworld/*` | 来自 [openwrt_helloworld](https://github.com/MinimaxFlora/openwrt_helloworld)：PassWall（仅 Xray，无 Sing-Box）、passwall2、OpenClash 与它们的内核软件包，版本更新和插件同步都在那个仓库里由 workflow 完成 |
| 软件包列表 | `scripts/zerowrt_core/configgen.py` | 统一在 `PACKAGES` 中维护 |

替换品牌素材：覆盖 `assets/background.jpg`、`assets/logo.png` 后重新运行。

### 关于 Argon 版本

`luci-theme-argon` 使用仓库默认分支 **`master`**（3.x）。

3.x 已把 Argon 设置界面合并进主题包：主题自身提供 `/etc/config/argon`、`Argon Config` 菜单、rpcd 和品牌设置。如果再把独立的 `luci-app-argon-config` 装进去，两个包会写同一批文件（`/etc/config/argon`、menu、rpcd），产生文件冲突。因此脚本检测到主题已内置设置界面时，会跳过独立插件并打印警告；设置页面仍然在 **系统 → Argon 主题设置**。

如果你确实要旧版“主题 + 独立插件”的组合，可把工作流环境变量改为：

```yaml
env:
  ARGON_THEME_REF: v2.4.8
```

v2.4.8 的登录页使用 `img/bg1.jpg`；master 使用 `img/bg1.webp`，脚本会按模板自动生成对应的背景文件。

主题默认外观由脚本写入 `root/etc/config/argon`：

```ini
option mode 'light'
option primary '#2E9D72'
option dark_primary '#4CAF86'
option dark_primary_mode 'custom'
option online_wallpaper 'none'
```

同时替换登录 Logo、主题 `favicon.ico`、`icon/*.png` 以及根路径 `/www/favicon.ico`，浏览器标签页和 “Argon 主题设置” 里的图标都会显示 `assets/logo.png`。

## 五、设备

设备由 Actions 的 `device` 参数选择：

- `ruijie_rg-x60-new`：在 `target/linux/mediatek/image/filogic.mk` 中按 `define Device/ruijie_rg-x60-new` 查找，自动得到 `mediatek/filogic`
- `x86_64`：固定使用 `x86/64` 的 `Generic` profile，生成 `CONFIG_TARGET_x86_64_Generic=y`

当前支持：

```
ruijie_rg-x60-new   (mediatek/filogic, 设备 profile)
x86_64              (x86/64, Generic profile)
```

以后新增设备时：

1. 源码树里必须有对应的 `define Device/<name>` 定义
2. 在 [build.yml](.github/workflows/build.yml) 的 `device.options` 增加选项

如果名称写错，工作流会失败并列出源码树里包含 `rg-x60` 的设备名，便于排查。

## 六、固件版本与登录页

固件版本号使用构建日期（例如 `20261020`）：

- `include/version.mk` 的 `VERSION_NUMBER` 默认值在构建时改为日期
- `VERSION_NUMBER` 是隐藏 Kconfig 符号，不能写进 `.config`（会被 `defconfig` 丢弃），所以由 `version.mk` 提供
- Argon 登录页 footer 去掉了空的 `revision` 后缀，因此显示为 `ZeroWrt 20261020`，不再出现 `ZeroWrt 24.10.5-`

## 七、软件包

包列表在 `scripts/zerowrt_core/configgen.py`：

```python
PACKAGES = [
    "CONFIG_PACKAGE_luci-theme-argon",
    "CONFIG_PACKAGE_luci-app-argon-config",  # 仅当独立插件被克隆（非 3.x 主题）时使用
    "CONFIG_PACKAGE_luci-app-passwall",
    "CONFIG_PACKAGE_luci-app-openclash",
]
```

ShadowSocksR Plus+ 已从 `include/target.mk` 默认包、`feeds/helloworld` 和最终 `.config` 中移除。

PassWall 只保留 Xray 核心，显式关闭 Sing-Box，避免固件变大：

```ini
CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray=y
# CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox is not set
# CONFIG_PACKAGE_sing-box is not set
```

Argon `master` 内置设置界面时，脚本会自动从 `.config` 中去掉 `luci-app-argon-config`，避免安装不存在的独立包。

`luci-compat`、`lyaml` 等依赖由 OpenWrt 自动解析，不重复声明。

## 八、构建加速（工具链缓存）

采用 [sbwml/r4s_build_script](https://github.com/sbwml/r4s_build_script) 的做法：把工具链单独编译好，
打包成 `tar.zst` 放进 release，固件构建时下载解压，跳过工具链编译。

**生成缓存**：`Build Toolchain Cache` workflow（`.github/workflows/toolchain.yml`）

```bash
make -j$(nproc) toolchain/compile || make -j$(nproc) toolchain/compile V=s
tar -I "zstd -19 -T$(nproc --all)" -cf toolchain-cache/toolchain_${LIBC}_${toolchain_arch}_gcc-${gcc_version}.tar.zst ./{build_dir,dl,staging_dir,tmp}
```

产物上传到 tag 为 `toolchain`、标题为 `Toolchain_Cache` 的 release，资产名按 sbwml 的规则自动推导
（`LIBC`/架构/GCC 版本都从 `staging_dir/toolchain-*` 目录名解析，换设备不用改脚本）。

**使用缓存**：固件构建在编译前执行

```bash
gh release download toolchain --pattern "toolchain_*" --output toolchain.tar.zst
tar -I zstd -xf toolchain.tar.zst
mkdir -p bin
find ./staging_dir/ -name '*' -exec touch {} \;
find ./tmp/ -name '*' -exec touch {} \;
```

`touch` 是必须的：解压出来的文件时间戳比 make 的 stamp 旧，不刷新就会被判定为过期而重编。

相比之前的 ccache：

- 省掉的是工具链 + 工具这一段（首次构建里最长的固定开销），不是零散的目标文件
- 不依赖 `actions/cache` 的 10GB 上限和淘汰策略，缓存放在 release 里可以长期保存
- 缓存内容与构建用的 `.config` 必须一致（同一 target、同一 LIBC、同一 GCC 版本），所以 workflow 与固件构建走同一套配置生成逻辑

## 九、代码质量（QC）

- Ruff 配置：`pyproject.toml`（行宽 120，`E/F/W/I/UP/B/SIM`）
- 单元测试：`tests/test_zerowrt.py`（设置校验、IP/SSID/密码补丁、设备查找、`.config` 生成、Argon 品牌化、产物收集）
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

## 十、目录结构

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

## 十一、在线升级（OTA）与固件下载页

固件内置 [luci-app-ota](https://github.com/MinimaxFlora/luci-app-ota)，菜单在 **系统 → 在线升级**（概览 / 配置）。
插件用的更新索引和配套的下载页都由构建流程自动发布到本仓库的 `gh-pages` 分支（GitHub Pages）：

```
https://minimaxflora.github.io/ZeroWrt/            # 下载页：按设备列最新镜像、SHA256、更新日志
https://minimaxflora.github.io/ZeroWrt/ota.json    # 插件读取的更新索引
https://minimaxflora.github.io/ZeroWrt/history.json  # 下载页用的发布历史
```

流水线里新增的三步：

1. `Add luci-app-ota`：把插件克隆到 `package/new/luci-app-ota`（`Generate .config` 之前）
2. `Embed OTA metadata`：写入 `/etc/ota/build.json`、`version.date` 和默认更新源地址（`/etc/uci-defaults`），让固件能自报设备名与构建时间
3. `Publish OTA page`：Release 发布后把页面、`ota.json`、`history.json` 推送到 `gh-pages` 分支

每台设备构建完成后只更新自己在索引里的条目，不同设备的条目不会互相覆盖；所以
`ruijie_rg-x60-new` 和 `x86_64` 各构建一次后，索引和下载页里两套设备就都齐了。
x86 会分成「传统 BIOS」和「UEFI」两项，刷错会无法启动，下载页上用徽章区分。

升级流程：检查更新 → 下载（SHA256 校验 + `sysupgrade -T` 预检镜像）→ 安装（可选保留配置）。

设备上的命令行（输出 JSON，方便脚本调用）：

```sh
ota info       # 本地固件信息、设备标识、索引地址
ota check      # 检查更新
ota status     # 下载进度
ota cancel     # 取消下载
```

> `version.date` 让 `SOURCE_DATE_EPOCH` 等于本次构建时间，从而 `/etc/os-release` 的
> `OPENWRT_BUILD_DATE` 与 `/etc/ota/build.json` 的 `build_date` 完全一致；
> 不写的话会退回 git 提交时间，同一个 commit 多次构建就分不出新旧了。

仓库的 `Settings → Pages` 需要设为 **Deploy from a branch / `gh-pages` / `/`**（只需设置一次，
本仓库已配置）。页面本身在插件仓库的 `site/` 目录，改样式或文案时改那里即可。

## 十二、运行环境与 Action 版本

runner 和 action 都**钉死具体版本**，不追 latest：

| 组件 | 版本 | 说明 |
| --- | --- | --- |
| runner | `ubuntu-24.04` | `ubuntu-latest` 在 2026 年 10 月切到 Ubuntu 26，同一个 commit 重跑会换掉工具链 |
| `actions/checkout` | `v7.0.1` | Node 24 运行时 |
| `actions/cache` | `v6.1.0` | Node 24 运行时 |
| `actions/upload-artifact` | `v7.0.2` | v4 及更早跑在 Node 20 上，GitHub 已开始弃用 |
| `actions/setup-python` | `v7.0.0` | Node 24 运行时 |

版本号以 **GitHub 上的 tag** 为准（`gh api --paginate repos/actions/<name>/tags`），不要看 `releases/latest`：像 `setup-python` 这样的 action 根本不发 release，那个接口会 404。不要写 `@v7` 这种浮动主版本，
否则上游发版会在你没改任何东西的情况下换掉构建环境。
