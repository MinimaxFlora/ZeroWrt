# 设备配置

本目录是 **已经执行过 `make defconfig` 的完整 `.config`**，每个设备一份。构建时
`config apply` 只做两件事：

1. 把 `configs/<设备>.config` 复制到源码树根目录的 `.config`；
2. 校验文件中只有当前设备这一行 `CONFIG_TARGET_DEVICE_...=y`，且关键插件存在。

不会再执行 `make defconfig`，所以工作流不需要每次重新展开依赖。

## 文件命名

设备 profile 里的 `_` 换成 `-`：

```text
netcore_n60-pro              -> netcore-n60-pro.config
ruijie_rg-x60-new            -> ruijie-rg-x60-new.config
ruijie_ew-6000gx-pro-expand  -> ruijie-ew-6000gx-pro-expand.config
supergateway_s20m            -> supergateway-s20m.config
```

## 重新生成

上游源码、feeds 或插件变化后，在 Linux 源码树执行：

```bash
python3 scripts/zerowrt.py config generate \
  --tree /builder/source \
  --out configs
```

该命令会对 12 个设备依次：

```text
高功率模板 → 删除旧设备 → 加入当前设备 + 插件
→ make defconfig
→ 校验唯一设备/关键包
→ 写入 configs/<设备>.config
```

生成结果需要提交到仓库后再跑 `Build ZeroWrt`。
