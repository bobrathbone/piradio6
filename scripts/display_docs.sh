#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: display_docs.sh,v 1.10 2025/04/08 14:42:13 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# Display HTML documents in the /usr/share/radio/docs directory
# These are created from .md (markdown) documents using cmark 
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

if [[ ${FLAGS} == '-t' ]]; then 
    cd ../
    DIR=$(pwd)
fi

DOCS_DIR=${DIR}/docs
DOC=""
LYNX=/usr/bin/lynx
CMARK_EXE=/usr/bin/cmark
CMARK="${CMARK_EXE} --hardbreaks"

# Install cmark if not yet installed
if [[ ! -x ${CMARK_EXE} ]]; then
    sudo apt-get -y install cmark
fi

# Install lynx if not yet installed
if [[ ! -x ${LYNX} ]]; then
    sudo apt-get -y install lynx
fi

ans=$(whiptail --title "Select document to display" --menu "Choose document" 15 75 9 \
"1" "Creating radio station playlists" \
"2" "Creating Media playlists" \
"3" "How to pair a Bluetooth device" \
"4" "Creating an IR remote control definition" \
"5" "Network configuration and roaming" \
"6" "Configuration tutorial (/etc/radiod.conf)" \
"7" "Recording a Radio station" \
"8" "Running Shoutcast" \
"9" "Building the radiod package from GitHub" \
"10" "Running diagnostics" \
3>&1 1>&2 2>&3)

exitstatus=$?
if [[ $exitstatus != 0 ]]; then
    exit 0

elif [[ ${ans} == '1' ]]; then
    DOC=${DOCS_DIR}/station_playlist

elif [[ ${ans} == '2' ]]; then
    DOC=${DOCS_DIR}/media_playlist

elif [[ ${ans} == '3' ]]; then
    DOC=${DOCS_DIR}/pair_bluetooth_device

elif [[ ${ans} == '4' ]]; then
    DOC=${DOCS_DIR}/create_ir_remote

elif [[ ${ans} == '5' ]]; then
    DOC=${DOCS_DIR}/network_configuration

elif [[ ${ans} == '6' ]]; then
    DOC=${DOCS_DIR}/config_tutorial

elif [[ ${ans} == '7' ]]; then
    DOC=${DOCS_DIR}/record_radio

elif [[ ${ans} == '8' ]]; then
    DOC=${DOCS_DIR}/shoutcast

elif [[ ${ans} == '9' ]]; then
    DOC=${DOCS_DIR}/build

elif [[ ${ans} == '10' ]]; then
    DOC=${DOCS_DIR}/running_diagnostics
fi

MD_DOC=${DOC}.md
HTML_DOC=${DOC}.html
echo "${LYNX} ${HTML_DOC}"

# Create and display requested html document
if [[ -f ${MD_DOC} ]]; then
    ${CMARK} --hardbreaks ${MD_DOC} > ${HTML_DOC}
    ${LYNX} ${HTML_DOC}
else
    echo "Error: Document ${MD_DOC} not found"
    echo -n "Press enter to continue: "
    read x
    exit 1
fi
exit 0
