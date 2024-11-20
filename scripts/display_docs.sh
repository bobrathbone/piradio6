#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: display_docs.sh,v 1.2 2002/02/24 16:31:38 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# Display HTML documents in the /usr/share/radio/docs directory
# These are created from .md (markdown) documents using cmark 
# 
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
DOCS_DIR=${DIR}/docs
DOC=""
LYNX=/usr/bin/lynx
CMARK=/usr/bin/cmark

# Install cmark if not yet installed
if [[ ! -f ${CMARK} ]]; then
    sudo apt-get -y install cmark
fi

# Install lynx if not yet installed
if [[ ! -f ${LYNX} ]]; then
    sudo apt-get -y install lynx
fi

ans=$(whiptail --title "Select document to display" --menu "Choose document" 15 75 9 \
"1" "Creating radio station playlists" \
"2" "Creating Media playlists" \
"3" "How to pair a Bluetooth device" \
"4" "Creating an IR remote control definition" \
"5" "Document 5" \
"6" "Document 6" \
"7" "Document 7" 3>&1 1>&2 2>&3)

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
    DOC=${DOCS_DIR}/station_playlist

elif [[ ${ans} == '6' ]]; then
    DOC=${DOCS_DIR}/station_playlist
fi

MD_DOC=${DOC}.md
HTML_DOC=${DOC}.html
echo "${LYNX} ${HTML_DOC}"

# Create and display requested html document
if [[ -f ${MD_DOC} ]]; then
    ${CMARK} ${MD_DOC} > ${HTML_DOC}
    ${LYNX} ${HTML_DOC}
else
    echo "Error: Document ${MD_DOC} not found"
    echo -n "Press enter to continue: "
    read x
    exit 1
fi
exit 0
