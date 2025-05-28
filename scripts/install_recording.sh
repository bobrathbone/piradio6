#!/bin/bash
# $Id: install_recording.sh,v 1.7 2025/05/20 16:01:41 bob Exp $
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

LOGDIR=${DIR}/logs
LOG=${LOGDIR}/install_record.log

sudo rm -f ${LOG}
echo "$0 configuration log, $(date) " | tee ${LOG}
sudo chown ${USR}:${GRP} ${LOG}

CONFIG=/etc/radiod.conf

clear
ans=0
selection=1
GPIO=0

LIQUIDSOAP_DEB="https://github.com/savonet/liquidsoap/releases/download/v2.2.5/liquidsoap_2.2.5-debian-bookworm-1_arm64.deb"
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

echo "Installing liquidsoap recording software"  | tee -a ${LOG}

echo "The system needs to downgraded to the standard distribution for liquidsoap to work" | tee -a ${LOG};
CMD="sudo apt-get dist-upgrade"
echo ${CMD}  | tee -a ${LOG}; 
${CMD} | tee -a ${LOG};

CMD="sudo apt-get -y install opam"
echo ${CMD}  | tee -a ${LOG}; 
${CMD} | tee -a ${LOG};

CMD="sudo apt-get -y install ffmpeg libavcodec-dev libavcodec59 libavdevice59 libavfilter8 libavformat-dev libavformat59 libavutil-dev libavutil57 libpostproc56 libswresample-dev libswresample4 libswscale-dev libswscale6"
echo ${CMD} | tee -a ${LOG};
${CMD} | tee -a ${LOG};


CMD="sudo apt-get -y install libfdk-aac2 libjemalloc2 liblo7 libpcre3 libportaudio2"
echo ${CMD}  | tee -a ${LOG}; 
${CMD} | tee -a ${LOG};

cd
CMD="wget ${LIQUIDSOAP_DEB}"
echo ${CMD}  | tee -a ${LOG};
${CMD} | tee -a ${LOG};

CMD="sudo dpkg -i liquidsoap_2.2.5-debian-bookworm-1_arm64.deb"
echo ${CMD}  | tee -a ${LOG};
${CMD} | tee -a ${LOG};
cd -

# Downgrade ffmpeg
CMD="sudo apt-get -y remove ffmpeg" 
echo ${CMD}  | tee -a ${LOG};
${CMD} | tee -a ${LOG}

sleep 2 
CMD="sudo apt-get -y install ffmpeg"
echo ${CMD}  | tee -a ${LOG};
${CMD} | tee -a ${LOG};

CMD="sudo cp -f ${DIR}/ffmpeg.pref ${FFMPEG_PREF}"

echo "Configured record_switch in ${CONFIG}" | tee -a ${LOG};
grep "^record_switch=" ${CONFIG} | tee -a ${LOG};
echo ${CMD}  | tee -a ${LOG};
${CMD} | tee -a ${LOG};

if [[ ${GPIO} < 1 ]]; then
    echo "The record switch parameter in ${CONFIG} has been set to ${GPIO}" | tee -a ${LOG};
    echo "Configure the record_switch in ${CONFIG} if required" | tee -a ${LOG};
fi

echo "" | tee -a ${LOG};

liquidsoap --version | tee -a ${LOG};
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

