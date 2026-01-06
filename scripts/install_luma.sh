#!/bin/bash
# set -x
# Raspberry Pi Internet Radio LUMA LCDs configuration script
# $Id: install_luma.sh,v 1.5 2025/12/14 09:04:22 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program installs the LUMA driver software from OLEDs and TFTs
# It normally called from the configure_audio.sh script
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
# The authors shall not be liable for any loss or damage however caused.
#
# This program uses whiptail. Set putty terminal to use UTF-8 charachter set
# for best results

# This script requires an English locale(C)
export LC_ALL=C

FLAGS=$1
DIR=/usr/share/radio
# Test flag - change to current directory
if [[ ${FLAGS} == "-t" ]]; then
    DIR=$(pwd)
fi

LOGDIR=${DIR}/logs
LOG=${LOGDIR}/install_luma.log
DOCS_DIR=${DIR}/docs
EXTERNALLY_MANAGED="/usr/lib/python3.11/EXTERNALLY-MANAGED"     # Bookworm
EXTERNALLY_MANAGED2="/usr/lib/python3.13/EXTERNALLY-MANAGED"    # Trixie

OS_RELEASE=/etc/os-release

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

# Get OS release name
function codename
{
    VERSION_CODENAME=$(grep VERSION_CODENAME $OS_RELEASE)
    arr=(${VERSION_CODENAME//=/ })
    CODENAME=$(echo "${arr[1]}" | tr -d '"')
    echo ${CODENAME}
}

echo "$0 configuration log, $(date) " | tee ${LOG}

# Releases before Bullseye not supported
if [[ $(release_id) -lt 11 ]]; then
    echo "This program is only supported on Raspbian Bullseye/Bookworm or later!" | tee -a ${LOG}
    echo "This system is running $(codename) OS" | tee -a ${LOG}
    echo "Exiting program." | tee -a ${LOG}
    exit 1
fi

echo "Using ${DIR}" | tee -a ${LOG}

# Install dependicies
if [[ $(release_id) -ge 13 ]]; then
    if [[ -f ${EXTERNALLY_MANAGED2} ]]; then
        sudo mv ${EXTERNALLY_MANAGED2} ${EXTERNALLY_MANAGED2}.old   # Trixie
    fi
elif [[ $(release_id) -eq 12 ]]; then
    if [[ -f ${EXTERNALLY_MANAGED} ]]; then
        sudo mv ${EXTERNALLY_MANAGED} ${EXTERNALLY_MANAGED}.old     # Bookworm
    fi 
    sudo apt-get -y install libtiff5-dev | tee -a ${LOG}   # Bookworm or later
elif [[ $(release_id) -le 11 ]]; then
    # Bullseye
    sudo apt-get -y install libtiff5 | tee -a ${LOG}      # Bullseye
fi

sudo apt-get -y install python3-pip | tee -a ${LOG}
sudo apt-get -y install python3 python3-pil libjpeg-dev zlib1g-dev | tee -a ${LOG}
sudo apt-get -y install libfreetype6-dev liblcms2-dev libopenjp2-7 | tee -a ${LOG}
sudo -H pip3 install --upgrade luma.oled | tee -a ${LOG}
sudo pip3 install pathlib | tee -a ${LOG}
sudo pip3 install luma.core | tee -a ${LOG}

# Restor Pip virtual environment
if [[ $(release_id) -ge 12 ]] && [[ -f  ${EXTERNALLY_MANAGED}.old ]]; then
    sudo mv ${EXTERNALLY_MANAGED}.old ${EXTERNALLY_MANAGED}
fi

echo "A log of these changes has been written to ${LOG}"
# End of script

# set tabstop=4 shiftwidth=4 expandtab
# retab
