#!/bin/bash
# Raspberry Pi Internet Radio
# $Id: show_translation.py,v 1.1 2020/10/10 15:00:47 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# Display translation settings

CONFIG=/etc/radiod.conf
LOG=/var/log/radio.log

echo "Translation settings in ${CONFIG}"
echo "========================================"
grep "translate_lcd=" ${CONFIG}
grep "language=" ${CONFIG}
grep "codepage=" ${CONFIG}
grep "controller=" ${CONFIG}
grep "romanize=" ${CONFIG}
echo
head ${LOG} | grep Loaded | awk '{print $4 " " $5}'
