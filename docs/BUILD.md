# Building ZeroWrt

Maintainer documentation: inputs, what every step does and which files carry the
customisations.

Back to the [README](../README.md) · [other languages](readme)

---

ZeroWrt 通过 GitHub Actions 自动编译，源码来自一个**公开**仓库：

| 设备 | 源码树 | 分支 |
| --- | --- | --- |
| 锐捷 RG-X60 New | [Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly](https://github.com/Yuzhii0718/immortalwrt-mt798x-6.6-padavanonly) | `openwrt-24.10-6.6` |

- 固件名称：`ZeroWrt`
- 构建环境：Ubuntu 24.04
- IP、WiFi 名称、WiFi 密码全部在 Actions 中设置
- 软件包和设备由 Python 脚本统一写入 `.config`，不再维护单独的配置文件
- 代码质量由 Ruff 检查和单元测试保证

## 一、源码与 Secrets

源码树是公开仓库，**不需要**任何源码 Token；`git clone` 直接匿名拉取。
`LEDE_REPO` / `LEDE_TOKEN` / `LEDE_REF` 三个旧的 Secret 已经删除，留着也不会被读取。

仍然需要的 Secret 只有发布相关的两个：

| Secret | 必填 | 说明 |
| --- | --- | --- |
| `CLOUDFLARE_API_TOKEN` | 否 | 把 gh-pages 内容同步到 Cloudflare Pages（`ota.tatalvpai.vip`） |
| `CLOUDFLARE_ACCOUNT_ID` | 否 | 同上 |

`GITHUB_TOKEN` 由 Actions 自动提供，用于发布 Release 和 gh-pages。

设备与源码的对应关系写在 `scripts/zerowrt_core/profiles.py`，想换分支或换源只改那一个文件。

## 二、触发方式与参数

### 手动触发

`Actions → Build ZeroWrt → Run workflow`，可填写：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `ip` | `10.0.0.1` | 管理地址 / LAN IP |
| `wifi_name` | `ZeroWrt` | WiFi 名称前缀，自动生成 `-2.4G`、`-5G`、`-6G` |
| `wifi_password` | `1234567890` | WiFi 密码，8–63 位，仅字母/数字/`!@#$%^&*()_+.:=?-`；不经过命令行、不打印 |

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
4. **拉取源码**：按 `profiles.py` 里的仓库和分支匿名 clone ImmortalWrt，不需要 Token
5. **更新 feeds**：删除 feeds 里与 `package/new` 重名的包（Argon 主题/插件、PassWall、sing-box 等）
6. **核心定制**：删除源码树根部的 `files/` 覆盖层、版本/发行字符串、IP、主机名、WiFi 名称/密码
7. **添加第三方包与主题品牌化**
8. **生成 `.config`**：设备/profile 选择 + 固定软件包列表
9. **恢复工具链缓存**：从 `toolchain` release 下载 tar.zst，解压后 touch `staging_dir`/`tmp`，跳过 40 分钟的工具链编译
10. **下载、编译、收集产物**：编译使用 `nproc + 1` 个并行任务和 `IGNORE_ERRORS="n m"`
11. **发布 Release**：tag 和 release 名称都使用设备名（`ruijie_rg-x60-new`），上传 `dist/*`

产物在本次 Run 的 **Artifacts** 中：`ZeroWrt-<run_number>`，包含固件、`SHA256SUMS`、`BUILD_INFO.txt`。构建成功后还会自动创建/更新以设备命名的 Release；同一设备再次构建会删除旧 release/tag 后重新发布。

固件文件保留 OpenWrt 原始命名，例如：

```
zerowrt-mediatek-filogic-ruijie_rg-x60-new-ubootmod-squashfs-sysupgrade.itb
```

`VERSION_DIST=ZeroWrt` 已经让前缀变成 `zerowrt`，不再额外重命名为 `ZeroWrt-20261020-...`。

## 四、定制内容

| 项目 | 实现位置 | 说明 |
| --- | --- | --- |
| 源码树覆盖层 | `files/`（源码树根部） | ImmortalWrt 在这里放了一份 `etc/banner`，会盖掉我们自己的 banner，构建时整个目录删除 |
| 固件名 `ZeroWrt` | `include/version.mk` | 把 `VERSION_DIST`、`VERSION_MANUFACTURER` 的默认值（`ImmortalWrt` 或 `OpenWrt`）改为 `ZeroWrt`；`VERSION_NUMBER` 设为构建日期 |
| 发行字符串 | `package/base-files/files/etc/openwrt_release`<br>`package/base-files/files/usr/lib/os-release` | release 文件是 `%D %V %C` 模板，脚本直接写成字面量：`DISTRIB_DESCRIPTION='ZeroWrt-20261020'`、`DISTRIB_REVISION=' By MinimaxFlora'`、`OPENWRT_RELEASE="ZeroWrt 标准版 @R20261020 BY MinimaxFlora"` |
| 管理 IP | `package/base-files/files/bin/config_generate` | 把所有 `ipad=${ipaddr:-"..."}` 默认值改为 Actions 里的 `ip`（默认 `10.0.0.1`）。ImmortalWrt 给 `ruijie,rg-x60*` 分支单独写了 `192.168.110.1`，也一并改掉；校验步骤会确认没有任何分支还留着别的默认值，所以 LAN 登录地址不随设备变化。主机名默认 `ZeroWrt` |
| WiFi 名称与密码（MT7986） | `package/mtk/applications/mtwifi-cfg/files/mtwifi.sh` | 改掉 `ImmortalWrt-2.4G` / `-5G` 两个默认 SSID，并把 `encryption=none` 改成 `psk2` + `key` |
| Argon 主题 | `package/new/luci-theme-argon` | 跟踪 `master`（3.x），登录背景、登录 Logo、网站图标全部替换为 `assets/` 素材 |
| Argon 外观 | 主题包内 `root/etc/config/argon` | 亮色模式、主色 `#2E9D72`、暗色主色 `#4CAF86`、在线壁纸 `none` |
| 网站图标 | `package/new/luci-theme-argon/.../icon/*`、`package/base-files/files/www/favicon.ico` | 主题 favicon + `/favicon.ico` 都使用 ZeroWrt Logo；`branding.js` 指向新的 `favicon-zerowrt.png`，模板链接加 `?v=zerowrt` 避免浏览器缓存 |
| 移除 SSR Plus+ | `include/target.mk`、`feeds/helloworld` | 删除默认 SSR Plus+ 插件及默认包引用 |
| 代理插件 | `package/new/helloworld/*` | 来自 [openwrt_helloworld](https://github.com/MinimaxFlora/openwrt_helloworld)：PassWall（sing-box 内核，不含 Xray、不含 SmartDNS）、passwall2、OpenClash 与它们的内核软件包，版本更新和插件同步都在那个仓库里由 workflow 完成 |
| 释放内存 | `package/new/luci-app-ramfree` | 来自 [sbwml/luci-app-ramfree](https://github.com/sbwml/luci-app-ramfree) |
| 软件包列表 | `scripts/zerowrt_core/configgen.py` | 在 `PACKAGES` 中统一维护 |

`package/new/` 下每个仓库一个目录，和 helloworld 平级：

```
package/new/helloworld/            # 代理插件
package/new/luci-app-ramfree/      # 释放内存
package/new/luci-theme-argon/      # 主题
```

凡是 `package/new/` 里有的包，feed 里的同名目录都会被删掉，由 `scripts/zerowrt_core/packages.py` 的 `PACKAGE_DIR_NAMES` 统一维护。
除了目录名，还会读每个 Makefile 实际 `BuildPackage` 出来的包名：`helloworld/v2ray-geodata` 生成 `v2ray-geoip` 和 `v2ray-geosite`，而 feed 从 `net/v2ray-geodata` 生成同样两个名字，只看目录名会漏掉这种重复。

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

登录 banner 来自 `assets/banner`（含 ANSI 颜色转义），构建时会整体覆盖源码树的
`package/base-files/files/etc/banner`；改这个文件即可，不必改代码。校验步骤会比对两侧内容，
不一致就判定失败。

### 关于 wget 依赖

`luci-theme-argon` 的 `LUCI_DEPENDS` 同时声明了 apk 和 opkg 两套依赖：

```make
+USE_APK:wget-any +!USE_APK:wget
```

OpenWrt 扫描包元数据时（`scripts/package-metadata.pl`）会**先按第一个冒号切分、再去校验依赖名是否存在**，
两边都会被查一遍；而 `wget-any` 这个虚拟包只在 apk 世界（25.12 以后）由 `uclient-fetch` 提供，
24.10 里没有任何包 provide 它，于是每次构建都会打印：

```
WARNING: Makefile 'package/new/luci-theme-argon/Makefile' has a dependency on 'wget-any', which does not exist
```

它只是一条警告（那条依赖会被丢掉，构建继续），但说明主题的依赖声明和当前包管理器不匹配。
`packages.py` 在克隆后把这一串改成 `+wget-ssl`：这棵树是 opkg，且主题的 rpcd 脚本
（`luci.argon_update`、`luci.argon_wallpaper`）用 `wget` 访问 https，`/usr/bin/wget` 由
`wget-ssl` 的 alternatives 提供。上游把这一行改成别的写法时脚本会直接报错，而不是继续刷警告。

## 五、设备

目前只支持锐捷 RG-X60 New，名字同时就是 Release tag。对应关系集中在
`scripts/zerowrt_core/profiles.py`：

```python
"ruijie_rg-x60-new": DeviceProfile(
    source="immortalwrt", board="mediatek", subtarget="filogic",
    device="ruijie_rg-x60-new-ubootmod", layout="OpenWrt U-Boot layout (ubootmod)",
),
```

`ruijie_rg-x60-new`：在 `target/linux/mediatek/image/filogic.mk` 中按
`define Device/ruijie_rg-x60-new-ubootmod` 查找，自动得到 `mediatek/filogic`。
profile 名字保持 `ruijie_rg-x60-new`，是为了让 Release tag 和 OTA 条目在换基线后不变。

当前支持：

```
ruijie_rg-x60-new   (ImmortalWrt, mediatek/filogic, Device/ruijie_rg-x60-new-ubootmod)
```

新增设备时：

1. 在 `profiles.py` 的 `SOURCES` 里登记源码树（如果和现在的 ImmortalWrt 不同）
2. 源码树里必须有对应的 `define Device/<name>` 定义，并在 `PROFILES` 里加一条
3. 在 [build.yml](.github/workflows/build.yml) 和 [toolchain.yml](.github/workflows/toolchain.yml) 里把 `ZEROWRT_DEVICE` 改成新名字，并补上 `--device` 参数

如果名称写错，工作流会失败并列出源码树里可选的设备名，便于排查。

## 六、固件版本与登录页

固件版本号使用构建日期（例如 `20261020`）：

- `include/version.mk` 的 `VERSION_NUMBER` 默认值在构建时改为日期
- `VERSION_NUMBER` 是隐藏 Kconfig 符号，不能写进 `.config`（会被 `defconfig` 丢弃），所以由 `version.mk` 提供
- `/etc/openwrt_release` 写成 `DISTRIB_DESCRIPTION='ZeroWrt-20261020'`、`DISTRIB_REVISION=' By MinimaxFlora'`；
  `/usr/lib/os-release` 写成 `OPENWRT_RELEASE="ZeroWrt 标准版 @R20261020 BY MinimaxFlora"`
- Argon 登录页 footer 去掉了空的 `revision` 后缀，因此显示为 `ZeroWrt 20261020`，不再出现 `ZeroWrt 24.10.5-`

## 七、软件包

包列表在 `scripts/zerowrt_core/configgen.py`：

```python
PACKAGES = [
    "CONFIG_PACKAGE_luci-theme-argon",
    "CONFIG_PACKAGE_luci-app-argon-config",  # 仅当独立插件被克隆（非 3.x 主题）时使用
    "CONFIG_PACKAGE_luci-app-passwall",
    "CONFIG_PACKAGE_luci-app-openclash",
    "CONFIG_PACKAGE_luci-app-ota",
    "CONFIG_PACKAGE_luci-i18n-ota-zh-cn",
    "CONFIG_PACKAGE_luci-app-ttyd",          # 终端
    "CONFIG_PACKAGE_luci-i18n-ttyd-zh-cn",
]
```

`luci-app-ttyd` 依赖 feeds 里的 `ttyd`，会进入固件。

PassWall 改用 **sing-box 内核**，同时显式关掉 Xray 和 SmartDNS：

```ini
CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SingBox=y
# CONFIG_PACKAGE_luci-app-passwall_INCLUDE_Xray is not set
# CONFIG_PACKAGE_luci-app-passwall_INCLUDE_SmartDNS is not set
CONFIG_PACKAGE_luci-app-passwall_INCLUDE_V2ray_Geodata=y
CONFIG_PACKAGE_sing-box=y
# CONFIG_PACKAGE_smartdns is not set
```

PassWall 的 Makefile 里 `INCLUDE_Xray`、`INCLUDE_SingBox`、`INCLUDE_SmartDNS` 三个选项对
aarch64 默认都是 `y`，所以三个都必须显式写出来，否则镜像里会同时出现 Xray 内核和
SmartDNS，体积变大还会在运行时抢 DNS。

`INCLUDE_V2ray_Geodata` 带进 `v2ray-geoip` / `v2ray-geosite`，安装到 `/usr/share/v2ray/`，
sing-box 的 geo 分流和 PassWall 界面的域名列表都依赖这两个文件；缺了它们 PassWall 会为每个
分流节点记一条“缺少 Geo 规则文件”的错误。

生成 `.config` 后会校验：`sing-box`、`INCLUDE_SingBox` 必须在，`xray-core`、`INCLUDE_Xray`、
`smartdns`、`INCLUDE_SmartDNS` 必须不在，任何一个不满足就直接失败，避免镜像里混进第二个内核或 DNS。

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

产物上传到 tag 为 `toolchain`、标题为 `Toolchain_Cache` 的 release，资产名是：

```
toolchain_<libc>_<arch>_gcc-<major>.tar.zst
```

`LIBC`/架构/GCC 版本从 `staging_dir/toolchain-*` 目录名解析，固件构建挑最新的匹配资产，
同名资产会被新构建覆盖。带设备前缀的旧资产（`toolchain_<device>_...`）不再被识别。

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
- 单元测试：`tests/test_zerowrt.py`（设置校验、IP/SSID/密码补丁、登录 banner、设备查找、`.config` 生成、Argon 品牌化、产物收集）
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
.github/workflows/toolchain.yml  # 工具链缓存
.github/workflows/quality.yml    # Ruff + 单元测试
assets/                          # 登录背景、Logo、登录 banner
scripts/zerowrt.py               # CLI 入口
scripts/zerowrt_core/
  settings.py                    # 参数校验（IP、WiFi、设备）
  profiles.py                    # 设备 → 源码树 / Device / 额外包
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

1. `Add luci-app-ota`：`packages ota` 把插件克隆到 `package/new/luci-app-ota`（`Generate .config` 之前），
   同时改掉 `tools/gen_ota_index.py` 的 `BAD_TOKENS`：上游会把文件名里带 `uboot` 的镜像全部排除，
   正好把 ubootmod 的 `-squashfs-sysupgrade.itb` 也排除掉，而且没有规则阻止它选中 `preloader.bin`。
   补丁把 `"uboot"` 换成 `"preloader"`、`"bl31"`，等于只排除引导文件；上游改了布局会直接报错而不是发错镜像。
2. `Embed OTA metadata`：写入 `/etc/ota/build.json`、`version.date` 和默认更新源地址（`/etc/uci-defaults`），让固件能自报设备名与构建时间
3. `Publish OTA page`：Release 发布后把页面、`ota.json`、`history.json` 推送到 `gh-pages` 分支

每次构建只更新 `ruijie_rg-x60-new` 自己在索引里的条目，其它条目保持不动。

> **RG-X60 New 换基线后不能跨版本在线升级。** 旧固件是 LEDE + 原厂分区布局，新固件是
> ImmortalWrt + **ubootmod** 布局，镜像格式和分区表都不同。Release tag 仍然是
> `ruijie_rg-x60-new`（OTA 索引不会出现两条设备），但发布说明和下载页会标注需要从
> U-Boot 恢复页全新刷机、不保留配置。
> 另外 `build.json` 的 `device` 用的是源码里的 `Device/` 名（`ruijie_rg-x60-new-ubootmod`），
> 旧固件按 `ruijie_rg-x60-new` 查索引会查不到条目，等于从机制上挡住了跨布局升级。

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
