#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: configure_bluetooth.sh,v 1.2 2024/11/25 10:16:08 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used during installation to set up Bluetooth device with
# with MPD and the radio daemon 
# See https://sigmdel.ca/michel/ha/rpi/bluetooth_in_rpios_02_en.html#pulseaudio
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#
# This program uses whiptail. Set putty terminal to use UTF-8 charachter set
# for best results
# Warning: whiptail overwrites the LINES variable previously used in this script. Use DLINES

FLAGS=$1

DIR=/usr/share/radio
LOGDIR=${DIR}/logs
LOG=${LOGDIR}/bluetooth.log
BLUETOOTH_SERVICE=/lib/systemd/system/bluetooth.service
TEMPFILE=/tmp/output$$

# Test mode, use current directory
if [[ ${FLAGS} == "-t" ]]; then
    DIR=$(pwd)
fi

DOCS_DIR=${DIR}/docs
DOC=""
LYNX=/usr/bin/lynx
CMARK=/usr/bin/cmark
OS_RELEASE=/etc/os-release
ASOUND_CONF=/etc/asound.conf
ASOUND_CONF_DIST=${DIR}/asound/asound.conf.dist.blue
CONFIG=/etc/radiod.conf
MPDCONFIG=/etc/mpd.conf
AUDIO_INTERFACE="pulse"
BOOTCONFIG=/boot/config.txt
BOOTCONFIG_2=/boot/firmware/config.txt
USR=$(logname)
BT_DEVICE=""
PA_PLAY=/usr/bin/paplay
#WAV=/usr/share/sounds/alsa/Front_Center.wav
WAV=${DIR}/asound/piano.wav
APLAY="aplay -q -D bluealsa:SRV=org.bluealsa,PROFILE=a2dp,DEV="



# Get OS release ID
function release_id
{
    VERSION_ID=$(grep VERSION_ID $OS_RELEASE)
    arr=(${VERSION_ID//=/ })
    ID=$(echo "${arr[1]}" | tr -d '"')
    ID=$(expr ${ID} + 0)
    echo ${ID}
}

# End of run message
function exit_message
{
    echo "A log of this run will be found in ${LOG}"
}

# Install cmark if not yet installed
if [[ ! -f ${CMARK} ]]; then
    sudo apt-get -y install cmark
fi

# Install lynx if not yet installed
if [[ ! -f ${LYNX} ]]; then
    sudo apt-get -y install lynx
fi

# In Bookworm (Release ID 12) the configuration has been moved to /boot/firmware/config.txt
if [[ $(release_id) -ge 12 ]]; then
    BOOTCONFIG=${BOOTCONFIG_2}
fi

if [[ $(release_id) -lt 12 ]]; then
    PAIRED=$(bluetoothctl paired-devices)
else
    PAIRED=$(bluetoothctl devices)
fi

loop=1
while [ ${loop} == 1 ]
do
    INSTALL_BLUETOOTH=0
    BLUETOOTH_SHELL=0
    PAIRING_DOC=0
    STATUS=0
    PAPLAY=0
    ALSA_PLAY=0

    run=1
    while [ ${run} == 1 ]
    do
        ans=0

        ans=$(whiptail --title "Upgrading, Re-configure radio?" --menu "Choose your option" 15 75 9 \
        "1" "Install Bluetooth software (Do this first!)" \
        "2" "Tutorial - How to pair a Bluetooth device" \
        "3" "Run Bluetooth shell (bluetoothctl) " \
        "4" "Configure Radio to use Bluetooth device" \
        "5" "Bluetooth device status" \
        "6" "Play a sound with paplay" \
        "7" "Play a sound with Alsa aplay" \
        "8" "Exit" 3>&1 1>&2 2>&3)

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            exit 0

        elif [[ ${ans} == '1' ]]; then
            INSTALL_BLUETOOTH=1
            DESC="Install Bluetooth software"

        elif [[ ${ans} == '2' ]]; then
            PAIRING_DOC=1
            DESC="Pairing a Bluetooth device"

        elif [[ ${ans} == '3' ]]; then
            BLUETOOTH_SHELL=1
            DESC="Run Bluetooth shell"

        elif [[ ${ans} == '4' ]]; then
            USE_BLUETOOTH=1
            DESC="Configure Radio"

        elif [[ ${ans} == '5' ]]; then
            STATUS=1 
            DESC="Status"

        elif [[ ${ans} == '6' ]]; then
            PAPLAY=1 
            DESC="Play sound"

        elif [[ ${ans} == '7' ]]; then
            ALSA_PLAY=1 
            DESC="Play sound"

        elif [[ ${ans} == '8' ]]; then
            exit_message
            exit 0
        fi
        run=0

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
    done

    # Install Bluetooth software
    if [[ ${INSTALL_BLUETOOTH} == 1 ]]; then
        echo "$0 Bluetooth configuration log, $(date) " | tee ${LOG}
        echo "Boot configuration in ${BOOTCONFIG}" | tee ${LOG}
        echo "Removing pipewire package" | tee -a ${LOG}
        CMD="sudo apt -y remove pipewire"
        echo ${CMD} | tee -a ${LOG}
        ${CMD}

        echo "Installing Bluetooth packages" | tee -a ${LOG}
        PKGS="install pulseaudio pulseaudio-module-bluetooth "
    
        if [[ $(release_id) -ge 12 ]]; then
            PKGS=${PKGS}" bluez-alsa-utils"
        fi

        for PKG in ${PKGS} 
        do
            CMD="sudo apt-get -y install ${PKG}"
            echo ${CMD} | tee -a ${LOG}
            ${CMD}
        done

        CMD="sudo apt -y autoremove"
        echo ${CMD} | tee -a ${LOG}
        ${CMD}

        CMD="sudo usermod -G bluetooth -a ${USR}"
        echo ${CMD} | tee -a ${LOG}
        ${CMD}

        echo "Bluetooth software installation complete" | tee -a ${LOG}

    elif [[ ${BLUETOOTH_SHELL} == 1 ]]; then
        echo "Run Bluetooth shell (bluetoothctl)"     
        bluetoothctl

    elif [[ ${PAIRING_DOC} == 1 ]]; then
        DOC="${DOCS_DIR}/pair_bluetooth_device"
        MD_DOC=${DOC}.md
        HTML_DOC=${DOC}.html
        echo "${LYNX} ${HTML_DOC}"

        # Create and display requested html document
        if [[ -f ${MD_DOC} ]]; then
            ${CMARK} ${MD_DOC} > ${HTML_DOC}
            ${LYNX} ${HTML_DOC}
        fi

    elif [[ ${USE_BLUETOOTH} == 1 ]]; then
        echo "$0 Bluetooth configuration log, $(date) " | tee ${LOG}
        echo ${PAIRED} |  tee -a ${LOG}
        BT_NAME=$(echo ${PAIRED} | awk '{print $3}')
        BT_DEVICE=$( echo ${PAIRED} | awk '{print $2}')

        if [[  ${BT_DEVICE} != '' ]];then
            echo "Paired ${BT_DEVICE} found" | tee -a ${LOG}

            # Disable Sap initialisation in bluetooth.service
            grep "noplugin=sap" ${BLUETOOTH_SERVICE}
            if [[ $? != 0 ]]; then  # Do not separate from above
                echo "Disabling Sap driver in  ${BLUETOOTH_SERVICE}" | tee -a ${LOG}
                sudo sed -i -e 's/^ExecStart.*/& --plugin=a2dp --noplugin=sap/' ${BLUETOOTH_SERVICE} | tee -a ${LOG}
            fi
            DEVICE="bluetooth"
            cmd="bluetoothctl trust ${BT_DEVICE}"
            echo $cmd | tee -a ${LOG}
            $cmd | tee -a ${LOG}
            cmd="bluetoothctl connect ${BT_DEVICE}"
            echo $cmd | tee -a ${LOG}
            $cmd | tee -a ${LOG}
            cmd="bluetoothctl discoverable on"
            echo $cmd | tee -a ${LOG}
            $cmd | tee -a ${LOG}
            cmd="bluetoothctl info ${BT_DEVICE}"
            echo $cmd | tee -a ${LOG}
            $cmd | tee -a ${LOG}

            # Configure bluetooth device in /etc/radiod.conf
            sudo sed -i -e "0,/^bluetooth_device/{s/bluetooth_device.*/bluetooth_device=${BT_DEVICE}/}" ${CONFIG}
            if [[ ! -f ${ASOUND_CONF}.org && -f ${ASOUND_CONF} ]]; then
                echo "Saving ${ASOUND_CONF} to ${ASOUND_CONF}.org" | tee -a ${LOG}
                sudo cp -f ${ASOUND_CONF} ${ASOUND_CONF}.org
            fi

            echo "Copying ${ASOUND_CONF_DIST} to  ${ASOUND_CONF}" | tee -a ${LOG}
            sudo cp ${ASOUND_CONF_DIST} ${ASOUND_CONF}
        
            # Configure /etc/mpd.conf 
            sudo sed -i -e "0,/^\sname/{s/\sname.*/\tname\t\t\"${BT_NAME}\"/}" ${MPDCONFIG}
            sudo sed -i -e "0,/^\stype/{s/\stype.*/\ttype\t\t\"alsa\"/}" ${MPDCONFIG}
            sudo sed -i -e "0,/^#\sdevice\s/{s/^#\sdevice/\tdevice/}" ${MPDCONFIG}
            sudo sed -i -e "0,/^\sdevice\s/{s/^\sdevice.*/\tdevice\t\t\"bluealsa\"/}" ${MPDCONFIG}

            # /etc/asound.conf
            sudo sed -i -e "0,/device <btdevice>/{s/device <btdevice>/device \"${BT_DEVICE}\"/g}" ${ASOUND_CONF}
            sudo sed -i -e "0,/defaults.bluealsa.device <btdevice>/{s/device <btdevice>/device \"${BT_DEVICE}\"/g}" ${ASOUND_CONF}
        
            # config.txt
            sudo sed -i 's/^dtparam=audio=.*$/dtparam=audio=off/g'  ${BOOTCONFIG}
            echo | tee -a ${LOG}

            # /etc/radiod.conf
            echo "Configuring audio_out parameter in ${CONFIG}" | tee -a ${LOG}
            #sudo sed -i -e "0,/audio_out=/{s/^#aud/aud/}" ${CONFIG}
            sudo sed -i -e "0,/^audio_out=/{s/^audio_out=.*/audio_out=\"bluetooth\"/}" ${CONFIG}
            grep -i "audio_out="  ${CONFIG} | tee -a ${LOG}
            exit_message
        else 
            echo "Error: No paired bluetooth devices found" | tee -a ${LOG}
            echo "First check that you have installed the Bluetooth software" 
            echo "Then run Bluetooth Shell and scan and pair a device" 
            echo "See Tutorial - How to pair a Bluetooth device for help"
            echo -n "Enter to continue: "
            read x
        fi

    elif [[ ${STATUS} == 1 ]]; then
        BT_NAME=$(echo ${PAIRED} | awk '{print $3}')
        BT_DEVICE=$( echo ${PAIRED} | awk '{print $2}')

        if [[ ${BT_DEVICE} != "" ]]; then
            TITLE="Status Bluetooth Device ${BT_NAME} ${BT_DEVICE}"
            # Create .md file, convert to HTML and display with lynx
            echo ${TITLE} > ${TEMPFILE}.md
            echo "=====" >> ${TEMPFILE}.md
            echo '```' >> ${TEMPFILE}.md
            bluetoothctl info ${BT_DEVICE} >> ${TEMPFILE}.md
            echo '```' >> ${TEMPFILE}.md

            echo "Bluealsa devices list" >> ${TEMPFILE}.md
            echo "=====================" >> ${TEMPFILE}.md
            echo '```' >> ${TEMPFILE}.md
            bluealsa-aplay -l >> ${TEMPFILE}.md
            echo '```' >> ${TEMPFILE}.md

            ${CMARK} ${TEMPFILE}.md > ${TEMPFILE}.html
            ${LYNX}  ${TEMPFILE}.html
            rm -f ${TEMPFILE}.*
        else
            echo "No paired devices found" | tee -a ${LOG}
            echo "First pair a Bluetooth audio device" | tee -a ${LOG}
            echo -n "Press enter to continue: " 
            read x
        fi

    elif [[ ${PAPLAY} == 1 ]]; then
        bluetoothctl power on
        echo  ${PAPLAY} -v ${WAV}
        ${PA_PLAY} -v ${WAV}
        echo -n "Press enter to continue: " 
        read x

    elif [[ ${ALSA_PLAY} == 1 ]]; then
        bluetoothctl power on
        BT_DEVICE=$( echo ${PAIRED} | awk '{print $2}')
        echo ${BT_DEVICE}
        CMD="${APLAY}${BT_DEVICE} ${WAV} >/dev/null 2>&1 "
        echo ${CMD} | tee -a ${LOG}
        ${CMD}
        echo -n "Press enter to continue: " 
        read x
    fi
done

exit_message
exit 0

# set tabstop=4 shiftwidth=4 expandtab
# retab
    
# End of configuration script