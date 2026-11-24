#!/bin/bash

# 关闭 Lucky
uci set lucky.@lucky[0].enabled='0'
uci commit lucky
/etc/init.d/lucky stop

exit 0
