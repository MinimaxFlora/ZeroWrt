#!/bin/bash

# 修改主机名称
sed -i 's/LEDE/ZeroWrt/g' package/base-files/files/bin/config_generate
sed -i 's/LEDE/ZeroWrt/g' package/base-files/luci/bin/config_generate

# 修改默认IP
sed -i 's/192.168.1.1/10.0.0.1/g' package/base-files/files/bin/config_generate
sed -i 's/192.168.1.1/10.0.0.1/g' package/base-files/luci/bin/config_generate

# 修改默认密码
default_password=$(openssl passwd -5 password)
sed -i "s|^root:[^:]*:|root:${default_password}:|" package/base-files/files/etc/shadow

# SSH 登录横幅
mkdir -p files/etc
cp -f $GITHUB_WORKSPACE/scripts/banner files/etc/banner

# Kernel 版本
sed -i 's/KERNEL_PATCHVER:=6\.18/KERNEL_PATCHVER:=7.3/' target/linux/x86/Makefile

# TTYD 免登录
sed -i 's|/bin/login|/bin/login -f root|g' feeds/packages/utils/ttyd/files/ttyd.config
sed -i 's/services/system/g' feeds/luci/applications/luci-app-ttyd/root/usr/share/luci/menu.d/luci-app-ttyd.json
sed -i '3 a\\t\t"order": 50,' feeds/luci/applications/luci-app-ttyd/root/usr/share/luci/menu.d/luci-app-ttyd.json
sed -i 's/procd_set_param stdout 1/procd_set_param stdout 0/g' feeds/packages/utils/ttyd/files/ttyd.init
sed -i 's/procd_set_param stderr 1/procd_set_param stderr 0/g' feeds/packages/utils/ttyd/files/ttyd.init

# profile
sed -i 's#\\u@\\h:\\w\\\$#\\[\\e[32;1m\\][\\u@\\h\\[\\e[0m\\] \\[\\033[01;34m\\]\\W\\[\\033[00m\\]\\[\\e[32;1m\\]]\\[\\e[0m\\]\\\$#g' package/base-files/files/etc/profile
sed -ri 's/(export PATH=")[^"]*/\1%PATH%:\/opt\/bin:\/opt\/sbin:\/opt\/usr\/bin:\/opt\/usr\/sbin/' package/base-files/files/etc/profile
sed -i '/ENV/i\export TERM=xterm-color' package/base-files/files/etc/profile

# bash
sed -i 's#ash#bash#g' package/base-files/files/etc/passwd
sed -i '\#export ENV=/etc/shinit#a export HISTCONTROL=ignoredups' package/base-files/files/etc/profile
mkdir -p files/root
cp -f $GITHUB_WORKSPACE/scripts/.bash_profile files/root/.bash_profile
cp -f $GITHUB_WORKSPACE/scripts/.bashrc files/root/.bashrc

# 版本设置
sed -i 's/VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),OpenWrt)/VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),ZeroWrt)/' include/version.mk
sed -i 's/VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),OpenWrt)/VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),ZeroWrt)/' include/version.mk
sed -i "s/DISTRIB_DESCRIPTION='LEDE '/DISTRIB_DESCRIPTION='ZeroWrt '/" package/lean/default-settings/files/zzz-default-settings
sed -i 's/OPENWRT_RELEASE="LEDE R@BUILD_DATE@"/OPENWRT_RELEASE="ZeroWrt R@BUILD_DATE@"/' package/lean/default-settings/files/zzz-default-settings

# 修改默认主题
sed -i 's/luci-theme-design/luci-theme-brutal/g' include/target.mk

# 移除要替换的包
rm -rf feeds/packages/lang/golang
rm -rf feeds/luci/themes/luci-theme-argon
rm -rf feeds/luci/applications/{luci-app-argon-config,luci-app-diskman,luci-app-mosdns,luci-app-nikki,luci-app-passwall,luci-app-passwall2,luci-app-lucky}
rm -rf feeds/packages/net/{xray-core,v2ray-geodata,sing-box,chinadns-ng,dns2socks,hysteria,ipt2socks,microsocks,naiveproxy,shadowsocks-rust,shadowsocksr-libev,simple-obfs,tcping,v2ray-plugin,xray-plugin,geoview,shadow-tls,mihomo,nikki,smartdns,mosdns,lucky}

# Go 1.27
git clone --depth=1 -b 27.x https://github.com/sbwml/packages_lang_golang feeds/packages/lang/golang

# PassWall
git clone --depth 1 https://github.com/Openwrt-Passwall/openwrt-passwall-packages package/passwall-packages
git clone --depth 1 https://github.com/Openwrt-Passwall/openwrt-passwall package/passwall-luci
git clone --depth 1 https://github.com/Openwrt-Passwall/openwrt-passwall2 package/passwall-luci2

# OpenWrt-nikki
git clone --depth 1 https://github.com/nikkinikki-org/OpenWrt-nikki package/OpenWrt-nikki && rm -rf package/OpenWrt-nikki/mihomo-alpha

# Argon 主题
git clone --depth 1 https://github.com/jerrykuku/luci-theme-argon package/luci-theme-argon

# 更改 Argon 主题背景
cp -f $GITHUB_WORKSPACE/images/bg1.webp package/luci-theme-argon/htdocs/luci-static/argon/img/bg1.webp

# Brutal 主题
git clone --depth 1 https://github.com/MinimaxFlora/luci-theme-brutal package/luci-theme-brutal

# bash-completion 自动补全
git clone --depth 1 https://github.com/MinimaxFlora/bash-completion package/bash-completion

# MosDNS
git clone --depth 1 https://github.com/sbwml/luci-app-mosdns package/luci-app-mosdns

# OpenList
git clone --depth 1 https://github.com/sbwml/luci-app-openlist2 package/luci-app-openlist2

# Diskman
git clone --depth 1 https://github.com/sbwml/luci-app-diskman package/luci-app-diskman

# Airconnect
git clone --depth 1 https://github.com/sbwml/luci-app-airconnect package/luci-app-airconnect

# Lucky
git clone --depth 1 https://github.com/gdy666/luci-app-lucky package/luci-app-lucky

# OTA 在线更新
git clone --depth 1 https://github.com/MinimaxFlora/luci-app-ota package/luci-app-ota

# ── OTA 构建元数据 ────────────────────────────────────────────────────────────
# luci-app-ota 靠 /etc/ota/build.json 知道自己是哪台设备、什么时候编译的：
#   * device  决定去 ota.json 里查哪个 key（x86 还需 +efi / +bios 变体）
#   * build_date 与新索引里的时间戳比较，才判断得出「有新版本」
# 同时写入默认索引地址（/etc/uci-defaults/90-luci-app-ota），用户改过的配置优先。
# 各设备的工作流通过环境变量覆盖 OTA_DEVICE / OTA_TARGET / OTA_MODEL。
OTA_META_TOOL="package/luci-app-ota/tools/embed_ota_meta.py"
if [ ! -f "$OTA_META_TOOL" ]; then
	echo "::error::luci-app-ota 没有克隆成功（缺少 $OTA_META_TOOL），OTA 无法工作"
	exit 1
fi

OTA_DEVICE="${OTA_DEVICE:-x86_64}"
OTA_MODEL="${OTA_MODEL:-}"
OTA_TARGET="${OTA_TARGET:-x86/64}"
OTA_VERSION="${OTA_VERSION:-$(TZ=Asia/Shanghai date +%Y%m%d)}"
OTA_BUILD_DATE="${OTA_BUILD_DATE:-$(date +%s)}"
OTA_API_URL="${OTA_API_URL:-https://ota.tatalvpai.vip/ota.json}"

# 构建时间戳同时写进 build.json 与 version.date：
# 插件以 build.json 为准；version.date 只是给支持 SOURCE_DATE_EPOCH 的树用（LEDE 忽略它）。
python3 "$OTA_META_TOOL" \
	--tree . \
	--device "$OTA_DEVICE" \
	${OTA_MODEL:+--model "$OTA_MODEL"} \
	--target "$OTA_TARGET" \
	--version "$OTA_VERSION" \
	--build-date "$OTA_BUILD_DATE" \
	--api-url "$OTA_API_URL" \
	--emit "$PWD/ota-meta.json" || {
	echo "::error::OTA 元数据写入失败（embed_ota_meta.py 返回非 0）"
	exit 1
}

# 插件自带的 uci-defaults 只在「已有 config 段」时才能写进 api_url；
# 从其它固件（iStoreOS / 老版 OTA）带过来的 /etc/config/ota 往往是
# `config global 'network'`，此时 uci set 会报 Invalid argument，索引地址
# 就永远写不进去。这里换成一个先补段再写值的版本。
OTA_UCI_DEFAULTS="package/base-files/files/etc/uci-defaults/90-luci-app-ota"
cat > "$OTA_UCI_DEFAULTS" <<EOF
#!/bin/sh
# luci-app-ota: 首次启动写入默认更新索引。用户改过的值优先。
[ -f /etc/config/ota ] || exit 0
uci -q get ota.config >/dev/null 2>&1 || uci -q set ota.config=ota
[ -n "\$(uci -q get ota.config.api_url)" ] || uci -q set ota.config.api_url='$OTA_API_URL'
[ -n "\$(uci -q get ota.config.download_proxy)" ] || uci -q set ota.config.download_proxy='https://gh-proxy.tatalvpai.vip'
uci -q commit ota
exit 0
EOF
chmod 755 "$OTA_UCI_DEFAULTS"

cat "$PWD/ota-meta.json"
cat package/base-files/files/etc/ota/build.json
cat "$OTA_UCI_DEFAULTS"

./scripts/feeds update -a
./scripts/feeds install -a
