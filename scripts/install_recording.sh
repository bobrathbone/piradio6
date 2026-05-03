#!/bin/bash
# $Id: install_recording.sh,v 1.16 2026/04/26 16:39:17 bob Exp $
#
# Raspberry Pi Internet Radio - Install LiquidSoap
# This script installs and configures LiquidSoap recording utility
# See https://www.liquidsoap.info/doc-2.2.5/build.html
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.

# This script requires an English locale(C)
export LC_ALL=C

FLAGS=$1
DIR=/usr/share/radio

# Test flag - change to current directory
if [[ ${FLAGS} == "-t" ]]; then
    DIR=$(pwd)
fi

OS_RELEASE=/etc/os-release
LOGDIR=${DIR}/logs
LOG=${LOGDIR}/install_record.log
SCRIPTS_DIR=${DIR}/scripts
PREFS_DIR=/etc/apt/preferences.d
LIQUIDSOAP_PREF=liquidsoap.pref 

sudo rm -f ${LOG}
echo "$0 configuration log, $(date) " | tee ${LOG}
sudo chown ${USR}:${GRP} ${LOG}

CONFIG=/etc/radiod.conf

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

clear
ans=0
selection=1
GPIO=0

FFMPEG_PREF="/etc/apt/preferences.d/ffmpeg.pref"

# Get architecture
BIT=$(getconf LONG_BIT)     # 32 or 64-bit architecture
if [[ ${BIT} != 64 ]];then
    echo
    echo "The liquidsoap software can only be installed on a 64-bit OS" | tee -a ${LOG}
    echo "This is a ${BIT}-bit system!"  | tee -a ${LOG}
    echo -n "Press enter to continue: "
    read ans
    exit 1
fi

while [ $selection != 0 ]
do
    ans=$(whiptail --title "Recording utility & configuration" --menu "Choose your option" 15 75 9 \
    "1" "Select GPIO27 for the record button (default)" \
    "2" "Select GPIO05 for the record button (If using SPI devices)" \
    "3" "No record button or manually configure" \
    3>&1 1>&2 2>&3)

    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
            exit 0
    fi

    if [[ ${ans} == '1' ]]; then
        DESC="Use GPIO27 for the record button"
        GPIO=27

    elif [[ ${ans} == '2' ]]; then
        DESC="Use GPIO5 for the record button"
        GPIO=5

    elif [[ ${ans} == '3' ]]; then
        DESC="No record button or manually configure"
        GPIO=0

    fi

    whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
    selection=$?
done

# Configure record switch 
sudo sed -i -e "0,/^record_switch=/{s/record_switch=.*/record_switch=${GPIO}/}" ${CONFIG}

echo "Release ID $(release_id) $(codename)"

if [[ $(release_id) -ge 13 ]]; then
    # Trixie
    LIBS="libavcodec-dev libavcodec61 libavdevice61 libavfilter10 libavformat-dev libavformat61 libavutil-dev libavutil59 libpostproc58 libswresample-dev libswresample5 libswscale-dev libswscale8"
else
    # Bookworm
    LIBS="libavcodec-dev libavcodec59 libavdevice59 libavfilter8 libavformat-dev libavformat59 libavutil-dev libavutil57 libpostproc56 libswresample-dev libswresample4 libswscale-dev libswscale6"
fi
echo "Installing libraries"

CMD="sudo apt-get install -y ${LIBS}"
echo ${CMD} | tee -a ${LOG};
${CMD} | tee -a ${LOG};

# Install Debian copy of liquidsoap 
echo "Installing liquidsoap recording software"  | tee -a ${LOG}
echo "Get liquidsoap package from the Debian repository not the Raspberry Pi one" | tee -a ${LOG};
echo "${PREFS_DIR}/${LIQUIDSOAP_PREF}"
if [[ ! -f ${PREFS_DIR}/${LIQUIDSOAP_PREF} ]]; then
    CMD="sudo cp ${SCRIPTS_DIR}/${LIQUIDSOAP_PREF} ${PREFS_DIR}/${LIQUIDSOAP_PREF}"
    echo ${CMD}; ${CMD}
fi

CMD="sudo apt-get install liquidsoap -y"
echo ${CMD}; ${CMD}

echo "Configured record_switch in ${CONFIG}" | tee -a ${LOG};
grep "^record_switch=" ${CONFIG} | tee -a ${LOG};
echo ${CMD}  | tee -a ${LOG};
${CMD} | tee -a ${LOG};

if [[ ${GPIO} < 1 ]]; then
    echo "The record switch parameter in ${CONFIG} has been set to ${GPIO}" | tee -a ${LOG};
    echo "Configure the record_switch in ${CONFIG} if required" | tee -a ${LOG};
fi

echo "" | tee -a ${LOG};

liquidsoap --version 
if [[ $? -ne 0 ]]; then
    echo "ERROR: Installation of liquidsoap failed" | tee -a ${LOG};
else
    echo "The liquidsoap package successfully installed" | tee -a ${LOG};
fi

echo "" | tee -a ${LOG};
echo "End of recording facility installation" | tee -a ${LOG};

echo "A log of these changes has been written to ${LOG}" | tee -a ${LOG};
echo -n "End of installation. Press enter to continue: " 
read x

# End of configuration script

# set tabstop=4 shiftwidth=4 expandtab
# retab

