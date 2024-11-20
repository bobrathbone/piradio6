#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# Audio output configurator
# $Id: configure_audio_device.sh,v 1.1 2002/02/24 14:42:36 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used to select the sound card to be used.
# It configures /etc/mpd.conf and /etc/asound.conf depending upon
# the output of the "aplay" -l command
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
# The authors shall not be liable for any loss or damage however caused.
#

# This script requires an English locale(C)
export LC_ALL=C

MPDCONFIG=/etc/mpd.conf
ASOUNDCONF=/etc/asound.conf
CONFIG=/etc/radiod.conf
TMP=/tmp/aplay$$
DEFAULT_DEVICE="headphones"
DEVICE=$1

# This function identifies the card that matches the device   
# string specified by the device string. For example "headphones" 
# Returns the card number for the specified device string
# If no audio_out parameter specified, configure for card 0
function getCard {
    sDevice=$(echo $1 | sed -e 's/^"//' -e 's/"$//')
	${APLAY} > ${TMP}
	aplay -l | grep -i ^card > ${TMP} 
	while read -r card
	do
		echo ${card} | grep -i ${sDevice} >/dev/null 2>&1 
		ret=$?
		if [[ $ret -eq "0" ]]; then
			device=$(echo ${card} | awk '{print $2}') 
			device=${device%:}
            break
		fi
	done < ${TMP}
	rm -f ${TMP}

	if [[ ${device} == "" ]];then
		device='0'
	fi
	let nDevice=${device}	# Convert to a number
	echo ${nDevice}
}

# Routine to get device from either /etc/radiod.conf or command line
# If neither found then default to "headphones"
function getDevice {
	sDevice=$1
	if [[ ${sDevice} == "" ]]; then
		device=$(grep -i ^audio_out= ${CONFIG})
		if [[ $device != "" ]]; then
			SAVEIFS=${IFS}
			IFS="="
			params=$(echo ${device})
			sDevice=$(echo $params | awk '{print $2}'  | tr --delete \" )
		else
			sDevice=${DEFAULT_DEVICE}
		fi
	fi
	echo ${sDevice}
}

# This routine configures the correct card number in asound.conf
# and /etc/mpd.conf. 
function configure {
	num=$1
    device=$2
	echo "Configuring ${ASOUNDCONF} with card $num"
    sudo sed -i -e "0,/card.*/s/card.*/card $num/" ${ASOUNDCONF}
    sudo sed -i -e "0,/plughw.*/s/plughw.*/plughw:$num,0\"/" ${ASOUNDCONF}

	# Do not overcopy equalizer device definition 
	grep "plug:" ${MPDCONFIG} >/dev/null 2>&1
	if [[ $? != 0 ]]; then	# Don't seperate from above
		# Set up device "hw:<card>:0"
		echo "Configuring ${MPDCONFIG} with card $num"
		sudo sed -i -e "0,/device/{s/.*device.*/\tdevice\t\t\"hw:${card},0\"/}" ${MPDCONFIG}
	else 
		echo "${MPDCONFIG} configured with equalizer plugin"
	fi
}

# Create backups of configuration files
function backup {
	if [[ ! -f ${ASOUNDCONF}.org ]]; then
		sudo cp ${ASOUNDCONF} ${ASOUNDCONF}.org
	fi
	if [[ ! -f ${MPDCONFIG}.orig ]]; then
		sudo cp ${MPDCONFIG} ${MPDCONFIG}.orig
	fi
}

function print_usage {
	echo "Usage: $1 [--help] [-h] [-d <device>]"
	echo "   Where <device> is an optional device such as headphones, DAC or HDMI"
	echo "   If the audio_out parameter is configured in ${CONFIG}"
	echo "   this will be used as the required device."
	echo "   Use -h or --help for this help message."
}

# Usage and help
function usage {
	if [[ $2 == "-h" || $2 == "--help" ]]; then
		print_usage 
		exit 0
	elif [[ $2 != "" && $2 != "-d" ]]; then
		echo "Error: Device $2 must be specified using the -d flag"
		echo
		print_usage 
		exit 1
	fi
}

# Main routine
usage $0 $1
backup 	# Backup files
if [[ $1 == "-d" ]]; then
	DEVICE=$2
	device=$(getDevice ${DEVICE})
else
	device=$(getDevice)
fi
card=$(getCard ${device})

if [[ ${device} == "" ]]; then
	echo "Configuring first card ${card}"
else
	echo "Configuring ${device} on card ${card}"
fi

if [[ ${device} != "vc4hdmi" ]]; then
    grep "hw:wm8960" ${ASOUNDCONF} >/dev/null 2>&1
	if [[ $? != 0 ]]; then	# Don't seperate from above
        configure ${card} ${device}
    else
        echo "Skipping configuration of ${ASOUNDCONF} for WM8960 devices"
    fi
fi

# End of script
