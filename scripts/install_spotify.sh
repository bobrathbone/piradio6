#!/bin/bash
# $Id: install_spotify.sh,v 1.8 2025/01/10 17:24:33 bob Exp $
# Raspberry Pi Internet Radio - Install Spotify
# This script installs and configures Spotify (librespot)
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.

FLAGS=$1
DIR=/usr/share/radio
# Test flag - change to current directory
if [[ ${FLAGS} == "-t" ]]; then
    DIR=$(pwd)
fi

LOGDIR=${DIR}/logs
SCRIPTS_DIR=${DIR}/scripts
LOG=${LOGDIR}/install_spotify.log
RADIO_CONFIG=/etc/radiod.conf
SPOTIFY_SERVICE=/lib/systemd/system/raspotify.service
RASPOTIFY_CONF=/etc/raspotify/conf

# Identify card ID from "aplay -l" command

function get_audio_device
{
    X=$(grep "^audio_out=" ${RADIO_CONFIG})
    AUDIO_OUT=$(echo ${X} | awk -F '=' '{print $2}')
    AUDIO_OUT=$(echo ${AUDIO_OUT} | sed 's/"//g')
    echo ${AUDIO_OUT}
}

function card_id
{
    name=$1
    # Match first line only
    CARD_ID=$(aplay -l | grep -m1 ${name} | awk '{print $2}')
    CARD_ID=$(echo "${CARD_ID}" | tr -d ':')
    if [[ ${#CARD_ID} < 1 ]]; then
        CARD_ID=0
    fi
    CARD_ID=$(expr ${CARD_ID} + 0)
    echo ${CARD_ID}
}


# Install details
echo "$0 configuration log, $(date) " | tee ${LOG}
echo "Using ${DIR}" | tee -a ${LOG}

echo "Installing Spotify (librespot)" | tee -a ${LOG}
sudo apt-get install apt-transport-https | tee -a ${LOG}
cd 
curl -sL https://dtcooper.github.io/raspotify/install.sh | sh | tee -a ${LOG}

echo | tee -a ${LOG}

# Set up Spotify device for raspotify.service 
AUDIO_DEVICE=$(get_audio_device)
# Handle bluetooth
if [[ ${AUDIO_DEVICE} =~ bluetooth ]]; then
    SPOTIFY_DEVICE="btdevice"
else
    CARD=$(card_id ${AUDIO_DEVICE} )
    SPOTIFY_DEVICE="hw:${CARD},0"
fi
echo "Audio device ${AUDIO_DEVICE} ${SPOTIFY_DEVICE}" | tee -a ${LOG}
# Set the audio device card number in the Spotify service
sudo sed -i -e "0,/^ExecStart=/{s/librespot.*/librespot --device=hw:${CARD},0/}" ${SPOTIFY_SERVICE}
#sudo sed -i -e "0,/^ExecStart=/{s/librespot.*/librespot --device=${SPOTIFY_DEVICE}" ${SPOTIFY_SERVICE}
echo "Changes made to ${SPOTIFY_SERVICE}" | tee -a ${LOG}
grep "^ExecStart=" ${SPOTIFY_SERVICE} | tee -a ${LOG}


# Reload Spotify service
sudo systemctl daemon-reload 

# Run the set_mixer_id.sh script
${SCRIPTS_DIR}/set_mixer_id.sh | tee -a ${LOG}

# Disable Raspotify (Controlled by radio program)
echo "Stopping and disabling Spotify service (Controlled by radio program)" | tee -a ${LOG}
sudo systemctl stop raspotify
sudo systemctl disable raspotify

if [[ ! -f  ${RASPOTIFY_CONF}.orig ]]; then
    sudo cp -f ${RASPOTIFY_CONF}  ${RASPOTIFY_CONF}.orig
else
    # Restore original Raspotify configuration
    sudo cp -f ${RASPOTIFY_CONF}.orig  ${RASPOTIFY_CONF}
fi

# Set volume levels (Initialy spotify client controls volume)"
sudo sed -i -e "0,/^#LIBRESPOT_VOLUME_RANGE=/{s/^#LIBRESPOT_VOLUME_RANGE.*/LIBRESPOT_VOLUME_RANGE=\"100.0\"/}" ${RASPOTIFY_CONF}
sudo sed -i -e "0,/^#LIBRESPOT_INITIAL_VOLUME=/{s/^#LIBRESPOT_INITIAL_VOLUME.*/LIBRESPOT_INITIAL_VOLUME=\"100\"/}" ${RASPOTIFY_CONF}

# Comment out LIBRESPOT_QUIET parameter 
sudo sed -i -e "0,/^LIBRESPOT_QUIET/{s/^LIBRESPOT_QUIET.*/#LIBRESPOT_QUIET/}" ${RASPOTIFY_CONF}

echo  | tee -a ${LOG}
echo "Changes made to ${RASPOTIFY_CONF}" | tee -a ${LOG}
sudo grep "LIBRESPOT_QUIET" ${RASPOTIFY_CONF} | tee -a ${LOG}
sudo grep "LIBRESPOT_VOLUME_RANGE" ${RASPOTIFY_CONF} | tee -a ${LOG}
sudo grep "LIBRESPOT_INITIAL_VOLUME" ${RASPOTIFY_CONF} | tee -a ${LOG}
echo | tee -a ${LOG}

echo "Note: Raspotify messages during operation can be observed with the following command" | tee -a ${LOG}
echo "journalctl --lines 0 --follow _SYSTEMD_UNIT=raspotify.service" | tee -a ${LOG}

echo
echo "Spotify installation complete" | tee -a ${LOG}
echo "A log of this run will be found in ${LOG}"

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
