#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: set_mixer_id.sh,v 1.3 2024/12/06 15:50:53 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used during installation to set up the mixer volume ID 
# parameter mixer_volume_id in /var/lib/radiod
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
# The set_mixer_id script is called from the radiod program to set the alsa mixer ID
# unless audio_config_locked in /etc/radiod.conf is set to yes
# It gets the audio devices from the 'aplay -l' command and compares the name configured
# in the audio_out parameter in /etc/radiod.conf. For example: audio_out="headphones"
# would display:
# card 2: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]
#
# It uses the card number (2 in this case) to get the volume mixer id from the amixer command 
# $ amixer -c2 controls
#
# This gives the following and identifies the mixer ID for Volume as 1
# numid=2,iface=MIXER,name='PCM Playback Switch'
# numid=1,iface=MIXER,name='PCM Playback Volume' 
#
# The reason for all this is that earlier versions of the Raspberry Pi OS if
# the HDMI cable was removed the aplay command would only display the "Headphones" device
# and its card number will have changed to Card 0. 
# card 0: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]
#
# However the HDMI devices do not now disapear if the cable is pulled out and the 
# latest vc4-kms-v3d HDMI drivers are being used

# This script requires an English locale(C)
export LC_ALL=C

# Version 7.5 onwards allows any user with sudo permissions to install the software
USR=$(logname)
GRP=$(id -g -n ${USR})

CONFIG=/etc/radiod.conf
BOOTCONFIG=/boot/config.txt
BOOTCONFIG_2=/boot/firmware/config.txt
OS_RELEASE=/etc/os-release
LIBDIR=/var/lib/radiod
LIB_MIXERID=${LIBDIR}/mixer_volume_id
LIB_HDMI=${LIBDIR}/hdmi
MIXERID=0
SAVEIFS=${IFS}
CARD=0              # Default audio device card number
DEVICE="headphones" # Default device
TMP=/tmp/mixer$$
DIR=/usr/share/radio
LOGDIR=${DIR}/logs
LOG=${LOGDIR}/set_mixer_id.log

# Controls strings for amixer ( The order of these is important)
CONTROLS="A2DP_Playback_Volume Digital_Playback_Volume Master_Playback_Volume Speaker_Playback_Volume Analogue_Playback_Volume Playback_Volume"

# This function identifies the card that matches the device
# string specified by the device string. For example "headphones"
# Returns the card number for the specified device string
# If no audio_out parameter specified, configure for card 0
function getCard {
    # Remove quotes
    sDevice=$(echo $1 | sed -e 's/^"//' -e 's/"$//')
    ${APLAY} > ${TMP}
    aplay -l | grep -i ^card > ${TMP}
    while read -r card
    do
        echo ${card} | grep -i ${sDevice} >/dev/null 2>&1
        ret=$?
        if [[ $ret -eq "0" ]]; then
            device=$(echo ${card} | awk '{print $2}')
            device=${device%:}
            break
        fi
    done < ${TMP}
    rm -f ${TMP}

    if [[ ${device} == "" ]];then
        device='0'
    fi
    let nDevice=${device}   # Convert to a number
    echo ${nDevice}
}

# Get OS release ID
function release_id
{
    VERSION_ID=$(grep VERSION_ID $OS_RELEASE)
    arr=(${VERSION_ID//=/ })
    ID=$(echo "${arr[1]}" | tr -d '"')
    ID=$(expr ${ID} + 0)
    echo ${ID}
}

##### Start of main script ######
# Create log directory
sudo mkdir -p ${LOGDIR}
sudo chown ${USR}:${GRP} ${LOGDIR}

echo | tee ${LOG}
echo $0 $(date) | tee -a ${LOG}

# Get audio out setting, headphones, HDMI, DAC etc.
AUDIO_OUT=$(grep -i "audio_out=" ${CONFIG})
if [[ $? == 0 ]]; then
    arry=(${AUDIO_OUT//=/ })
    DEVICE=${arry[1]}
    CARD=$(getCard ${DEVICE})
fi

if [[ ${DEVICE} =~ bluetooth ]]; then
    echo "Configuring Bluetooth device" | tee -a ${LOG}
else
    echo "Card ${CARD} ${DEVICE}" | tee -a ${LOG}
fi

# Find the play ID for the volume control
for control in ${CONTROLS}
do 
	text=$(echo ${control} | sed 's/_/ /g')

	# Get the mixer volume ID and set in radiod.conf
    if [[ ${DEVICE} =~ bluetooth ]]; then
        VOL=$(amixer -D bluealsa controls | grep -i "${text}")
    else
        VOL=$(amixer -c ${CARD} controls | grep -i "${text}")
    fi

	IFS=","
	read -ra ELEMENTS <<< "${VOL}"
	for i in "${ELEMENTS[@]}"; do
		if [[ $i =~ "numid" ]]; then
			IFS="="
			read -ra NUMID <<< "${i}"
			MIXERID=${NUMID[1]}
            echo "Using ${text}" | tee -a ${LOG}
			break
		fi
	done
    if [[ ${MIXERID} > 0 ]]; then
        break;
    fi
done
IFS=${SAVEIFS}
echo "mixer_volume_id=${MIXERID}" | tee -a ${LOG}

# Update /var/lib/radiod/mixer_volume_id with control (numid) number
if [[ ${MIXERID} > 0 ]]; then
    sudo rm -f ${LIB_MIXERID}
    sudo echo ${MIXERID} > ${LIB_MIXERID} 
    sudo chown ${USR}:${GRP} ${LIB_MIXERID}
    sudo chmod +x ${LIB_MIXERID}
    echo "Mixer numid ${MIXERID} written to ${LIB_MIXERID}" | tee -a ${LOG}
else
    echo "Could not find a suitable mixer control for volume for card ${CARD}" | tee -a ${LOG}
    echo "${LIB_MIXERID} unchanged" | tee -a ${LOG}
    CMD="amixer -c ${CARD} controls"
    echo ${CMD} | tee -a ${LOG}
    echo "--------------------" 
    ${CMD}
    echo "Exiting" |  tee -a ${LOG}
    exit 1
fi

# In Bookworm (Release ID 12) the configuration has been moved to /boot/firmware/config.txt
if [[ $(release_id) -ge 12 ]]; then
    BOOTCONFIG=${BOOTCONFIG_2}
fi

echo "Boot configuration in ${BOOTCONFIG}" | tee -a ${LOG} 

grep "dtparam=audio=on" ${BOOTCONFIG}
if [[ $? == 0 ]]; then 	# Do not seperate from above
	# Set output for HDMI on on-board jack
	if [[ -f ${LIB_HDMI} ]]; then
		echo "Configuring HDMI audio output" | tee -a ${LOG}
		MODE=2
		sudo rm -f ${LIB_HDMI}
	else
		echo "Configuring on-board jack audio output" | tee -a ${LOG}
		MODE=1
	fi
    # Switch to on-board headphone jack
    if [[ ${MIXERID} > 0 ]]; then
        cmd="sudo amixer cset numid=${MIXERID} ${MODE}" >/dev/null 2>&1
        echo ${cmd} | tee -a ${LOG}
        ${cmd} 
    else
        echo "Invalid mixer numid ${MIXERID}. Unable to configure on-board jack"  | tee -a ${LOG}
    fi
fi

# End of script

