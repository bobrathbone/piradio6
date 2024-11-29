#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: select_ir_remote.sh,v 1.5 2024/11/28 09:49:27 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used during installation to set up which IR remote control
# definition (<remote_device>.toml) is to be used. It displays a list of the .toml
# files found in /usr/share/radio/remotes amd copies the the selected definition 
# file to the /etc/rc_keymaps directory. It also sets the keytable parameter
# in /etc/radiod.conf, for example keytable=mini.toml. 
# 
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.

DIR=/usr/share/radio
LOGDIR=${DIR}/logs
LOG=${LOGDIR}/install_ir.log
RC_MAPS=/etc/rc_keymaps 
REMOTES_DIR=${DIR}/remotes
CONFIG=/etc/radiod.conf
KEYMAPS=/etc/rc_keymaps
RADIOLIB=/var/lib/radiod
REMOTE_CONTROL=${RADIOLIB}/remote_control

mkdir -p ${LOGDIR}

# Display colours
orange='\033[33m'
default='\033[39m'

# Select remote control definition <file>.toml
num=1
lines=()
names=()
# Build a list of available .toml files
for toml in ${REMOTES_DIR}/*.toml
do
    toml=$(basename $toml)
    names+=($toml)
    lines+=("\"$num\" \"${toml}\"" )
    let "num += 1"
done

# Display toml file selection menu using whiptail
selection=1
while [ $selection != 0 ]
do
    ans=0
    ans=$(whiptail --title "Select IR remote control definition" --menu "Choose file" 15 75 9 \
    ${lines[@]} \
    3>&1 1>&2 2>&3)

    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
        exit 0
    fi

    # Setup toml file name
    idx=$(printf '%d' $ans)
    idx=$((idx-49))
    TOML_FILE=${names[idx]}

    whiptail --title "${TOML_FILE} selected" --yesno "Is this correct?" 10 60
    selection=$?
done

# Log to install_ir.log
echo "Select IR remote control definition" | tee -a  ${LOG}
# Copy selected toml file to /etc/rc_keymaps
CMD="sudo cp -f ${REMOTES_DIR}/${TOML_FILE} ${KEYMAPS}/."
echo ${CMD} | tee -a ${LOG}
${CMD}
CMD="sudo ir-keytable -c -w ${KEYMAPS}/${TOML_FILE}" 
echo ${CMD} | tee -a ${LOG}
${CMD} 

# Copy toml filename to /var/lib/radiod/remote_control to be picked up by configure_ir_remote.sh
sudo echo ${TOML_FILE} > ${REMOTE_CONTROL}

# Configure the keymap parameter with the selected <file>.toml definition
sudo sed -i -e "0,/^keytable/{s/^keytable.*/keytable=${TOML_FILE}/}" ${CONFIG}
echo "Configured keytable=${TOML_FILE} in ${CONFIG}" | tee -a ${LOG}

echo "" 
echo "A log of this script will be found in ${LOG}"
exit 0

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
