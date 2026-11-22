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

# 版本设置
sed -i 's/VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),OpenWrt)/VERSION_DIST:=$(if $(VERSION_DIST),$(VERSION_DIST),ZeroWrt)/' include/version.mk
sed -i 's/VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),OpenWrt)/VERSION_MANUFACTURER:=$(if $(VERSION_MANUFACTURER),$(VERSION_MANUFACTURER),ZeroWrt)/' include/version.mk
sed -i "s/DISTRIB_DESCRIPTION='[^']*'/DISTRIB_DESCRIPTION='ZeroWrt-$(date +%Y%m%d)'/g" package/base-files/files/etc/openwrt_release
sed -i "s/DISTRIB_REVISION='[^']*'/DISTRIB_REVISION=' By MinimaxFlora'/g" package/base-files/files/etc/openwrt_release
sed -i "s|^OPENWRT_RELEASE=\".*\"|OPENWRT_RELEASE=\"ZeroWrt 标准版 @R$(date +%Y%m%d) BY MinimaxFlora\"|" package/base-files/files/usr/lib/os-release

# 移除要替换的包
rm -rf feeds/packages/lang/{golang,rust}
rm -rf feeds/luci/themes/luci-theme-argon
rm -rf feeds/applications/{luci-app-airplay2,luci-app-argon-config,luci-app-diskman,luci-app-homeproxy,luci-app-mosdns,luci-app-nikki,luci-app-passwall,luci-app-passwall2}
rm -rf feeds/packages/net/{xray-core,v2ray-geodata,sing-box,chinadns-ng,dns2socks,hysteria,ipt2socks,microsocks,naiveproxy,shadowsocks-rust,shadowsocksr-libev,simple-obfs,tcping,v2ray-plugin,xray-plugin,geoview,shadow-tls,smartdns,mosdns,}

# Go 1.27
git clone --depth=1 -b 27.x https://github.com/sbwml/packages_lang_golang feeds/packages/lang/golang

# Rust
git clone --depth=1 https://github.com/sbwml/packages_lang_rust feeds/packages/lang/rust

# PassWall
git clone --depth 1 https://github.com/Openwrt-Passwall/openwrt-passwall-packages package/passwall-packages
git clone --depth 1 https://github.com/Openwrt-Passwall/openwrt-passwall package/passwall-luci
git clone --depth 1 https://github.com/Openwrt-Passwall/openwrt-passwall2 package/passwall-luci2

# OpenWrt-nikki
git clone --depth 1 https://github.com/nikkinikki-org/OpenWrt-nikki package/OpenWrt-nikki && rm -rf package/OpenWrt-nikki/mihomo-alpha

# Argon 主题
git clone --depth 1 https://github.com/jerrykuku/luci-theme-argon package/luci-theme-argon

# MosDNS
git clone --depth 1 https://github.com/sbwml/luci-app-mosdns package/luci-app-mosdns

# OpenList
git clone --depth 1 https://github.com/sbwml/luci-app-openlist2 package/luci-app-openlist2

# Diskman
git clone --depth 1 https://github.com/sbwml/luci-app-diskman package/luci-app-diskman

# Airconnect
git clone --depth 1 https://github.com/sbwml/luci-app-airconnect package/luci-app-airconnect

# 更改 Argon 主题背景
cp -f $GITHUB_WORKSPACE/images/bg1.webp package/luci-theme-argon/htdocs/luci-static/argon/img/bg1.webp

./scripts/feeds update -a
./scripts/feeds install -a
