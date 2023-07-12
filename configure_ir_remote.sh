#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: configure_ir_remote.sh,v 1.21 2023/07/07 08:01:27 bob Exp $
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
RADIO_DIR=/usr/share/radio
LOGDIR=${RADIO_DIR}/logs
LOG=${LOGDIR}/install_ir.log
CONFIG=/etc/radiod.conf
BOOTCONFIG=/boot/config.txt
LIRC_ETC=/etc/lirc
LIRC_OPTIONS=${LIRC_ETC}/lirc_options.conf
LIRCD_CONFIG=${LIRC_ETC}/lircd.conf
SYSTEMD_DIR=/usr/lib/systemd/system
CONFIG_DIR=${LIRC_ETC}/lircd.conf.d 
RC_MAPS=/etc/rc_keymaps
KEYMAPS_TOML=/lib/udev/rc_keymaps 
KEYMAPS=/etc/rc_keymaps
ERRORS=(0)

IR_GPIO=9   
DT_OVERLAY=""
REMOTE_LED=0

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

OSNAME=$(osname)
REL_ID=$(release_id)
if [[ ${REL_ID} -lt 10 ]]; then
    echo "Release ${REL_ID} ${OSNAME} not supported by the IR software "
    echo "Exiting setup"
    exit 1
fi

sudo rm -f ${LOG}
mkdir -p ${LOGDIR}
echo "$0 configuration log, $(date) " | tee ${LOG}

# Check if user wants to configure IR remote control 
if [[ -f ${CONFIG}.org ]]; then
        ans=0
        ans=$(whiptail --title "Configure IR Remote Control?" --menu "Choose your option" 15 75 9 \
        "1" "Run IR Remote Control configuration?" \
        "2" "Do not change configuration?" 3>&1 1>&2 2>&3)

        exitstatus=$?
        if [[ $exitstatus != 0 ]] || [[ ${ans} == '2' ]]; then
                echo "Current IR remote control configuration unchanged" | tee -a ${LOG}
                exit 0
        fi
fi

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

    elif [[ ${ans} == '4' ]]; then
        DESC="No remote activity LED"
        REMOTE_LED=0    
    fi

    whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
    selection=$?
done

# Interface type LIRC or Kernel Event
KERNEL_EVENT=1
LIRC=2
INTERFACE=${KERNEL_EVENT}
selection=1
while [ $selection != 0 ]
do
    ans=$(whiptail --title "Select Interface type LIRC or Kernel Event " --menu "Choose your option" 15 75 9 \
    "1" "Kernel event configured with ir-keytable (Default)" \
    "2" "LIRC daemon configured using irrecord (Legacy only)" \
    "3" "Unsure? - Let system use defaults" \
    3>&1 1>&2 2>&3)

    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
            exit 0
    fi

    if [[ ${ans} == '1' ]]; then
        DESC="Default GPIO 11 selected"
        INTERFACE=${KERNEL_EVENT}

    elif [[ ${ans} == '2' ]]; then
        DESC="Use LIRC daemon to detect IR events"
        INTERFACE=${LIRC}

    elif [[ ${ans} == '3' ]]; then
        DESC="Use Kernel Events (ev_dev) for IR detection"
        INTERFACE=${KERNEL_EVENT}
    fi

    whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
    selection=$?
done

# Display configuration changes
echo "Selected GPIO is ${IR_GPIO}" | tee -a ${LOG}
echo "Remote activity LED is GPIO ${REMOTE_LED}" | tee -a ${LOG}
echo "" | tee -a ${LOG}

# Commit changes 

# Delete any old IR overlays
sudo sed -i -e /^dtoverlay=gpio-ir/d ${BOOTCONFIG}
sudo sed -i -e /^dtoverlay=lirc-rpi/d ${BOOTCONFIG}
sudo sed -i -e /^dtoverlay=gpio-ir/d ${BOOTCONFIG}

# Write the new one to /boot/config.txt
sudo sed -i -e "$ a ${DT_OVERLAY}" ${BOOTCONFIG}
echo "Added following line to ${BOOTCONFIG}:" | tee -a ${LOG}
echo ${DT_OVERLAY} | tee -a ${LOG}

# Load Device Tree overlay
echo ${DT_COMMAND} | tee -a ${LOG}
${DT_COMMAND}
if [[ $? -ne '0' ]]; then       # Do not seperate from above
    # The overlay may be already loaded
    echo "Warning: Failed to run ${DT_COMMAND}" | tee -a ${LOG}
fi
echo "" | tee -a ${LOG}

# Configure the remote LED
sudo sed -i -e "0,/^remote_led/{s/remote_led.*/remote_led=${REMOTE_LED}/}" ${CONFIG}
echo "Configured remote_led=${REMOTE_LED} in ${CONFIG}" | tee -a ${LOG}

# Install LIRC packages

packages="lirc ir-keytable lirc-compat-remotes python3-evdev "
# evtest ?

for package in ${packages}
do
    echo "Installing ${package}"  | tee -a ${LOG}
    sudo apt -y install ${package}
    if [[ $? -ne '0' ]]; then       # Do not seperate from above
        if [[  ${package} == "lirc" || ${package} == "lircd" ]]; then
            echo "Setting up ${package}" | tee -a ${LOG}
            
        else
            echo "Failed to install ${package}" | tee -a ${LOG}
            ERRORS=$(($ERRORS+1))
        fi
    fi
done

# Copy options file 
if [[ -f  ${LIRC_OPTIONS}.dist ]]; then
    CMD="sudo cp ${LIRC_OPTIONS}.dist ${LIRC_OPTIONS}"  
    echo ${CMD} | tee -a ${LOG}
    ${CMD}
    if [[ $? -ne '0' ]]; then       # Do not seperate from above
        echo "Failed to copy ${LIRC_OPTIONS}" | tee -a ${LOG}
        ERRORS=$(($ERRORS+1))
    fi
