#!/bin/bash
# set -x
# Raspberry Pi Internet Radio Waveshare LCDs configuration script
# $Id: install_ws_LCD.sh,v 1.21 2026/01/22 09:34:20 bob Exp $
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
# Script based on https://www.waveshare.com/wiki/3.5inch_RPi_LCD_(C)
# Waveshare Wiki's all products https://www.waveshare.com/wiki/Main_Page 

# This script requires an English locale(C)
export LC_ALL=C

FLAGS=$1
DIR=/usr/share/radio
# Test flag - change to current directory
if [[ ${FLAGS} == "-t" ]]; then
    DIR=$(pwd)
fi
PROG=${0}
LOGDIR=${DIR}/logs
LOG=${LOGDIR}/install_ws_lcd.log
CALIBRATOR=/usr/bin/xinput_calibrator
CALIBRATE_CONF="/usr/share/X11/xorg.conf.d/99-calibration.conf"
OS_RELEASE=/etc/os-release
CONFIG=/etc/radiod.conf
BOOTCONFIG=/boot/firmware/config.txt
EV_CONF_10="/usr/share/X11/xorg.conf.d/10-evdev.conf"
EV_CONF_45="/usr/share/X11/xorg.conf.d/45-evdev.conf"
USER=$(logname)
GRP=$(id -g -n ${USR})
GRADIO="${DIR}/gradio.py"
BASH_PROFILE="/home/${USER}/.bash_profile"
PROFILE="/home/${USER}/.profile"
EVTEST=/usr/bin/evtest
DISPLAY_TYPE="GRAPHICAL"
SCREEN_SIZE="480x320"

# Colours
orange='\033[33m'
default='\033[39m'

