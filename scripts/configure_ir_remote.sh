#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: configure_ir_remote.sh,v 1.10 2024/11/30 16:34:38 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
# This program uses whiptail. Set putty terminal to use UTF-8 charachter set
# for best results

SCRIPT=$0
OS_RELEASE=/etc/os-release
CONFIG=/etc/radiod.conf
BOOTCONFIG=/boot/config.txt
BOOTCONFIG_2=/boot/firmware/config.txt
SYSTEMD_DIR=/usr/lib/systemd/system
RC_MAPS=/etc/rc_keymaps
UDEV_KEYMAPS=/lib/udev/rc_keymaps 
KEYMAPS=/etc/rc_keymaps
SYS_RC=/sys/class/rc
RADIOLIB=/var/lib/radiod
REMOTE_CONTROL=${RADIOLIB}/remote_control
ERRORS=(0)
LYNX=/usr/bin/lynx
CMARK=/usr/bin/cmark

FLAGS=$1
DIR=/usr/share/radio
LOGDIR=${DIR}/logs
LOG=${LOGDIR}/install_ir.log
DOCS_DIR=${DIR}/docs
REMOTES_DIR=${DIR}/remotes
SCRIPTS_DIR=${DIR}/scripts

IR_GPIO=9   
DT_OVERLAY=""
REMOTE_LED=0

# Display colours
orange='\033[33m'
default='\033[39m'

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
function osname
{
    VERSION_OSNAME=$(grep VERSION_CODENAME $OS_RELEASE)
    arr=(${VERSION_OSNAME//=/ })
    OSNAME=$(echo "${arr[1]}" | tr -d '"')
    echo ${OSNAME}
}

# Returns the device name for the "gpio_ir_recv" overlay (rc0...rc6)
function find_device()
{
    sname=$1
    found=0
    for x in 0 1 2 3 4 6
    do
        for y in 0 1 2 3 4 5 6
        do
            if [[ -f ${SYS_RC}/rc${x}/input${y}/name ]]; then
                name=$(cat ${SYS_RC}/rc${x}/input${y}/name)
                if [[ ${name} == ${sname} ]]; then
                    echo "rc${x}"
                    found=1
                    break
                fi
            fi
        done
        if [[ ${found} == 1 ]]; then
            break
        fi
    done
}

OSNAME=$(osname)
REL_ID=$(release_id)
if [[ ${REL_ID} -lt 10 ]]; then
    echo "Release ${REL_ID} ${OSNAME} not supported by the IR software "
    echo "Exiting setup"
    exit 1
fi

# Install cmark if not yet installed
if [[ ! -f ${CMARK} ]]; then
    sudo apt-get -y install cmark
fi

# Install lynx if not yet installed
if [[ ! -f ${LYNX} ]]; then
    sudo apt-get -y install lynx
fi

config_changed=0

mkdir -p ${LOGDIR}
sudo rm -f ${LOG}

# In Bookworm (Release ID 12) the configuration has been moved to /boot/firmware/config.txt
if [[ $(release_id) -ge 12 ]]; then
    BOOTCONFIG=${BOOTCONFIG_2}
fi

# Check if user wants to configure IR remote control 
run=1
while [ ${run}  == 1 ]
do
    ans=0
    ans=$(whiptail --title "Configure IR Remote Control?" --menu "Choose your option" 15 75 9 \
    "1" "Install and configure IR Remote Control configuration?" \
    "2" "Test remote control (Stops IR event daemon)" \
    "3" "IR Remote Control confguration and status" \
    "4" "Flash IR activity LED" \
    "5" "Start ireventd daemon" \
    "6" "Stop ireventd daemon" \
    "7" "IR event daemon (ireventd) status" \
    "8" "Create an IR remote control definition" \
    "9" "Select IR remote control definition" \
    3>&1 1>&2 2>&3)

    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
        if [[ ${config_changed} == 1 ]]; then
            echo "Warning: IR remote control configuration  has been changed!" 
        else
            echo "Current IR remote control configuration unchanged" 
        fi
        echo "A log of this run will be found in ${LOG}"
        exit 0
    fi

    if [[ ${ans} == '1' ]]; then
        CONFIGURE=1
        run=0

    elif [[ ${ans} == '2' ]]; then
        clear
        sudo systemctl stop ireventd.service
        echo
        echo "Press Ctl-C to end test"
        ${DIR}/test_events.py 
        echo

    elif [[ ${ans} == '3' ]]; then
        clear
        sudo ${DIR}/ireventd.py config
        sudo ${DIR}/ireventd.py status

        echo
        echo "${CONFIG} parameters"
        echo "---------------------------"
        grep "^keytable" ${CONFIG}
        if [[ $? != 0 ]]; then
            echo "Error: keytable not specified in ${CONFIG}"
        fi
        grep "^remote_led" ${CONFIG}
        echo
        echo -n "Press enter to continue: "
        read x

    elif [[ ${ans} == '4' ]]; then
        sudo ${DIR}/ireventd.py flash

    elif [[ ${ans} == '5' ]]; then
        clear
        sudo systemctl start ireventd.service
        sudo ${DIR}/ireventd.py status
        echo -n "Press enter to continue: "
        read x

    elif [[ ${ans} == '6' ]]; then
        clear
        sudo systemctl stop ireventd.service
        sudo ${DIR}/ireventd.py status
        echo -n "Press enter to continue: "
        read x

    elif [[ ${ans} == '7' ]]; then
        clear
        echo "Press Ctl-C to exit status screen"
        sudo systemctl status ireventd.service

    elif [[ ${ans} == '8' ]]; then
        clear
        ${DIR}/create_keymap.py
        echo -n "Press enter to continue: "
        read x
        
    elif [[ ${ans} == '9' ]]; then
        clear
        ${SCRIPTS_DIR}/select_ir_remote.sh ${FLAGS}
        echo "Reboot the Raspberry Pi or run the following command:"
        printf "${orange}sudo systemctl restart ireventd radiod${default}"
        echo ''
        echo -n "Press enter to continue: "
        read x
        
    elif [[ ${ans} == '10' ]]; then
        DOC="${DOCS_DIR}/create_ir_remote"
        MD_DOC=${DOC}.md
        if [[ -f ${MD_DOC} ]]; then
            HTML_DOC=${DOC}.html
            ${CMARK} ${MD_DOC} > ${HTML_DOC}
            ${LYNX} ${HTML_DOC}
        else
            echo "Error: Document ${MD_DOC} not found"
            echo -n "Press enter to continue: "
            read x
            exit 1
        fi
    fi
done

# Select the IR sensor GPIO 
ans=0
selection=1
while [ $selection != 0 ]
do
    ans=$(whiptail --title "Select IR sensor GPIO configuration" --menu "Choose your option" 15 75 9 \
    "1" "Directly connected LCD - No DAC (GPIO 9 pin 21)" \
    "2" "Directly connected LCD with a USB DAC (GPIO 9 pin 21)" \
    "3" "LCD with I2C backpack - No DAC (GPIO 9 pin 21)" \
    "4" "Adafruit RGB plate (GPIO 16)" \
    "5" "All versions using a DAC (GPIO 25)" \
    "6" "IQaudIO Cosmic Controller (GPIO 25)" \
    "7" "PiFace CAD (GPIO 23)" \
    3>&1 1>&2 2>&3)

    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
            exit 0
    fi

    if [[ ${ans} == '1' ]]; then
        DESC="Directly connected LCD - No DAC (GPIO 9 pin 21)"
        IR_GPIO=9   

    elif [[ ${ans} == '2' ]]; then
        DESC="Directly connected LCD with a USB DAC (GPIO 9 pin 21)"
        IR_GPIO=9   

    elif [[ ${ans} == '3' ]]; then
        DESC="LCD with I2C backpack - No DAC (GPIO 9)"
        IR_GPIO=9   

    elif [[ ${ans} == '4' ]]; then
        DESC="Adafruit RGB plate (GPIO 16)"
        IR_GPIO=16  

    elif [[ ${ans} == '5' ]]; then
        DESC="All 40 pin versions using a DAC (GPIO 25)"
        IR_GPIO=25  

    elif [[ ${ans} == '6' ]]; then
        DESC="IQaudIO Cosmic Controller (GPIO 25)"
        IR_GPIO=25  

    elif [[ ${ans} == '7' ]]; then
        DESC="Piface CAD (GPIO 23)"
        IR_GPIO=23  
    fi

    whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
    selection=$?
done

# OS is Raspbian Buster or later
DT_OVERLAY="dtoverlay=gpio-ir,gpio_pin=${IR_GPIO}"
DT_COMMAND="sudo dtoverlay gpio-ir gpio_pin=${IR_GPIO}"

# Configure remote activity LED
ans=0
selection=1
while [ $selection != 0 ]
do
    ans=$(whiptail --title "Configure remote activity LED" --menu "Choose your option" 15 75 9 \
    "1" "Default GPIO 11 (pin 23) or 26-pin GPIO header" \
    "2" "All 40-pin designs using DAC sound card GPIO 16 (pin 36)" \
    "3" "Adafruit plate  GPIO 13 (pin 33)" \
    "4" "IQaudIO Cosmic Controller GPIO 14 (pin 8)" \
    "5" "No remote activity LED or manually configure" \
    3>&1 1>&2 2>&3)

    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
            exit 0
    fi

    if [[ ${ans} == '1' ]]; then
        DESC="Default GPIO 11 selected"
        REMOTE_LED=11   

    elif [[ ${ans} == '2' ]]; then
        DESC="All designs using DAC sound cards, GPIO 16 (pin 36)"
        REMOTE_LED=16   

    elif [[ ${ans} == '3' ]]; then
        DESC="Adafruit plate/PiFace CAD, GPIO 13 (pin 33)"
        REMOTE_LED=13   

    elif [[ ${ans} == '4' ]]; then
        DESC="IQaudIO Cosmic controller, GPIO 14 (pin 8)"
        REMOTE_LED=14   

    elif [[ ${ans} == '5' ]]; then
        DESC="No remote activity LED"
        REMOTE_LED=0    
    fi

    whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
    selection=$?
done

# Select the IR remote control definition (toml file)
${SCRIPTS_DIR}/select_ir_remote.sh  
TOML_FILE=$(cat ${REMOTE_CONTROL})

# Display configuration changes
config_changed=1
echo "$0 configuration log, $(date) " | tee ${LOG}
echo "Boot configuration in ${BOOTCONFIG}" | tee -a ${LOG}
echo "Selected GPIO${IR_GPIO} for the IR sensor" | tee -a ${LOG}
echo "Remote activity LED is GPIO ${REMOTE_LED}" | tee -a ${LOG}
echo "Remote control definition ${TOML_FILE} selected" | tee -a ${LOG}
echo "" | tee -a ${LOG}

# Commit changes 

# Delete any old IR overlays (especially lirc-rpi)
sudo sed -i -e /^dtoverlay=gpio-ir/d ${BOOTCONFIG}
sudo sed -i -e /^dtoverlay=lirc-rpi/d ${BOOTCONFIG}

# Write the new one to /boot/config.txt
sudo sed -i -e "$ a ${DT_OVERLAY}" ${BOOTCONFIG}
echo "Added the following line to ${BOOTCONFIG}:" | tee -a ${LOG}
echo ${DT_OVERLAY} | tee -a ${LOG}

# Configure the remote LED
sudo sed -i -e "0,/^remote_led/{s/remote_led.*/remote_led=${REMOTE_LED}/}" ${CONFIG}
echo "Configured remote_led=${REMOTE_LED} in ${CONFIG}" | tee -a ${LOG}

# Find device name for the "gpio_ir_recv" overlay
IR_DEV=$(find_device "gpio_ir_recv")

# Copy keymaps to /etc/rc_keymaps
echo "" | tee -a ${LOG}
if [[ -f  ${UDEV_KEYMAPS}/rc6_mce.toml ]]; then
    CMD="sudo cp -f ${UDEV_KEYMAPS}/rc6_mce.toml ${KEYMAPS}/."
    echo ${CMD} | tee -a ${LOG}
    ${CMD}
    if [[ $? -ne '0' ]]; then       # Do not seperate from above
        echo "Failed to copy ${UDEV_KEYMAPS}/rc6_mce.toml to ${KEYMAPS}" | tee -a ${LOG}
        ERRORS=$(($ERRORS+1))
    fi
fi

echo "" | tee -a ${LOG}
# Install evdev
PKGS="ir-keytable python3-evdev evtest"
CMD="sudo apt-get -y install ${PKGS}"
echo ${CMD} | tee -a ${LOG}
${CMD}
if [[ $? -ne '0' ]]; then       # Do not seperate from above
    echo "Failed to install ${PKGS}" | tee -a ${LOG}
    ERRORS=$(($ERRORS+1))
else
    CMD="sudo apt -y autoremove"
    echo ${CMD} | tee -a ${LOG}
${CMD}
fi

# Enable ireventd.service service
echo "Enabling Kernel Events ireventd.service" |  tee -a ${LOG}
CMD="sudo systemctl enable ireventd.service" 
echo ${CMD} | tee -a ${LOG}
${CMD}
if [[ $? -ne '0' ]]; then       # Do not seperate from above
    echo "Failed to enable ireventd.service" | tee -a ${LOG}
    ERRORS=$(($ERRORS+1))
fi
echo "" |  tee -a ${LOG}

if [[ ${ERRORS} > 0 ]]; then
    echo "ERROR: There was ${ERRORS} error(s)" | tee -a ${LOG}
    echo "Configuration of Kernel Events FAILED" |  tee -a ${LOG}
else
    echo "Configuration of Kernel Events completed OK" | tee -a ${LOG}
    echo "" |  tee -a ${LOG}
    echo "Reboot the Raspberry Pi or run the following command:"
    printf "${orange}sudo systemctl restart ireventd radiod${default}"
    echo "" |  tee -a ${LOG}
    echo "" |  tee -a ${LOG}
fi
echo "A log of this run will be found in ${LOG}"

exit 0

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab

