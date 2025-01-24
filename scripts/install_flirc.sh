#!/bin/bash
# $Id: install_flirc.sh,v 1.2 2025/01/24 13:55:37 bob Exp $
# Raspberry Pi Internet Radio - Install FLIRC
# This script installs and configures FLIRC remote control software
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
LOG=${LOGDIR}/install_flirc.log

# Install details
echo "$0 configuration log, $(date) " | tee ${LOG}
echo "Using ${DIR}" | tee -a ${LOG}

CMD="sudo sudo apt install libhidapi-hidraw0 libqt5xmlpatterns5"
echo ${CMD} | tee -a ${LOG}
${CMD} | tee -a ${LOG}
curl apt.flirc.tv/install.sh | sudo bash | tee -a ${LOG}

echo | tee -a ${LOG}
echo "FLIRC installation complete" | tee -a ${LOG}
echo "A log of this run will be found in ${LOG}"

echo | tee -a ${LOG}
echo "Reboot the Raspberry pi in Desktop mode (Important)"
echo "On the desktop open Programs -> Accessories -> Flirc"
echo "and follow the instructions in the Radio Constructors Manual"
echo | tee -a ${LOG}
echo -n "Enter to continue: "
read ans

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab

