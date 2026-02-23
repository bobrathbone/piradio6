#!/usr/bin/bash
#!/bin/bash
# set -x
# Raspberry Pi Internet Radio Adafruit touchscreen configuration script
# $Id: install_adafruit_tft.sh,v 1.9 2026/02/13 09:23:00 bob Exp $
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
SCREEN_SIZE="480x320"   # 3.5-inch screen. Smaller not supported

USR=$(logname)
GRP=$(id -g -n ${USR})

STMPE_RULES="/etc/udev/rules.d/95-stmpe.rules"
RULE='SUBSYSTEM=="input", ATTRS{name}=="stmpe-ts", ENV{DEVNAME}=="*event*", SYMLINK+="input/touchscreen"'

# Get OS release ID
function release_id
{
    VERSION_ID=$(grep VERSION_ID $OS_RELEASE)
    arr=(${VERSION_ID//=/ })
    ID=$(echo "${arr[1]}" | tr -d '"')
    ID=$(expr ${ID} + 0)
    echo ${ID}
}


# Get Raspberry Pi model
function rpi_model
{
    model=$(cat /proc/device-tree/model | cut -d ' ' -f 3)
    echo ${model}
}

EVTEST=/usr/bin/evtest
TSTEST=/usr/bin/ts_test
INSTALL_ADA_SPI=0
CALIBRATE_TOUCH=0
TS_TEST=0
EV_TEST=0
selection=1

while [ $selection != 0 ]
do
    ans=0
    ans=$(whiptail --title "Adafruit SPI touchscreen installation" --menu "Choose your option" 15 75 9 \
    "1" "Install Adafruit software (Do this first!)" \
    "2" "Calibrate Adafruit touch screen" \
    "3" "Test touchscreen  with ts_test" \
    "4" "Test raw touchscreen events with evtest" \
    "5" "Exit" 3>&1 1>&2 2>&3)
    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
        exit 0

    elif [[ ${ans} == '1' ]]; then
        INSTALL_ADA_SPI=1
        DESC="Install Adafruit 2.8/3.5 SPI touchscreen software"

    elif [[ ${ans} == '2' ]]; then
        CALIBRATE_TOUCH=1
        DESC="Calibrate touch screen"

    elif [[ ${ans} == '3' ]]; then
        TS_TEST=1
        DESC="Test touch screen with ts_test"

    elif [[ ${ans} == '4' ]]; then
        EV_TEST=1
        DESC="Test touch screen events using evtest"
    fi

    whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
    selection=$?
done

# Install software components
if [[ ${INSTALL_ADA_SPI} == '1' ]]; then
    : # NO-OP

# Run the X-screen calibrator software
elif [[ ${CALIBRATE_TOUCH} == '1' ]]; then
    CMD="sudo TSLIB_FBDEVICE=/dev/fb0 TSLIB_TSDEVICE=/dev/input/touchscreen ts_calibrate"
    echo ${CMD}; ${CMD}
    echo ""
    exit 0

# Run ts_test software
elif [[ ${TS_TEST} == '1' ]]; then
    if [[ ! -x ${TSTEST} ]]; then
        echo -n "Install touch-sreen software first. Enter to continue: "
        read a
        exit 1
    fi
    CMD="sudo TSLIB_FBDEVICE=/dev/fb0 TSLIB_TSDEVICE=/dev/input/touchscreen ${TSTEST}"
    echo ${CMD}; ${CMD}
    echo ""
    exit 0

# Run evtest software
elif [[ ${EV_TEST} == '1' ]]; then
    if [[ ! -x ${EVTEST} ]]; then
        echo -n "Install touch-sreen software first. Enter to continue: "
        read a
        exit 1
    fi
    echo ""
    echo "The program will now run evtest and display the available devices:" | tee -a ${LOG};
    echo "Enter the event number for the stmpe-ts device" | tee -a ${LOG};
    echo -n "Enter to continue: " | tee -a ${LOG};
    read a
    CMD="/usr/bin/evtest"
    echo ${CMD}; ${CMD}
    echo ""
    exit 0
else
    echo "Error! You must install the Adafruit touch-screen software first!"
    echo -n "Press enter to continue: " | tee -a ${LOG};
    read a
    exit 1
fi

echo "$0 configuration log, $(date) " | tee ${LOG}
echo "Installing Adafruit touch-screen software" | tee ${LOG}
echo "Hardware Raspberry Pi model $(rpi_model)" | tee -a ${LOG}

sudo apt-get install -y git python3-pip
sudo apt-get install -y evtest libts-bin
sudo apt-get install -y xinput

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

# Update stmpe_ts module (Check if required)
#echo "Update ${STMPE_RULES}" | tee -a ${LOG}
#CMD="sudo echo ${RULE} ${STMPE_RULES}" 
#echo ${CMD} | tee -a ${LOG}
#${CMD}
#sudo rmmod stmpe_ts; sudo modprobe stmpe_ts

sudo -E env PATH=$PATH python3 adafruit-pitft.py

exit 0
