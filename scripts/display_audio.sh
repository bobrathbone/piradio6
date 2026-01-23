#!/bin/bash
# Raspberry Pi Internet Radio display configuration for analysis
# $Id: display_audio.sh,v 1.8 2026/01/15 13:28:24 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is diagnostic to display the OS and radio configuration
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#

# This script requires an English locale(C)
export LC_ALL=C

DIR=/usr/share/radio
LOGDIR=${DIR}/logs
LOG=${LOGDIR}/audio.log
BOOTCONFIG=/boot/config.txt
BOOTCONFIG_2=/boot/firmware/config.txt
MPD_CONFIG=/etc/mpd.conf
OS_RELEASE=/etc/os-release
EMAIL=bob@bobrathbone.com
DEBIAN_VERSION=/etc/debian_version
CONFIG=/etc/radiod.conf
RADIOLIB=/var/lib/radiod
ASOUND=/etc/asound.conf
SOUND_CARD=0
DKMS=/usr/sbin/dkms
WM8960_LOG=/var/log/wm8960-soundcard.log
BLUETOOTHCTL=/usr/bin/bluetoothctl

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

# Create run log directory
mkdir -p ${LOGDIR}
sudo chown ${USR}:${GRP} ${LOGDIR}

echo "Audio configuration log for $(hostname) $(date)" | tee ${LOG}
grep ^Release ${DIR}/README | tee -a ${LOG}

# Display sound devices
echo | tee -a ${LOG}
echo ${CONFIG}
echo "-----------------"
AUDIO_OUT=`grep audio_out= ${CONFIG}`
echo ${AUDIO_OUT} | tee -a ${LOG}
grep "^audio_config_locked="  ${CONFIG} | tee -a ${LOG}

echo "" | tee -a ${LOG}
echo "aplay -l" | tee -a ${LOG}
echo "--------" | tee -a ${LOG}
if [[ ${AUDIO_OUT} =~ bluetooth  ]]; then
    echo ${AUDIO_OUT}  | tee -a ${LOG}
else
    /usr/bin/aplay -l | tee -a ${LOG}
fi
aplay -L | grep -i pulse | tee -a ${LOG}

# Display Radio lib configuration
echo | tee -a ${LOG}
echo "${RADIOLIB} relevant audio settings" | tee -a ${LOG}
echo "---------------------------------------" | tee -a ${LOG}
echo "audio_out_card=$(cat ${RADIOLIB}/audio_out_card)" | tee -a ${LOG}
echo "mixer_volume=$(cat ${RADIOLIB}/mixer_volume)" | tee -a ${LOG}
echo "mixer_volume_id=$(cat ${RADIOLIB}/mixer_volume_id)" | tee -a ${LOG}

echo | tee -a ${LOG}
if [[ ${AUDIO_OUT} =~ bluetooth  || ${AUDIO_OUT} =~ USB ]]; then
    echo "Mixer controls for card ${SOUND_CARD}" | tee -a ${LOG}
    echo "--------------" | tee -a ${LOG}
fi
if [[ ${AUDIO_OUT} =~ bluetooth  ]]; then
    cmd="amixer -D bluealsa controls"
elif [[ ${AUDIO_OUT} =~ USB  ]]; then
    SOUND_CARD=1
    cmd="amixer -c ${SOUND_CARD} controls 2>$1" | tee -a ${LOG}
fi

# Display /etc/asound.conf configuration
if [[ -f ${ASOUND} ]]; then
    echo | tee -a ${LOG}
    echo "${ASOUND} configuration file" | tee -a ${LOG}
    echo "-----------------------------------" | tee -a ${LOG}
    cat ${ASOUND} | tee -a ${LOG}
fi

# Display MPD configuration
echo | tee -a ${LOG}
echo "MPD Configuration" | tee -a ${LOG}
echo "-----------------" | tee -a ${LOG}

