#!/bin/bash
# set -x
# Raspberry Pi Internet Radio Web Interface
# $Id: edit_files.sh,v 1.2 2024/11/25 10:16:08 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This menu is used to edit the MPD and radio software configuration files
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.

DIR=/usr/share/radio
OS_RELEASE=/etc/os-release
RADIOLIB=/var/lib/radiod
USER=$(logname)
GRP=$(id -g -n ${USER})

# Configuration files
RADIO_CONF=/etc/radiod.conf
MPD_CONF=/etc/mpd.conf
STATION_LIST=/var/lib/radiod/stationlist
ALSA_CONF=/etc/asound.conf
BOOTCONFIG=/boot/config.txt
BOOTCONFIG_2=/boot/firmware/config.txt

# Text editors 
VI=/usr/bin/vi
NANO=/usr/bin/nano
EMACS=/usr/bin/emacs
EDITOR=${NANO}    # Default

# Check that radio software has been installed 
if [[ ! -d ${DIR} ]];then
    echo "Fatal error: radiod package not installed!"
    exit 1
fi

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


# Releases before Bullseye not supported
if [[ $(release_id) -lt 11 ]]; then
    echo "This program is only supported on Raspbian Bullseye/Bookworm or later!"
    echo "This system is running $(codename) OS"
    echo "Exiting program." | tee -a ${LOG}
    exit 1
fi

# In Bookworm (Release ID 12) the configuration has been moved to /boot/firmware/config.txt
if [[ $(release_id) -ge 12 ]]; then
    BOOTCONFIG=${BOOTCONFIG_2}
fi

# Get editor if set
if [[ -f ${RADIOLIB}/editor ]]; then
    EDITOR=$(cat ${RADIOLIB}/editor)
fi

run=1
while [ ${run} -eq 1 ]
do
    selection=1
    FILE=""
    SELECT_EDITOR=0
    while [ $selection != 0 ]
    do
        ans=$(whiptail --title "Edit configuration files" --menu "Choose file" 18 75 12 \
        "1" "Edit Radio configuration (/etc/radiod.conf)" \
        "2" "Edit Music Player Daemon Configuration (/etc/mpd.conf)" \
        "3" "Edit Radio station list (/var/lib/radiod/stationlist)" \
        "4" "Edit ALSA sound configuration (/etc/asound.conf)" \
        "5" "Edit boot configuration (config.txt)" \
        "6" "Select file editor (vi, nano or emacs)" 3>&1 1>&2 2>&3)

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            exit 0
        fi

        if [[ ${ans} == '1' ]]; then
            DESC="Edit ${RADIO_CONF}"    
            FILE=${RADIO_CONF}
        fi

        if [[ ${ans} == '2' ]]; then
            DESC="Edit ${MPD_CONF}"    
            FILE=${MPD_CONF}
        fi

        if [[ ${ans} == '3' ]]; then
            DESC="Edit ${STATION_LIST}"    
            FILE=${STATION_LIST}
        fi

        if [[ ${ans} == '4' ]]; then
            DESC="Edit ${ALSA_CONF}"    
            FILE=${ALSA_CONF}
        fi

        if [[ ${ans} == '5' ]]; then
            DESC="Edit ${BOOTCONFIG}"    
            FILE=${BOOTCONFIG}
        fi

        if [[ ${ans} == '6' ]]; then
            DESC="Select text editor"    
            SELECT_EDITOR=1
            FILE=""
        fi

        whiptail --title "$DESC selected" --yesno "Is this correct?" 10 60
        selection=$?
        
    done

    if [[ ${FILE} != "" ]]; then
        sudo ${EDITOR} ${FILE}
    fi

    if [[ ${SELECT_EDITOR} -eq 1 ]]; then 
        selection=1
        while [ $selection != 0 ]
        do
            ans=$(whiptail --title "Select text editor" --menu "Choose editor" 18 75 12 \
            "1" "Nano (default)" \
            "2" "Vi professional editor" \
            "3" "Emacs" 3>&1 1>&2 2>&3)

            exitstatus=$?
            if [[ $exitstatus != 0 ]]; then
                exit 0
            fi

            if [[ ${ans} == '1' ]]; then
                DESC="Nano text editor"    
                EDITOR=${NANO}
            fi

            if [[ ${ans} == '2' ]]; then
                DESC="Vi text editor"    
                EDITOR=${VI}
            fi

            if [[ ${ans} == '3' ]]; then
                DESC="Emacs text editor"    
                EDITOR=${EMACS}
            fi
            whiptail --title "$DESC selected" --yesno "Is this correct?" 10 60
            selection=$?

        done
        if [[ -f ${EDITOR} ]]; then
            echo "Editor ${EDITOR} selected"
            echo ${EDITOR} > ${RADIOLIB}/editor 
        else
            echo "Editor ${EDITOR} not installed"
            if [[ ${EDITOR} == ${EMACS} ]]; then
                echo "Only install emacs if you know how to use it"
                echo -n "Do you want to install emacs y/n: "
                read ans
                if [[ ${ans} == "y" ]]; then
                    sudo apt-get -y install emacs
                fi
            else
                echo "Choose another editor"
            fi
        fi
            
        echo -n "Enter to continue: "
        read ans  
    fi
    
done

