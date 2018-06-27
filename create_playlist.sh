#!/bin/bash
# set -x
#set -B
# Raspberry Pi Internet Radio
# $Id: create_playlist.sh,v 1.19 2018/06/13 07:34:56 bob Exp $
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
#	     The authors shall not be liable for any loss or damage however caused.
#
# This program uses whiptail. Set putty terminal to use UTF-8 charachter set
# for best results

# Check running as sudo
if [[ "$EUID" -ne 0 ]];then
  	echo "Usage: sudo ${0}"
	exit 1
fi
VERBOSE=$1
PLAYLIST="USB_Stick"
DIR="media"
EXT="m3u"
MPD_MUSIC="/var/lib/mpd/music"
MPD_PLAYLISTS="/var/lib/mpd/playlists"
SHARE="/var/lib/radiod/share"
TEMPFILE="/tmp/list$$"
USBDEV=""
MAX_SIZE=5000

# Make a playlist name from the filter
make_name(){
	str="${1}"
	leng=${#str}
	name=""
	for (( i=0; i<${#str}; i++ )); do
		char="${str:$i:1}"
		if [[ $char == "/" ]];then
			continue
		fi
		if [[ $char != [A-Za-z0-9] ]];then
			name=${name}"_"
		else
			name=${name}$char
		fi
	done
	echo $name
}

# Stop the radio and mpd
CMD="sudo systemctl stop radiod.service"
echo ${CMD};${CMD}
CMD="sudo systemctl stop mpd.service"
echo ${CMD};${CMD}

sleep 2

# If the above fails check pid
rpid=$(cat /var/run/radiod.pid)
if [[ $? == 0 ]]; then  # Don't seperate from above
        sudo kill -TERM ${rpid}
fi

# Find which device is in use
if [[ -b /dev/sda1 ]]; then
	USBDEV="/dev/sda1"
elif [[ -b /dev/sda2 ]]; then
	 USBDEV="/dev/sda2"
fi 

ans=0
selection=1
while [ $selection != 0 ]
do
	 ans=$(whiptail --title "Create playlist" --menu "Choose your option" 15 75 9 \
	 "1" "From USB stick" \
	 "2" "From network share" 3>&1 1>&2 2>&3)

	 exitstatus=$?
	 if [[ $exitstatus != 0 ]]; then
		  exit 0
	 fi

	 if [[ ${ans} == '1' ]]; then
		  DESC="USB stick selected"
		PLAYLIST="USB_Stick"
		DIR="media"
		# Mount the USB stick
		if [[ ${USBDEV} != "" ]]; then
			sudo mount ${USBDEV} /media >/dev/null 2>&1
			if [[ $? != 0 ]]; then
				echo "Failed to mount USB stick"
				exit 1
			fi
			echo "Mounted  ${USBDEV} on /media"
		fi

	 elif [[ ${ans} == '2' ]]; then
		DESC="Network share selected"
		PLAYLIST="Network"
		DIR="share"
		# Mount the network share specified in /var/lib/radiod/share
		if [[ -f ${SHARE} ]]; then
			CMD=$(cat ${SHARE}) 
			echo ${CMD}; sudo ${CMD} >/dev/null 2>&1
			if [[ $? != 0 ]]; then
				echo "Failed to mount network drive"
				exit 1
				echo "Mounted network drive on /share"
			fi
		fi

	 else
		  DESC="User interface in ${CONFIG} unchanged"
		  echo ${DESC}
		exit 0
	 fi

	 whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
	 selection=$?
done

# Set up a filter (This becomes the playlist name)
ans=0
selection=1
while [ $selection != 0 ]
do
	FILTERS=$(whiptail --title "Enter a filter" --inputbox "Example: \"The Beatles\" or blank for no filter" 10 60 "" 3>&1 1>&2 2>&3) 
	exitstatus=$?
	if [ $exitstatus != 0 ]; then
		exit 0
	fi
	if [[ ${FILTERS} != "" ]]; then
		whiptail --title "Your filter is: ${FILTERS}" --yesno "Is this correct?" 10 60
	else
		whiptail --title "You have not specified a filter" --yesno "Is this correct?" 10 60
	fi
	selection=$?
done

# Create playlist name from (This becomes the playlist name)
if [[ ${FILTERS} != "" ]];then
	PLAYLIST=$(make_name "${FILTERS}")
fi

ans=0
selection=1
while [ $selection != 0 ]
do
	PLAYLIST=$(whiptail --title "Enter a playlist name" --inputbox "Example: ${PLAYLIST}" 10 60 ${PLAYLIST} 3>&1 1>&2 2>&3) 
	exitstatus=$?
	if [ $exitstatus != 0 ]; then
		exit 0
	fi
	whiptail --title "Your playlist name is: ${PLAYLIST}" --yesno "Is this correct?" 10 60
	selection=$?
done

# Make sure no spaces or special characters in the playlist name
PLAYLIST=$(make_name "${PLAYLIST}")

# Change directory to MPD music directory
CMD="cd ${MPD_MUSIC}/"
${CMD}

# Build the create command 
echo "Processing directory ${DIR}. Please wait."
CMD="sudo find -L ${DIR} -type f -name *.mp3 -or -name *.ogg -or -name *.flac "
${CMD} > ${TEMPFILE}

CMD="sudo mv ${TEMPFILE} /tmp/${PLAYLIST}"
${CMD}

# Perform the playlist creation
echo "Processing ${FILTERS}"
if [[ ${FILTERS} != "" ]];then
	cat /dev/null > /tmp/${PLAYLIST}.${EXT}
	# Split filters into seperate lines
        filters=$(echo ${FILTERS} | tr "|" "\n")
	
        echo "${filters}" |
	while read filter
        do
                echo "Processing filter \"${filter}\""

		# Process filter beginning with /
		if [[ ${filter:0:1} == "/" ]];then
			filter=$(echo ${filter} | tr "/" "\/")
		fi
		egrep -i "${filter}" /tmp/${PLAYLIST} >> /tmp/${PLAYLIST}.${EXT}
	done
else
	mv /tmp/${PLAYLIST}  /tmp/${PLAYLIST}.${EXT}
fi	

# Get directory size
if [[ ${VERBOSE} == "-v" ]];then
	cat  /tmp/${PLAYLIST}
fi

echo
echo "==========================================================="
size=$(wc -l /tmp/${PLAYLIST}.${EXT} | awk {'print $1'} )
if [[ ${FILTERS} != "" ]];then
	echo "${size} tracks found in directory ${DIR} matching \"${FILTERS}\""
else
	echo "${size} tracks found in directory ${DIR} (No filter)"
fi

if [[ ${size} -eq 0 ]];then
	echo "No matching tracks for filter \"${FILTERS}\" found"
	echo "No playlist created"
	exit 1
fi

if [[ ${size} -gt ${MAX_SIZE} ]];then
	CMD="cd /tmp/"
	echo  ${CMD}; ${CMD}

	echo "Splitting playlist into ${MAX_SIZE} chunks"
	CMD="split --numeric-suffixes=1 -l${MAX_SIZE}  ${PLAYLIST}.${EXT} ${PLAYLIST}"
	echo  ${CMD}; ${CMD}

	# Remove oversized file
	CMD="rm ${PLAYLIST}.${EXT}"
	echo  ${CMD}; ${CMD}

	# Copy new playlists to MPD playlist directory
	for file in ${PLAYLIST}*
	do
		CMD="mv ${file} ${MPD_PLAYLISTS}/${file}.${EXT}"
		echo  ${CMD}; ${CMD}
	done
	
else
	# Move new playlists to MPD playlist directory
	CMD="mv /tmp/${PLAYLIST}.${EXT}  ${MPD_PLAYLISTS}/${PLAYLIST}.${EXT}"
	echo  ${CMD}; ${CMD}
fi

# Update the mpd database
CMD="sudo service mpd start"
echo ${CMD};${CMD}
if [[ $? -ne 0 ]];then
	echo "Error Failed to start Music Mlayer Daemon"
else
	CMD="mpc stop"
	echo ${CMD};${CMD}
	CMD="mpc update ${DIR}"
	echo ${CMD};${CMD}
fi


exit 0



