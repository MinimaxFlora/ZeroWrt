# 贡献指南

欢迎提 Issue 和 PR。先说清楚这个仓库**不是**什么，能省你不少时间：

> 这里没有 OpenWrt 源码。LEDE 源码树是私有仓库，由 GitHub Secrets 提供，只有维护者能在 Actions 里拉取。
> 这个仓库装的是**构建流水线本身**：`scripts/`、`tests/`、品牌素材 `assets/`，以及触发它们的 workflow。

所以大部分改动是 Python，能在你自己的机器上几分钟内验证完；**完整的固件编译不需要也不应该在你本地跑**。

## 快速开始

```bash
git clone https://github.com/MinimaxFlora/ZeroWrt.git
cd ZeroWrt

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Python 要求 **3.11 及以上**（`pyproject.toml` 的 `target-version = "py311"`）。

## 提交前必跑

```bash
ruff check scripts tests
ruff format --check scripts tests
python -m unittest discover -s tests -v
```

这三条就是 CI 里 `quality.yml` 的全部内容。它们不全绿，PR 就不会被合并。

`ruff format` 可以直接改写文件，格式化问题不用手动修：

```bash
ruff format scripts tests
```

> Trade-off：为什么装了 Pillow 才算通过测试？`ArgonBrandingTest` 会断言 favicon 真的被缩放到指定尺寸，
> 没有 Pillow 时函数会退化为"直接用原图"，断言失效。`[dev]` 里已经装了，别跳过。

## 代码规范

`pyproject.toml` 里定了：行宽 120，规则集 `E, F, W, I, UP, B, SIM`。除此之外遵循这几条不成文的约定：

- **`from __future__ import annotations`** —— 所有模块都加，然后放心用 `str | None` 这类新语法
- **错误信息要能指导下一步** —— 抛 `util.BuildError`，内容写清"哪里错了 / 该怎么修"，而不是 `assert failed`。参考 `source.verify_core()`：它会在失败时列出所有问题，而不是遇到第一个就崩。
- **不要在脚本里 hardcode 上游结构** —— 这是踩过坑的一条。曾经把 target profile 符号写死成
  `CONFIG_TARGET_x86_64_Generic`，上游改了 device 名后 `defconfig` 静默丢弃这个符号，构建失败且很难查。
  现在的做法是**从源码树里真实解析**。同理，涉及".config 里的包名"的改动，请确认这个包真的存在。
- **不要吞掉失败** —— `check=False` 的 subprocess 后面要有明确的处理或告警，不要指望下游自己发现。

## 测试怎么加

所有测试继承 `tests/test_zerowrt.py` 里的 `TempTreeTest`，它给你一棵临时的假源码树：

```python
class MyPatchTest(TempTreeTest):
    def test_something(self) -> None:
        self.write("include/version.mk", VERSION_MK)
        patches.patch_something(self.root)
        self.assertIn("ZeroWrt", util.read_text(self.root / "include" / "version.mk"))
```

用 `self.write()` 造最小输入，**不要依赖真实 LEDE 树**（私有且巨大）。现有的 `CorePatchesTest`、
`DeviceLookupTest`、`FeedConflictTest` 都是这个套路，照着抄最快。

## 关于 `package/new`

新增外部插件时统一克隆到这里，**一个仓库一个目录，和 `helloworld/` 平级**：

```
package/new/helloworld/         # MinimaxFlora/openwrt_helloworld
package/new/luci-app-ramfree/   # sbwml/luci-app-ramfree
package/new/luci-app-mosdns/    # sbwml/luci-app-mosdns
package/new/luci-theme-argon/   # jerrykuku/luci-theme-argon
```

并且必须在 `scripts/zerowrt_core/packages.py` 的 `PACKAGE_DIR_NAMES` 里登记包名 ——
feeds 里的同名包会依据这份清单自动被删掉，漏登记会让 buildroot 报 duplicate package。

这里有个坑值得单独说：**只比对目录名是不够的**。`helloworld/v2ray-geodata` 这个目录实际
`BuildPackage` 出来的是 `v2ray-geoip` 和 `v2ray-geosite`，而 feeds 从 `net/v2ray-geodata` 生成同样两个名字。
所以 `packages.declared_package_names()` 会去读 Makefile 的真实包名，按"目录名 OR 实际包名"双路删除。
如果你加了新仓库，跑一下 `FeedConflictTest` 确认这套逻辑覆盖到了。

## 同步更新这些地方

改动行为时，别只改代码：

| 改了什么 | 还要动哪里 |
| --- | --- |
| 选装包列表 | `docs/BUILD.md` 的定制表 + `README.md` 的 Features |
| 新增 / 移除设备 | `build.yml` 与 `toolchain.yml` 的 `device.options`、`README.md` 的设备表 |
| `assets/` 素材 | `docs/BUILD.md` 的品牌化章节 |
| 值得用户知道的变更 | `CHANGELOG.md` 的 Unreleased 段 |

## 提交信息与 PR

提交信息用 Conventional Commits，仓库已经在用：

```
build: switch the PassWall core from Sing-Box to Xray
fix: resolve x86_64 device from the source tree
docs: describe the package/new layout
```

PR 请填 `.github/pull_request_template.md`，重点说清**影响面**：会不会改变生成的 `.config`、
会不会只影响某一个设备、是否需要重跑 toolchain 缓存 —— 这些决定了合并后要不要重新编译。

## 合并之后

**合并不会自动触发固件编译。** `build.yml` 和 `toolchain.yml` 都是 `workflow_dispatch`（手动触发），
所以没人点"Run workflow"就不会有人跑那个六小时的编译。需要出固件的话，改完在 PR 里说一声。

## 安全相关

- 不要提交任何 token、密钥、`feeds.conf` 里的私有地址。Secrets 走 GitHub Secrets，
  本地验证时用环境变量，不要写进文件，更不要 `git add -f`。
- 如果你发现的是**安全漏洞**，不要开公开 Issue，请走 [SECURITY.md](SECURITY.md) 里的私密通道。