mpd -V | grep Daemon | tee -a ${LOG}
if [[ $? -ne 0 ]];then
    mpd -V | tee -a ${LOG}
fi
mpc help | grep -i "version:"
if [[ $? -ne 0 ]];then
    "Error: mpc not found"  | tee -a ${LOG}
fi
echo | tee -a ${LOG}

if [[ -f  ${MPD_CONFIG} ]]; then
    grep -A 8 ^audio_output  ${MPD_CONFIG} | tee -a ${LOG}
else
    echo "FATAL ERROR!" | tee -a ${LOG}
    echo "MPD (Music Player Daemon) has not been installed" | tee -a ${LOG}
    echo "Install packages mpd,mpc and python3-mpd" | tee -a ${LOG}
    echo "and rerun configure_radio.sh to set-up the radio software" | tee -a ${LOG}
    exit 1
fi

# Display MPD outputs
echo | tee -a ${LOG}
echo "MPD outputs" | tee -a ${LOG}
echo "-----------" | tee -a ${LOG}
mpc outputs | tee -a ${LOG}

if [[ -f /usr/bin/pulseaudio ]];then
    echo | tee -a ${LOG}
    echo "The pulseaudio package appears to be installed" | tee -a ${LOG}
fi 

# Display boot configuration
# In Bookworm (Release ID 12) the configuration has been moved to /boot/firmware/config.txt
if [[ $(release_id) -ge 12 ]]; then
    BOOTCONFIG=${BOOTCONFIG_2}
fi

echo | tee -a ${LOG}
echo ${BOOTCONFIG} | tee -a ${LOG}
echo "-------------------------" | tee -a ${LOG}
grep ^hdmi ${BOOTCONFIG} | tee -a ${LOG}
grep ^dtparam= ${BOOTCONFIG} | tee -a ${LOG}
grep ^dtoverlay ${BOOTCONFIG} | tee -a ${LOG}
grep ^gpio=..=op,dh ${BOOTCONFIG} | tee -a ${LOG}

if [[ -x ${DKMS} ]]; then
    if [[ ${AUDIO_OUT} =~ "wm8960soundcard" ]]; then
        echo | tee -a ${LOG}
        echo "${DKMS} status" | tee -a ${LOG}
        echo "---------------------" | tee -a ${LOG}
        status=$(${DKMS} status)
        if [[ ${status} == "" ]]; then
            echo "ERROR: dkms module wm8960soundcard not loaded" | tee -a ${LOG}
            if [[ -f ${WM8960_LOG} ]]; then
                echo | tee -a ${LOG}
                echo ${WM8960_LOG} | tee -a ${LOG}
                echo "-----------------------------" | tee -a ${LOG}
                cat  ${WM8960_LOG} | tee -a ${LOG}
                echo "-------End of ${WM8960_LOG}-------" | tee -a ${LOG}
            fi
        else
            echo ${status} | tee -a ${LOG}
        fi
    fi
fi

# Display any Bluetooth devices
if [[ -x ${BLUETOOTHCTL} ]]; then
    echo "" | tee -a ${LOG}
    echo "Connected Bluetooth devices" | tee -a ${LOG}
    echo "---------------------------" | tee -a ${LOG}
    ${BLUETOOTHCTL} info | tee -a ${LOG}
fi

# Pulseaudio status
echo | tee -a ${LOG}
PKG=pulseaudio
dpkg -s ${PKG} | grep Package | tee -a ${LOG}
dpkg -s ${PKG} | grep Status | tee -a ${LOG}

# Create tar file
tar -zcf ${LOG}.tar.gz ${LOG} >/dev/null 2>&1

echo | tee -a ${LOG}
echo "This configuration has been recorded in ${LOG}"
echo "A compressed tar file has been saved in ${LOG}.tar.gz" | tee -a ${LOG}
echo | tee -a ${LOG}
echo "Send ${LOG}.tar.gz to ${EMAIL} if required" | tee -a ${LOG}
echo | tee -a ${LOG}

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab

