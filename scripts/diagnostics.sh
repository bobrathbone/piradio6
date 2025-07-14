#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: diagnostics.sh,v 1.10 2025/07/13 10:40:45 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program provides diagnostics and information about the radio software and OS 
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
# Test flag - change to current directory
if [[ ${FLAGS} == "-t" ]]; then
    DIR=$(pwd)
fi

LOGDIR=${DIR}/logs
NODAEMON_LOG=${DIR}/logs/radiod_nodaemon.log
TEMPFILE=/tmp/output
CMARK="/usr/bin/cmark --hardbreaks"
CMARK_EXE="/usr/bin/cmark"
LYNX=/usr/bin/lynx
SCRIPTS_DIR=${DIR}/scripts
DOCS_DIR=${DIR}/docs
SPEAKER_TEST="speaker-test -t sine -D default -l 1"

function build_report
{
    echo "Please wait - Building report: $1"
}

# Development directory
if [[ ! -d ${DIR} ]];then
    echo "Fatal error: radiod package not installed!"
    exit 1
fi

# Install cmark if not yet installed
if [[ ! -f ${CMARK_EXE} ]]; then
    sudo apt-get -y install cmark
fi

# Install lynx if not yet installed
if [[ ! -f ${LYNX} ]]; then
    sudo apt-get -y install lynx
fi

run=1
while [ ${run} == 1 ]
do
    ans=$(whiptail --title "Select diagnostic" --menu "Choose your option" 15 75 9 \
        "1" "Run the radio in diagnostic mode (nodaemon)" \
        "2" "Test rotary encoders" \
        "3" "Test push buttons" \
        "4" "Test events layer" \
        "5" "Test configured display" \
        "6" "Test GPIOs" \
        "7" "Speaker test (speaker-test)" \
        "8" "Display Radio and OS configuration" 3>&1 1>&2 2>&3)

    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
        exit 0

    elif [[ ${ans} == '1' ]]; then
        sudo systemctl stop radiod.service
        echo "Press Ctrl-C to exit diagnostic mode"
        echo "radiod.py nodaemon diagnostic log, $(date)" | tee  ${NODAEMON_LOG}
        sudo ${DIR}/radiod.py nodaemon 2>&1 | tee -a ${NODAEMON_LOG}
        echo | tee -a ${NODAEMON_LOG}
        echo "A log of this run has been recorded in ${NODAEMON_LOG}"
        echo "A compressed tar file has been saved in ${NODAEMON_LOG}.tar.gz"
        echo "Send ${NODAEMON_LOG}.tar.gz to bob@bobrathbone.com if required"
        echo "Press enter to continue: "
        read -n 1 ans
        exit 0

    elif [[ ${ans} == '2' ]]; then
        sudo systemctl stop radiod.service
        echo "Press Ctrl-C to exit diagnostic mode"
        sudo ${DIR}/rotary_class.py
        exit 0

    elif [[ ${ans} == '3' ]]; then
        sudo systemctl stop radiod.service
        echo "Press Ctrl-C to exit diagnostic mode"
        sudo ${DIR}/button_class.py
        exit 0

    elif [[ ${ans} == '4' ]]; then
        sudo systemctl stop radiod.service
        echo "Press Ctrl-C to exit diagnostic mode"
        sudo ${DIR}/event_class.py
        exit 0

    elif [[ ${ans} == '5' ]]; then
        sudo systemctl stop radiod.service
        echo "Press Ctrl-C to exit diagnostic mode"
        sudo ${DIR}/display_class.py
        exit 0

    elif [[ ${ans} == '6' ]]; then
        sudo systemctl stop radiod.service
        echo "Press Ctrl-C to exit diagnostic mode"
        echo "Test Rotary encoders and buttons "
        sudo ${DIR}/test_gpios.py --pull_up
        exit 0

    elif [[ ${ans} == '7' ]]; then
        sudo systemctl stop radiod.service
        echo "Press Ctrl-Z to exit speaker test (Takes a few seconds to stop)"
        ${SPEAKER_TEST}
        exit 0

    elif [[ ${ans} == '8' ]]; then
        INFO=1
    fi

    run_info=1
    while [ ${run_info} == 1 ]
    do
    if [[ ${INFO} == 1 ]]; then
        ans=$(whiptail --title "Select information to display" --menu "Choose your option" 15 75 9 \
        "1" "Display radio version and build" \
        "2" "Display Operating System details" \
        "3" "Display Raspberry Pi model" \
        "4" "Display wiring" \
        "5" "Display WiFi" \
        "6" "Display full radio configuration" \
        "7" "Display formatted /etc/radiod.conf" \
        "8" "Display current Music Player Daemon output" \
        "9" "Display Audio Configuration" \
         3>&1 1>&2 2>&3)

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            run_info=0

        elif [[ ${ans} == '1' ]]; then
            TITLE="Radio software version"
            ${DIR}/radiod.py version > ${TEMPFILE}
            ${DIR}/radiod.py build >> ${TEMPFILE}

        elif [[ ${ans} == '2' ]]; then
            TITLE="Operating System details"
            build_report "${TITLE}"
            ${SCRIPTS_DIR}/display_os.sh  > ${TEMPFILE}

        elif [[ ${ans} == '3' ]]; then > ${TEMPFILE}
            TITLE="Raspberry Pi model details"
            ${DIR}/display_model.py > ${TEMPFILE}

        elif [[ ${ans} == '4' ]]; then > ${TEMPFILE}
            TITLE="Wiring configuration details"
            build_report "${TITLE}"
            ${DIR}/wiring.py > ${TEMPFILE}

        elif [[ ${ans} == '5' ]]; then
            TITLE="WiFi configuration details"
            build_report "${TITLE}"
            ${SCRIPTS_DIR}/display_wifi.sh > ${TEMPFILE}

        elif [[ ${ans} == '6' ]]; then
            TITLE="Full configuration details"
            build_report "${TITLE}"
            ${SCRIPTS_DIR}/display_config.sh > ${TEMPFILE}

        elif [[ ${ans} == '7' ]]; then
            TITLE="/etc/radiod.conf parameter settings"
            build_report "${TITLE}"
            ${DIR}/config_class.py | tee ${LOGDIR}/radiod_config
            cat ${LOGDIR}/radiod_config > ${TEMPFILE}
            echo
            echo "Formatted /etc/radiod.conf stored in ${LOGDIR}/radiod_config"

        elif [[ ${ans} == '8' ]]; then
            TITLE="Current Music Player Daemom output"
            build_report "${TITLE}"
            ${DIR}/display_current.py > ${TEMPFILE}

        elif [[ ${ans} == '9' ]]; then
            TITLE="Audio configuration"
            build_report "${TITLE}"
            ${SCRIPTS_DIR}/display_audio.sh > ${TEMPFILE}
        fi

        if [[ ${run_info} == 1 ]]; then
            # Create .md file, convert to HTML and display with lynx
            echo ${TITLE} > ${TEMPFILE}.md
            echo "=====" >> ${TEMPFILE}.md
            echo '```' >> ${TEMPFILE}.md
            cat ${TEMPFILE} >> ${TEMPFILE}.md
            echo '```' >> ${TEMPFILE}.md

            # Display WiFi notes
            if [[ ${ans} == '5' ]]; then
                cat ${DOCS_DIR}/wifi_notes.md >> ${TEMPFILE}.md
            fi

            ${CMARK} ${TEMPFILE}.md > ${TEMPFILE}.html
            #clear
            ${LYNX}  ${TEMPFILE}.html
        fi
    fi
    done
done
exit 0

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
