#!/bin/bash

# Nikki 配置
uci set nikki.mixin.geoip_format='dat'
uci set nikki.mixin.geodata_loader='standard'
uci set nikki.mixin.geosite_url='https://testingcf.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/geosite.dat'
uci set nikki.mixin.geoip_dat_url='https://testingcf.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/geoip.dat'
uci set nikki.mixin.geox_auto_update='1'
uci set nikki.mixin.geox_update_interval='24'
uci commit nikki

exit 0
