#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: install_equalizer.sh,v 1.2 2024/12/14 17:15:10 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used during installation to set up the Graphic Equalizer
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.

# This script requires an English locale(C)
export LC_ALL=C

script=$0
CONFIG=/etc/radiod.conf
DIR=/usr/share/radio
MPDCONF=/etc/mpd.conf
ASOUND_DIR=${DIR}/asound
ASOUND_CONF=/etc/asound.conf
LOGDIR=${DIR}/logs
LOG=${LOGDIR}/equalizer.log
TMP=/tmp/card_id$$
CARD=0  # Default audio device card number
PLUGIN='plug:plugequal'
EQUALIZER_CMD=/var/lib/radiod/equalizer.cmd
APLAY=aplay

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

echo "$0 Installing Graphic Equalizer $(date)" | tee ${LOG}

# Get audio out setting, headphones, HDMI, DAC etc.
AUDIO_OUT=$(grep -i "audio_out=" ${CONFIG}) 
if [[ $? == 0 ]]; then
    arry=(${AUDIO_OUT//=/ })
    DEVICE=${arry[1]}
    CARD=$(getCard ${DEVICE})
fi

# Check device compatability
TYPE=''
grep '^\stype\s' ${MPDCONF} | grep '"pulse"' > /dev/null
if [[ $? == 0 ]]; then 
    echo "Pulse devices are not compatible with the equalizer software" | tee -a ${LOG}
    echo "Exiting ${script}"
    exit 1
fi

if [[ ${DEVICE} =~ "wm8960"]] || ${DEVICE} =~ "bluetooth" ]]; then
    echo "The ${DEVICE} device is not compatible with the equalizer software" | tee -a ${LOG}
    echo "Exiting ${script}"
    exit 1
fi

echo "Configuring equalizer for device ${DEVICE} card ${CARD}" | tee -a  ${LOG}

SCARD=$(grep audio_out= ${CONFIG})

# Setup Equalizer asound.conf
if [[ ! -f ${ASOUND_CONF}.save ]]; then
    CMD="sudo cp -f ${ASOUND_CONF} ${ASOUND_CONF}.save" 
    echo ${CMD} | tee -a ${LOG} 
    ${CMD}
fi

# Install equalizer software
echo "Install equalizer software" | tee -a ${LOG}
sudo apt-get install -y libasound2-plugin-equal | tee -a ${LOG}
echo | tee -a ${LOG}

# Copy equalizer distribution asound.conf to /etc/asound.conf
CMD="sudo cp ${DIR}/asound/asound.conf.dist.equalizer ${ASOUND_CONF}"
echo ${CMD} | tee -a ${LOG} 
${CMD}

# Set card number in /etc/asound.conf
echo "Setting card number and equalizer in ${ASOUND_CONF}" | tee -a ${LOG}
sudo sed -i -e "0,/card [0-9]/{s/card [0-9]/card ${CARD}/}" ${ASOUND_CONF}
sudo sed -i -e "0,/plughw:0,0/{s/plughw:[0-9],[0-9]/plughw:${CARD},0/}" ${ASOUND_CONF}
grep "card [0-9]" ${ASOUND_CONF} | tee -a ${LOG}
grep "plughw:" ${ASOUND_CONF} | tee -a ${LOG}

# Add equalizer plugin to /etc/mpd.conf
echo "Setting device to ${PLUGIN} in ${MPDCONF}" | tee -a ${LOG}
sudo sed -i -e "0,/device/{s/.*device.*/\#\tdevice\t\t\"${PLUGIN}\"/}" ${MPDCONF}
sudo sed -i -e "0,/device/{s/.*device.*/\tdevice\t\t\"${PLUGIN}\"/}" ${MPDCONF}
grep ${PLUGIN} ${MPDCONF} | tee -a ${LOG}

# Set card number in equalizer command in /var/lib/radio/equalizer.cmd
echo "Setting card number in ${EQUALIZER_CMD} to ${CARD}" | tee -a ${LOG}
sudo sed -i -e "0,/alsamixer -c [0-9]/{s/alsamixer -c [0-9]/alsamixer -c ${CARD}/}" ${EQUALIZER_CMD}
grep "^lxterminal" ${EQUALIZER_CMD} | tee -a ${LOG}

echo
echo "A log of this installation run will be found in ${LOG}"

exit 0

# End of script

# set tabstop=4 shiftwidth=4 expandtab
# retab
