#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: configure_speech.sh,v 1.1 2002/02/24 14:42:36 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# Script to install the espeak facility (espeak)
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
# This program uses whiptail. Set putty terminal to use UTF-8 charachter set
# for best results

FLAGS=$1
DIR=/usr/share/radio
# Test flag - change to current directory
if [[ ${FLAGS} == "-t" ]]; then
    DIR=$(pwd)
fi
LOGDIR=${DIR}/logs
LOG=${LOGDIR}/install_speech.log

ESPEAK=/usr/bin/espeak
CONFIG=/etc/radiod.conf
APLAY=/usr/bin/aplay
MESSAGE="'Speech facility enabled'"
PLAY="${ESPEAK} -ven+f2 -k5 -s130 -a20 ${MESSAGE} --stdout | ${APLAY}"
VOICE=/var/lib/radiod/voice

echo "$0 Speech installation log (espeak), $(date) " | tee ${LOG}

ans=0
ans=$(whiptail --title "Configure speech facility (espeak)?" --menu "Choose your option" 15 75 9 \
"1" "Enable Speech facility?" \
"2" "Disable Speech facility?" \
"3" "Test Speech speech facility (stops radio!)?" \
"4" "Uninstall Speech facility?" 3>&1 1>&2 2>&3)

TEST=0
exitstatus=$?
if [[ $exitstatus != 0 ]]; then
   exit 0 
fi

if [[ ${ans} == '4' ]]; then
    echo "Un-installing espeak package" | tee ${LOG}
    sudo apt-get -y remove espeak | tee -a ${LOG}
    echo "This run has been recorded in ${LOG}"
    exit 0

elif [[ ${ans} == '3' ]]; then
    TEST=1 
fi

if [[ ${ans} == '1' ]]; then
    ENABLE_SPEECH=1
    DESC="Enable speech facility"
else
    ENABLE_SPEECH=0
    DESC="Disable speech facility"
fi

whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
selection=$?

if [[ ${TEST} == 1 ]]; then
    if [[ -f ${ESPEAK} ]]; then
        sudo systemctl stop radiod.service
        echo ${PLAY} | tee -a ${LOG}
        bash -c "${PLAY}"
    else
        clear
        echo "${ESPEAK} not installed - Exiting"  | tee -a ${LOG}
    fi
    exit 0
fi

VERBOSE=0
INFO=0
# Set speech options
if [[ ${ENABLE_SPEECH} == 1 ]]; then
    
    # Install epeak if not installed
    if [[ ! -f ${ESPEAK} ]]; then
        echo "Installing espeak package" | tee ${LOG}
        sudo apt-get -y install espeak | tee -a ${LOG}
    fi

    ans=0
    run=1

    while [ ${run} == 1 ] 
    do
        ans=$(whiptail --title "Configure speech facility (espeak)?" --menu "Choose your option" 15 75 9 \
        "1" "Enable verbose output?" \
        "2" "Speak information menu" \
        "3" "Exit selection" 3>&1 1>&2 2>&3)

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            run=0
        fi

        if [[ ${ans} == '1' ]]; then
            DESC="Enable verbose output"
            VERBOSE=1

        elif [[ ${ans} == '2' ]]; then 
            INFO=1

        elif [[ ${ans} == '3' ]]; then 
            run=0
        fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
    done
    
    if [[ ${VERBOSE} == 1 ]]; then
        sudo sed -i -e "0,/^#verbose=/{s/#verbose=.*/verbose=yes/}" ${CONFIG}
        sudo sed -i -e "0,/^verbose=/{s/verbose=.*/verbose=yes/}" ${CONFIG}
    else
        sudo sed -i -e "0,/^#verbose=/{s/#verbose=.*/verbose=no/}" ${CONFIG}
        sudo sed -i -e "0,/^verbose=/{s/verbose=.*/verbose=no/}" ${CONFIG}
    fi

    if [[ ${INFO} == 1 ]]; then
        sudo sed -i -e "0,/^#speak_info=/{s/#speak_info=.*/speak_info=yes/}" ${CONFIG}
        sudo sed -i -e "0,/^speak_info=/{s/speak_info=.*/speak_info=yes/}" ${CONFIG}
    else
        sudo sed -i -e "0,/^#speak_info=/{s/#speak_info=.*/speak_info=no/}" ${CONFIG}
        sudo sed -i -e "0,/^speak_info=/{s/speak_info=.*/speak_info=no/}" ${CONFIG}
    fi

    # Enable speech in /etc/radiod.conf
    sudo sed -i -e "0,/^#speech=/{s/#speech=.*/speech=yes/}" ${CONFIG}
    sudo sed -i -e "0,/^speech=/{s/speech=.*/speech=yes/}" ${CONFIG}
else
    sudo sed -i -e "0,/^#speech=/{s/#speech=.*/speech=no/}" ${CONFIG}
    sudo sed -i -e "0,/^speech=/{s/speech=.*/speech=no/}" ${CONFIG}
fi

# Sumarise changes
echo "Changes made to ${CONFIG} for speech facility (espeak)" | tee -a ${LOG}
grep "^speech=" ${CONFIG} | tee -a ${LOG} 
grep "^verbose=" ${CONFIG}| tee -a ${LOG} 
grep "^speech_volume=" ${CONFIG}| tee -a ${LOG} 
grep "^speak_info=" ${CONFIG}| tee -a ${LOG} 
echo "The voice settings are found in the ${VOICE} file" | tee -a ${LOG}
cat ${VOICE} | tee -a ${LOG}
echo "For further information on espeak see https://espeak.sourceforge.net/" | tee -a ${LOG}
echo "This run has been recorded in ${LOG}"

exit 0

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
