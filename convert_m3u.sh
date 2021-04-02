#!/bin/bash
#set -x
#set -B
# Raspberry Pi Internet Radio
# Convert m3u Radio stream file to stationlist format
# $Id: convert_m3u.sh,v 1.3 2021/03/22 20:50:14 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used during installation to create playlists
# from either a network share or a USB stick
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.

DIR=/tmp
INPUT_FILE=$1

if [[ ! -f ${INPUT_FILE} ]];then
    echo "Input file ${INPUT_FILE} not found"
    echo "Usage: $0 <input m3u file>"
    exit 1
fi 

OUTPUT_FILE="${INPUT_FILE##*/}"
OUTPUT_FILE="${OUTPUT_FILE%.*}"
OUTPUT_FILE="${DIR}/${OUTPUT_FILE}"
PLAYLIST_NAME=${OUTPUT_FILE##*/}

echo "Converting ${INPUT_FILE} to ${OUTPUT_FILE}"
echo "(${PLAYLIST_NAME})" | tee ${OUTPUT_FILE} 

cat ${INPUT_FILE} | 
while read line;
do
    if [[ ${line} =~ '#EXTINF:' ]]; then
        name=${line#\#EXTINF:-1,}
    fi
    if [[ ${line} =~ 'http' ]]; then
        url=${line}
        output="[${name}] ${url}"
        echo ${output} | tee -a ${OUTPUT_FILE}
    fi
done 
echo "${INPUT_FILE} converted to stationlist file ${OUTPUT_FILE}"
