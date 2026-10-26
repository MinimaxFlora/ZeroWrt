## 改了什么

<!-- 一两句话。如果要别人 review，写清"为什么改"比"改了什么"更有用。 -->

## 影响面

<!-- 勾=yes。这几项决定了合并后要不要重新出固件、要不要重建 toolchain 缓存。 -->

- [ ] **改变了生成的 `.config`**（增删包、改目标符号）—— 需要重新构建才能生效
- [ ] **只影响单一设备** —— 若是，说明哪一台：`ruijie_rg-x60-new` / `x86_64`
- [ ] **影响 toolchain 缓存** —— 若是，合并后需重跑 *Build Toolchain Cache*
- [ ] **只影响文档 / 素材 / 治理文件，不影响产物**

补充：

<!-- 例如：新增插件的 upstream 地址、为什么换实现、删掉了什么冗余 -->

## 本地验证

<!-- CI 里的 quality.yml 就是下面这三条，请自己在本地先跑一遍 -->

```bash
ruff check scripts tests
ruff format --check scripts tests
python -m unittest discover -s tests -v
```

- [ ] 上述三条全部通过
- [ ] 新增 / 更新了对应的单元测试（改行为的 PR 必须要有）

<!-- 如果本地实在跑不了完整固件编译（正常，这需要 Actions 环境），请说明你验证了哪一层，
     以及打算怎么确认它在真实构建里生效。 -->

## 相关

<!-- Closes #123 / Relates to #123 -->

## 同步检查

<!-- 改动通常会牵连这几处，漏了会在后续构建里炸 -->

- [ ] `docs/BUILD.md` 的定制表 / `README.md` 的 Features 已同步（改了选包、设备、素材时）
- [ ] `CHANGELOG.md` 的 Unreleased 段已补充（值得用户知道的变更）
- [ ] 未提交任何 token、密钥或私有仓库地址
