# 设备配置

本目录是每个设备的 **`diffconfig.sh` 差异配置**，不是 9000 多行的完整 `.config`：

```bash
./scripts/diffconfig.sh > netcore-n60-pro.config
```

构建时 `config apply`：

```text
复制 configs/<设备>.config 到源码树/.config
→ make defconfig 展开默认值
→ 校验唯一设备/关键包
→ 编译
```

这样仓库里每个配置只有约 380 行，新增/修改设备时不需要手工维护完整 Kconfig。

## 文件命名

设备 profile 里的 `_` 换成 `-`：

```text
netcore_n60-pro              -> netcore-n60-pro.config
ruijie_rg-x60-new            -> ruijie-rg-x60-new.config
ruijie_ew-6000gx-pro-expand  -> ruijie-ew-6000gx-pro-expand.config
supergateway_s20m            -> supergateway-s20m.config
```

## 重新生成

源码、feeds 或插件变化后，在 Linux 源码树执行：

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
→ ./scripts/diffconfig.sh > configs/<设备>.config
```

生成结果提交到仓库后再跑 `Build ZeroWrt`。
