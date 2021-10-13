#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: set_mixer_id.sh,v 1.16 2021/09/03 07:22:59 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used during installation to set up the mixer volume ID 
# parameter mixer_volume_id in /etc/radiod.conf
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#

# This script requires an English locale(C)
export LC_ALL=C

CONFIG=/etc/radiod.conf
BOOTCONFIG=/boot/config.txt
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

##### Start of main script ######
# Create log directory
sudo mkdir -p ${LOGDIR}
sudo chown pi:pi ${LOGDIR}

echo | tee ${LOG}
echo $0 $(date) | tee -a ${LOG}

# Get audio out setting, headphones, HDMI, DAC etc.
AUDIO_OUT=$(grep "audio_out=" ${CONFIG})
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
    sudo chown pi:pi ${LIB_MIXERID}
    sudo chmod +x ${LIB_MIXERID}
    echo "Mixer numid ${MIXERID} written to ${LIB_MIXERID}" | tee -a ${LOG}
else
    echo "Invalid mixer numid ${MIXERID}. ${LIB_MIXERID} unchanged" | tee -a ${LOG}
fi

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

