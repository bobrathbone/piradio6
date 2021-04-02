#!/bin/bash
set -e
# Raspberry Pi Internet Radio - Install Icecast2
# This script installs and configures Airplay (shairport)
# $Id: install_airplay.sh,v 1.1 2020/10/10 15:00:45 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.

# File locations
CONFIG=/etc/radiod.conf
ALSA_CONFIG=/usr/share/alsa/alsa.conf 
DIR=/home/pi
BUILD_DIR=${DIR}/projects/airplay

# Install details
INSTALL="sudo apt-get -y install"
GIT="build-essential git xmltoman"
LIBS1="autoconf automake libtool libdaemon-dev libasound2-dev libpopt-dev libconfig-dev libssl-dev" 
LIBS2="libdaemon-dev libpopt-dev pkgconf libconfig-dev"
AVAHI="avahi-daemon libavahi-client-dev"

echo "Installing Airplay (shairport-sync)"
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}

echo "Installing GIT"
echo ${INSTALL} ${GIT} 
${INSTALL} ${GIT} 

echo "Installing shairport libraries"
echo ${INSTALL} ${LIBS1} 
${INSTALL} ${LIBS1} 
echo ${INSTALL} ${LIBS2} 
${INSTALL} ${LIBS2} 

echo "Installing Avahi daemon"
echo ${INSTALL} ${AVAHI} 
${INSTALL} ${AVAHI} 

# Remove previous build
rm -rf ${BUILD_DIR}/shairport-sync
rm -rf ${BUILD_DIR}/shairport-sync-metadata-reader 

echo "Cloning shairport-sync and metadata reader"
git clone https://github.com/mikebrady/shairport-sync.git
git clone https://github.com/mikebrady/shairport-sync-metadata-reader

echo
echo "Building shairport-sync"
echo "-----------------------"
echo "Please wait..."
cd ${BUILD_DIR}/shairport-sync
autoreconf -i -f
./configure --sysconfdir=/etc --with-alsa --with-avahi --with-ssl=openssl --with-metadata  --with-systemdcd
make 
sudo make install

echo
echo "Building shairport-sync-metadata-reader"
echo "---------------------------------------"
cd ${BUILD_DIR}/shairport-sync-metadata-reader 
autoreconf -vif
./configure 
make 
sudo make install

echo
echo "Configuring Airplay"
echo "-------------------"
echo "Setting airplay=yes in ${CONFIG}"
sudo sed -i -e "0,/^airplay=/{s/airplay=.*/airplay=yes/}" ${CONFIG}

if [[ ! -f  ${ALSA_CONFIG}.orig ]]; then
	echo "Saving ${ALSA_CONFIG} in ${ALSA_CONFIG}.orig"
	sudo cp ${ALSA_CONFIG} ${ALSA_CONFIG}.orig
fi
echo "Setting cards.pcm.default in ${ALSA_CONFIG}"
sudo sed -i -e "0,/^pcm.front cards.pcm.front/{s/pcm.front cards.pcm.front/pcm.front cards.pcm.default/}" ${ALSA_CONFIG}
echo
echo "Airplay build complete"

# End of script