# Get OS release ID
function release_id
{
    VERSION_ID=$(grep VERSION_ID $OS_RELEASE)
    arr=(${VERSION_ID//=/ })
    ID=$(echo "${arr[1]}" | tr -d '"')
    ID=$(expr ${ID} + 0)
    echo ${ID}
}

# Get OS release name
function codename
{
    VERSION_CODENAME=$(grep VERSION_CODENAME $OS_RELEASE)
    arr=(${VERSION_CODENAME//=/ })
    CODENAME=$(echo "${arr[1]}" | tr -d '"')
    echo ${CODENAME}
}

# Get Raspberry Pi model
function rpi_model
{
    model=$(cat /proc/device-tree/model | cut -d ' ' -f 3)
    echo ${model}
}


# Releases before Bookworm not supported
if [[ $(release_id) -lt 12 ]]; then
    echo "This program is only supported on Debian Bookworm/Trixie or later!" | tee -a ${LOG}
    echo "This system is running $(codename) OS" | tee -a ${LOG}
    echo "Exiting program." | tee -a ${LOG}
    exit 1
fi


run=1
INSTALL_WS_SPI=0
CALIBRATE_TOUCH=0
EV_TEST=0
selection=1

while [ $selection != 0 ]
do
    ans=0
    ans=$(whiptail --title "Waveshare SPI touchscreen installation" --menu "Choose your option" 15 75 9 \
    "1" "Install Waveshare software (Do this first!)" \
    "2" "Calibrate Waveshare touch screen" \
    "3" "Test raw touchscreen events with evtest" \
    "4" "Exit" 3>&1 1>&2 2>&3)
    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
        exit 0

    elif [[ ${ans} == '1' ]]; then
        INSTALL_WS_SPI=1
        DESC="Install Waveshare 2.4/3.5 SPI touchscreen software"

    elif [[ ${ans} == '2' ]]; then
        CALIBRATE_TOUCH=1
        DESC="Calibrate touch screen"

    elif [[ ${ans} == '3' ]]; then
        EV_TEST=1
        DESC="Test touch screen events using evtest"
    fi
    whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
    selection=$?
done

# Install software components
if [[ ${INSTALL_WS_SPI} == '1' ]]; then
    : # NO-OP

# Run the X-screen calibrator software
elif [[ ${CALIBRATE_TOUCH} == '1' ]]; then
    if [[ ! -f ${CALIBRATE_CONF}.save ]]; then
        sudo cp ${CALIBRATE_CONF} ${CALIBRATE_CONF}.save
    fi
    sudo DISPLAY=:0.0 ${CALIBRATOR} --output-filename ${CALIBRATE_CONF}
    echo "New calibration details written to ${CALIBRATE_CONF}" | tee -a ${LOG}
    echo -n "Enter to continue: "
    read a
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
    echo "Enter the event number for the touch-screen, normally 3" | tee -a ${LOG};
    echo -n "Enter to continue: " | tee -a ${LOG};
    read a
    /usr/bin/evtest 
else
    echo "Error! You must install the Waveshare touch-screen software first!"
    echo -n "Press enter to continue: " | tee -a ${LOG};
    read a
    exit 1 
fi

echo "$0 configuration log, $(date) " | tee ${LOG}
echo "Installing Waveshare touch-screen software" | tee ${LOG}
echo "Hardware Raspberry Pi model $(rpi_model)" | tee -a ${LOG}

CMD="sudo apt-get install evtest -y"
echo ${CMD}  | tee -a ${LOG};
${CMD} | tee -a ${LOG};

if [[ ! -x /usr/bin/unzip ]]; then
    CMD="sudo apt-get install unzip -y"
    echo ${CMD}  | tee -a ${LOG};
    ${CMD} | tee -a ${LOG};
fi

if [[ ! -x /usr/bin/cmake ]]; then
    CMD="sudo apt-get install cmake -y"
    echo ${CMD}  | tee -a ${LOG};
    ${CMD} | tee -a ${LOG};
fi

sudo rm -f Waveshare35c.zip
CMD="wget https://files.waveshare.com/wiki/common/Waveshare35c.zip"
echo ${CMD} | tee -a ${LOG};
${CMD} | tee -a ${LOG};

CMD="sudo unzip ./Waveshare35c.zip"
echo ${CMD} | tee -a ${LOG};
${CMD} | tee -a ${LOG};

CMD="sudo mv waveshare35c.dtbo /boot/overlays/"
echo ${CMD} | tee -a ${LOG};
${CMD} | tee -a ${LOG};

# Remove redundant Waveshare35c.zip
sudo rm -f Waveshare35c.zip

echo "Disabling DRM VC4 V3D driver in ${BOOTCONFIG}" | tee -a ${LOG}
sudo sed -i 's/^dtoverlay=vc4-kms-v3d.*/\#dtoverlay=vc4-kms-v3d/'  ${BOOTCONFIG}
sudo sed -i 's/^max_framebuffers=.*/\#max_framebuffers=2/'  ${BOOTCONFIG}
grep "dtoverlay=vc4-kms-v3d"  ${BOOTCONFIG}  | tee -a ${LOG}
grep "max_framebuffers"  ${BOOTCONFIG}  | tee -a ${LOG}

grep "^dtoverlay=waveshare" ${BOOTCONFIG}
if [[ $? != 0 ]]; then      # Do not seperate from above 
    echo "" | tee -a ${LOG}
    echo "Adding touch-screen parameters to ${BOOTCONFIG}" | tee -a ${LOG}
    sudo echo "" | sudo tee -a  ${BOOTCONFIG} 
    sudo echo "# Waveshare parameters added by radiod" | sudo tee -a  ${BOOTCONFIG} 
    sudo echo "dtoverlay=spi=on" | sudo tee -a  ${BOOTCONFIG} 
    sudo echo "dtoverlay=waveshare35c" | sudo tee -a  ${BOOTCONFIG} 
    sudo echo "hdmi_force_hotplug=1" | sudo tee -a  ${BOOTCONFIG} 
    sudo echo "max_usb_current=1" | sudo tee -a  ${BOOTCONFIG} 
    sudo echo "hdmi_group=2" | sudo tee -a  ${BOOTCONFIG} 
    sudo echo "hdmi_mode=1" | sudo tee -a  ${BOOTCONFIG} 
    sudo echo "hdmi_mode=87" | sudo tee -a  ${BOOTCONFIG} 
    sudo echo "hdmi_cvt 480 320 60 6 0 0 0" | sudo tee -a  ${BOOTCONFIG} 
    sudo echo "hdmi_drive=2" | sudo tee -a  ${BOOTCONFIG} 
    sudo echo "display_rotate=0" | sudo tee -a  ${BOOTCONFIG} 
fi

echo ""  | tee -a ${LOG} 
echo "Install Waveshare touch-screen calibration software"  | tee -a ${LOG};
CMD="sudo apt-get install xserver-xorg-input-evdev"
echo ${CMD}  | tee -a ${LOG};
${CMD} | tee -a ${LOG};
CMD="sudo cp -f ${EV_CONF_10} ${EV_CONF_45}"
echo ${CMD}  | tee -a ${LOG};
${CMD} | tee -a ${LOG};

if [[ ! -x /usr/bin/xinput_calibrator ]]; then
    CMD="sudo apt-get install xinput-calibrator"
    echo ${CMD}  | tee -a ${LOG};
    ${CMD} | tee -a ${LOG};
fi

sudo touch ${CALIBRATION_CONF}
grep "calibration" ${CALIBRATION_CONF}
if [[ $? != 0 ]];then
    echo "" | tee -a ${LOG}
    echo "Setting up ${CALIBRATION_CONF}" | tee -a ${LOG}
    sudo tee -a ${CALIBRATION_CONF}  <<EOF
Section "InputClass"
        Identifier      "calibration"
        MatchProduct    "ADS7846 Touchscreen"
        Option  "Calibration"   "3932 300 294 3801"
        Option  "SwapAxes"      "1"
        #Option "EmulateThirdButton" "1"
        #Option "EmulateThirdButtonTimeout" "1000"
        #Option "EmulateThirdButtonMoveThreshold" "300"
EndSection
EOF
fi

echo "" | tee -a ${LOG}
echo "Setting screen_size and fullscreen in ${CONFIG}" | tee -a ${LOG}
sudo sed -i -e "0,/^screen_size=/{s/screen_size=.*/screen_size=${SCREEN_SIZE}/}" ${CONFIG}
sudo sed -i -e "0,/^fullscreen=/{s/fullscreen=.*/fullscreen=yes/}" ${CONFIG}
sudo sed -i -e "0,/^display_type/{s/display_type.*/display_type=${DISPLAY_TYPE}/}" ${CONFIG}
grep "^screen_size=" ${CONFIG} | tee -a ${LOG}
grep "^fullscreen=" ${CONFIG} | tee -a ${LOG}
grep "^display_type=" ${CONFIG} | tee -a ${LOG}

echo "" | tee -a ${LOG}
echo "Add startx and FRAMEBUFFER device in ${BASH_PROFILE}" | tee -a ${LOG}
touch ${BASH_PROFILE}
grep "FRAMEBUFFER" ${BASH_PROFILE}
if [[ $? != 0 ]]; then      # Do not separate from above 
    echo "" | tee -a ${LOG}
    echo "Setting up framebuffer configuration in ${BASH_PROFILE}" | tee -a ${LOG}
    if [[ ${rpi_model} -ge '5' ]]; then
        echo "export FRAMEBUFFER=/dev/fb1" >> ${BASH_PROFILE}
    else
        echo "export FRAMEBUFFER=/dev/fb0" >> ${BASH_PROFILE}
    fi 
    echo "startx 2> /tmp/xorg_errors" >> ${BASH_PROFILE}
fi

# For some reason  labwc/autostart will not start gradio.py on a small touchscreen
# This workaround launches gradio.py from .profile (Ignored if using an SSH login"
echo "" | tee -a ${LOG}
echo "Add start gradio.py command to ${PROFILE}" | tee -a ${LOG}
grep "gradio.py" ${PROFILE}
if [[ $? != 0 ]]; then      # Do not seperate from above
    echo "" | tee -a ${LOG}
    echo "Adding \"${GRADIO}\" to ${PROFILE}"  | tee -a ${LOG}
    echo "# Added by ${PROG}" >> ${PROFILE}
    echo "sudo ${GRADIO} &" >> ${PROFILE}
fi

echo ""  | tee -a ${LOG} 
echo "Set CLI to auto login (User ${USER})"  | tee -a ${LOG} 
CMD="sudo -u ${USER} sudo raspi-config nonint do_boot_behaviour B2"
echo ${CMD}  | tee -a ${LOG};
${CMD} | tee -a ${LOG};
sleep 2 # Important, allow raspi-config to finish
CMD="sudo -u ${USER} sudo raspi-config nonint do_wayland W1 &"
echo ${CMD}  | tee -a ${LOG};
${CMD} | tee -a ${LOG};

echo "" | tee -a ${LOG}
echo "A log of these changes has been written to ${LOG}"
echo "It is necessary to reboot the Raspberry Pi to implement changes"

# End of script

# set tabstop=4 shiftwidth=4 expandtab
# retab
