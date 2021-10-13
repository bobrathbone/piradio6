#!/bin/bash
# Raspberry Pi Internet Radio display Wi-Fi details
# $Id: display_wifi.sh,v 1.6 2021/06/05 05:52:30 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is diagnostic to display the WiFi configuration
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#

# This script requires an English locale(C)
export LC_ALL=C

echo 
echo "Wi-Fi network information" 
echo "-------------------------" 
id=$(iwgetid)
if (( ${#id} < 5 )); then
    echo "Wi-Fi not configured"
else
    echo "Hostname: $(hostname)"
    echo "Wi-FI: ${id}" | sed 's/  */ /g'
    echo "IP address wlan0: $(ifconfig wlan0 | grep 'inet ' | awk '{print $2}')"
    iwgetid -ap | sed 's/  */ /g'
#   iwgetid -a
    iwlist channel 2>&1| grep Current | sed 's/^[ \t]*//;s/[ \t]*$//'
    iwlist txpower 2>&1 | grep -i tx-power | sed 's/\s/ /g' | sed 's/^[ \t]*//;s/[ \t]*$//'
fi