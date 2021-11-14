#!/bin/bash
# Raspberry Pi Internet Radio - Install Icecast2
# This script installs and configures Icecast2 to run with MPD 
# $Id: install_streaming.sh,v 1.7 2021/10/17 09:12:57 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.

# File locations
DIR=/home/pi/radio
MPDCONF=/etc/mpd.conf
XMLCONF=/etc/icecast2/icecast.xml 
MPDSTREAM=${DIR}/configs/mpdstream
RADIOLIB=/var/lib/radiod
STREAMING=${RADIOLIB}/streaming
CONFIG=/etc/radiod.conf

RET=0   # Script return code

echo "Starting Icecast2 integration with the Music Player Daemon"
if [[ $( id -u ) -ne 0 ]]; then
	echo "This script can only be run as super user"
	echo "Run the command \"sudo $0\""
	exit 1
fi

# Install Icecast 
if [[ ! -f ${XMLCONF} ]]; then
	echo "The Icecast2 installation program will ask if you wish to configure Icecast2. "
	echo "Answer 'yes' to this. Configure Icecast as follows:"
	echo "Icecast2 hostname: localhost"
	echo "Icecast2 source password: mympd"
	echo "Icecast2 relay password: mympd"
	echo "Icecast2 administration password: mympd"
	echo -n "Continue y/n: "
	read ans
	if [[ "${ans}" -ne 'y' ]]; then
		echo "Exiting."
		exit 0
	fi
	echo
	apt-get install icecast2 
else
	echo "Icecast2 package already installed"
fi

echo "Configuring Icecast2 (${XMLCONF})"
if [[ !  -f ${XMLCONF}.orig ]]; then
	echo "Copying ${XMLCONF} to ${XMLCONF}.orig"
	cp -fp ${XMLCONF} ${XMLCONF}.orig
fi

# Configure /etc/
OLDENTRY="<mount-name>\/example-complex\.ogg"
NEWENTRY="<mount-name>\/mpd<\/mount>"
sed -i "s/${OLDENTRY}.*/${NEWENTRY}/g" ${XMLCONF}

# Modify mpd.conf
grep mympd /etc/mpd.conf > /dev/null
if [[ $? -ne 0 ]]; then
	cat ${MPDSTREAM} >> ${MPDCONF}
    echo "Restarting MPD"
    sudo systemctl restart mpd
    if [[ $? == 0 ]]; then
        id=$(mpc outputs | grep "MPD Stream" | awk '{print $2}')
        echo "Enabling MPD Output $id"
        mpc enable ${id} | grep "MPD Stream"
    else
        echo "Failed to restart mpd"
    fi
fi

echo "Starting service icecast2"
sudo systemctl restart icecast2 
if [[ $? -ne '0' ]]; then 	# Do not seperate from above
    echo "Failed to start service icecast2"
    RET=1
else
    echo "Succesfully restarted service icecast2"
fi

echo "Restarting MPD"
sudo systemctl restart mpd.service
if [[ $? != 0 ]]; then
    echo "Failed to restart service mpd.service"
    RET=1
else
    echo "Succesfully restarted service mpd.service"
fi

# Enable streaming
echo "Enabling streaming on in ${STREAMING}"
sudo echo "on" > ${STREAMING}
# Configure display_icecast_button parameter in /etc/radiod.conf 
sudo sed -i -e "0,/^display_icecast_button/{s/display_icecast_button.*/display_icecast_button=yes/}" ${CONFIG}

# Start icecast

exit ${RET} 

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab

