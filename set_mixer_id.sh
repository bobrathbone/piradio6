#!/bin/bash
#set -x
# Raspberry Pi Internet Radio
# $Id: set_mixer_id.sh,v 1.9 2019/09/06 14:17:25 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used during installation to set up the mixer volume ID 
# parameter mixer_volume_id in /etc/radiod.conf
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
CONFIG=/etc/radiod.conf
BOOTCONFIG=/boot/config.txt
LIBDIR=/var/lib/radiod
LIB_MIXERID=${LIBDIR}/mixer_volume_id
LIB_HDMI=${LIBDIR}/hdmi
MIXERID=0
SAVEIFS=${IFS}

# Controls strings for amixer ( The order of these is important)
CONTROLS=" Playback_Volume Master_Playback_Volume Speaker_Playback_Volume Analogue_Playback_Volume Digital_Playback_Volume"

for control in ${CONTROLS}
do 
	text=$(echo ${control} | sed 's/_/ /g')

	# Get the mixer volume ID and set in radiod.conf
	VOL=$(amixer controls | grep -i "${text}")
	IFS=","
	read -ra ELEMENTS <<< "${VOL}"
	for i in "${ELEMENTS[@]}"; do
		if [[ $i =~ "numid" ]]; then
			IFS="="
			read -ra NUMID <<< "${i}"
			MIXERID=${NUMID[1]}
			break
		fi
	done
done
IFS=${SAVEIFS}
echo "mixer_volume_id=${MIXERID}"

# Update /var/lib/radiod/mixer_volume_id:
sudo echo ${MIXERID} > ${LIB_MIXERID} 

grep "dtparam=audio=on" ${BOOTCONFIG}
if [[ $? == 0 ]]; then 	# Do not seperate from above
	# Set output for HDMI on on-board jack
	if [[ -f ${LIB_HDMI} ]]; then
		echo "Configuring HDMI audio output"
		MODE=2
		sudo rm -f ${LIB_HDMI}
	else
		echo "Configuring on-board jack audio output"
		MODE=1
	fi
	cmd="sudo amixer cset numid=${MIXERID} ${MODE}" >/dev/null 2>&1
	echo ${cmd};${cmd}
fi


# End of script

