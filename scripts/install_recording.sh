#!/bin/bash
# $Id: install_recording.sh,v 1.2 2024/12/11 11:14:40 bob Exp $
#
# Raspberry Pi Internet Radio - Install Streamripper
# This script installs and configures Streamripper recording utility
# See https://streamripper.sourceforge.net/
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.

CONFIG=/etc/radiod.conf

clear
ans=0
selection=1
GPIO=0

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

echo "Installing streamripper recording software"
CMD="sudo apt-get install streamripper"
echo ${CMD}; ${CMD}

echo "Configured record_switch in ${CONFIG}"
grep "^record_switch=" ${CONFIG}

if [[ ${GPIO} < 1 ]]; then
    echo "The record switch parameter in ${CONFIG} has been set to ${GPIO}"
    echo "Configure the record_switch in ${CONFIG} if required" 
fi

echo -n "End of installation. Press enter to continue: "
read x


# End of configuration script

# set tabstop=4 shiftwidth=4 expandtab
# retab

