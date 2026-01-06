#!/usr/bin/bash
#!/bin/bash
# set -x
# Raspberry Pi Internet Radio Adafruit touchscreen configuration script
# $Id: install_adafruit_tft.sh,v 1.2 2026/01/02 16:25:26 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program installs the LUMA driver software from OLEDs and TFTs
# It normally called from the configure_radio.sh script
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
# The authors shall not be liable for any loss or damage however caused.
#
# This program uses whiptail. Set putty terminal to use UTF-8 charachter set
# for best results
#
# Script based on https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/easy-install-2

# This script requires an English locale(C)
FLAGS=$1
DIR=/usr/share/radio
# Test flag - change to current directory
if [[ ${FLAGS} == "-t" ]]; then
    DIR=$(pwd)
fi
PROG=${0}
LOGDIR=${DIR}/logs

EXTERNALLY_MANAGED="/usr/lib/python3.11/EXTERNALLY-MANAGED"     # Bookworm
EXTERNALLY_MANAGED2="/usr/lib/python3.13/EXTERNALLY-MANAGED"    # Trixie

CONFIG=/etc/radiod.conf
OS_RELEASE=/etc/os-release

DISPLAY_TYPE="GRAPHICAL"
SCREEN_SIZE="480x320"

USR=$(logname)
GRP=$(id -g -n ${USR})

# Get OS release ID
function release_id
{
    VERSION_ID=$(grep VERSION_ID $OS_RELEASE)
    arr=(${VERSION_ID//=/ })
    ID=$(echo "${arr[1]}" | tr -d '"')
    ID=$(expr ${ID} + 0)
    echo ${ID}
}

sudo apt-get install -y git python3-pip

# Install dependicies
if [[ $(release_id) -ge 13 ]]; then
    if [[ -f ${EXTERNALLY_MANAGED2} ]]; then
        sudo mv ${EXTERNALLY_MANAGED2} ${EXTERNALLY_MANAGED2}.old   # Trixie
    fi
elif [[ $(release_id) -eq 12 ]]; then
    if [[ -f ${EXTERNALLY_MANAGED} ]]; then
        sudo mv ${EXTERNALLY_MANAGED} ${EXTERNALLY_MANAGED}.old     # Bookworm
    fi
fi

pip3 install --upgrade adafruit-python-shell click Flask-SQLAlchemy
git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git
cd Raspberry-Pi-Installer-Scripts

echo "" | tee -a ${LOG}
echo "Setting screen_size and fullscreen in ${CONFIG}" | tee -a ${LOG}
sudo sed -i -e "0,/^screen_size=/{s/screen_size=.*/screen_size=${SCREEN_SIZE}/}" ${CONFIG}
sudo sed -i -e "0,/^fullscreen=/{s/fullscreen=.*/fullscreen=yes/}" ${CONFIG}
sudo sed -i -e "0,/^display_type/{s/display_type.*/display_type=${DISPLAY_TYPE}/}" ${CONFIG}
grep "^screen_size=" ${CONFIG} | tee -a ${LOG}
grep "^fullscreen=" ${CONFIG} | tee -a ${LOG}
grep "^display_type=" ${CONFIG} | tee -a ${LOG}

sudo -E env PATH=$PATH python3 adafruit-pitft.py

exit 0