fi

# Configure driver and device in lirc_options.conf
sudo sed -i -e '/^driver/s/devinput/default/' ${LIRC_OPTIONS}
sudo sed -i -e '/^device/s/auto/\/dev\/lirc0/' ${LIRC_OPTIONS}

# Copy keymaps
echo "" | tee -a ${LOG}
if [[ -f  ${KEYMAPS_TOML}/rc6_mce.toml ]]; then
    CMD="sudo cp ${KEYMAPS_TOML}/rc6_mce.toml ${KEYMAPS}/rc6_mce"
    echo ${CMD} | tee -a ${LOG}
    ${CMD}
    if [[ $? -ne '0' ]]; then       # Do not seperate from above
        echo "Failed to copy keymaps" | tee -a ${LOG}
        ERRORS=$(($ERRORS+1))
    fi
fi

# Copy lircrc (IR remote control button definitions) to /etc/lirc 
CMD="sudo cp ${RADIO_DIR}/lircrc.dist /etc/lirc/lircrc"
echo ${CMD} | tee -a ${LOG}
${CMD}
if [[ $? -ne '0' ]]; then       # Do not seperate from above
    echo "Failed to copy ${RADIO_DIR}/lircrc.dist to /etc/lirc" | tee -a ${LOG}
    ERRORS=${ERRORS}+1
fi

# Disable devinput.lircd.conf
DEVINPUT=${CONFIG_DIR}/devinput.lircd.conf
if [[ -f ${DEVINPUT} ]]; then
    CMD="sudo mv ${DEVINPUT} ${DEVINPUT}.dist"
    echo ${CMD} | tee -a ${LOG}
    ${CMD}
    if [[ $? -ne '0' ]]; then       # Do not seperate from above
        echo "Warning: failed to disable ${CONFIG_DIR}/devinput.lircd.conf" | tee -a ${LOG}
        exit 1
    fi
fi

# The service definition is copied to /usr/lib/systemd/system/irradiod.service

echo "Setting up irradiod.service for ${OSNAME}" | tee -a ${LOG}
if [[ ${REL_ID} < 11 ]]; then 
    CMD="sudo cp ${RADIO_DIR}/irradiod.service.buster ${SYSTEMD_DIR}/irradiod.service"
else
    CMD="sudo cp ${RADIO_DIR}/irradiod.service.bullseye ${SYSTEMD_DIR}/irradiod.service"
fi
echo ${CMD} | tee -a ${LOG}
${CMD}

# Make configuration file readable to all
sudo chmod og+r ${LIRCD_CONFIG}

if [[ ${ERRORS} > 0 ]]; then
    echo "There were ${ERRORS} errors" | tee -a ${LOG}
fi

# Enable correct service
if [[ ${INTERFACE} == ${KERNEL_EVENT} ]]; then
    echo "Enabling Kernel Events ireventd.service" |  tee -a ${LOG}
    CMD="sudo systemctl enable ireventd.service" 
    echo ${CMD} | tee -a ${LOG}
    ${CMD}
    CMD="sudo systemctl disable irradiod.service" 
    echo ${CMD} | tee -a ${LOG}
    ${CMD}
else
    echo "Enabling LIRC irradiod.service" |  tee -a ${LOG}
    CMD="sudo systemctl enable irradiod.service" 
    echo ${CMD} | tee -a ${LOG}
    ${CMD}
    CMD="sudo systemctl disable ireventd.service" 
    echo ${CMD} | tee -a ${LOG}
    ${CMD}
fi

# Print configuration instructions for either Kernel events or LIRC interface
echo "" |  tee -a ${LOG}
if [[ ${INTERFACE} == ${KERNEL_EVENT} ]]; then
    echo "Configuration of Kernel Event completed OK" |  tee -a ${LOG}
    echo "Reboot the system and then run the following " |  tee -a ${LOG}
    echo "to configure your IR remote control" |  tee -a ${LOG}
    echo "    sudo ir-keytable -v -t -p  rc-5,rc-5-sz,jvc,sony,nec,sanyo,mce_kbd,rc-6,sharp,xmpir-keytable" |  tee -a ${LOG}
    echo "" |  tee -a ${LOG}
    echo "Create myremote.toml using the scan codes from the ir-keytable program output" |  tee -a ${LOG}
    echo "See the example in ${RADIO_DIR}/myremote.mytoml"  |  tee -a ${LOG}
    echo "Then copy your configuration file (myremote.toml) to  ${RC_MAPS}" |  tee -a ${LOG}
    echo "    sudo cp myremote.toml ${RC_MAPS}/." |  tee -a ${LOG}
else
    echo "Configuration of LIRC completed OK" |  tee -a ${LOG}
    echo "Reboot the system and then run the following " |  tee -a ${LOG}
    echo "to configure your IR remote control" |  tee -a ${LOG}
    echo "    sudo irrecord -f -d /dev/lirc0 ~/lircd.conf " |  tee -a ${LOG}
    echo "" |  tee -a ${LOG}
    echo "Then copy your configuration file (myremote.conf) to  ${CONFIG_DIR}" |  tee -a ${LOG}
    echo "    sudo cp myremote.conf ${CONFIG_DIR}/." |  tee -a ${LOG}
fi

echo "" |  tee -a ${LOG}
echo "Reboot the Raspberry Pi " |  tee -a ${LOG}
echo "" |  tee -a ${LOG}
echo "A log of this run will be found in ${LOG}"

exit 0

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab

