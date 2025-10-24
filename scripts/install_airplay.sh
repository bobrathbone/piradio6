#!/bin/bash
set -e
# $Id: install_airplay.sh,v 1.4 2025/10/21 08:10:47 bob Exp $
# Raspberry Pi Internet Radio - Install Airplay
# This script installs and configures Airplay (shairport)
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.

FLAGS=$1
DIR=/usr/share/radio
# Test flag - change to current directory
if [[ ${FLAGS} == "-t" ]]; then
    DIR=$(pwd)
fi

LOGDIR=${DIR}/logs
LOG=${LOGDIR}/install_airplay.log

# File locations
CONFIG=/etc/radiod.conf
ALSA_CONFIG=/usr/share/alsa/alsa.conf 
BUILD_DIR=${DIR}/projects/airplay

function press_enter
{
    echo
    echo "Press enter to continue: "
    read x
}

run=1
while [ ${run} == 1 ]
do
    INSTALL=0
    STATUS=0
    ENABLE=0
    DISABLE=0
    ans=0
    selection=1

    clear
    while [ $selection != 0 ]
    do
        ans=$(whiptail --title "Airplay installation & configuration" --menu "Choose your option" 15 75 9 \
        "1" "Install Airplay software (shairport-sync)" \
        "2" "Display shairport-sync service status" \
        "3" "Enable shairport-sync service" \
        "4" "Disable shairport-sync service" \
        3>&1 1>&2 2>&3)

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
                exit 0
        fi

        if [[ ${ans} == '1' ]]; then
            DESC="Install Airplay software"
            INSTALL=1
            run=0

        elif [[ ${ans} == '2' ]]; then
            DESC="Display shairport-sync service status"
            STATUS=1
            
        elif [[ ${ans} == '3' ]]; then
            DESC="Enable shairport-sync service"
            ENABLE=1

        elif [[ ${ans} == '4' ]]; then
            DESC="Disable shairport-sync service"
            DISABLE=1

        fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
    done

    if [[ ${STATUS} == 1 ]]; then
        echo
        echo "Press Ctrl-C to exit status display"
        echo "==================================="
        echo "$(grep airplay= ${CONFIG}) set in ${CONFIG}"
        echo
        sudo systemctl status shairport-sync || /bin/true
        echo "Press enter to continue"
        read a

    elif [[ ${ENABLE} == 1 ]]; then
        echo "Enabling Airplay (shairport-sync)"
        sudo systemctl enable shairport-sync || /bin/true
        sudo systemctl start shairport-sync || /bin/true
        echo "Setting airplay=yes in /etc/radiod.conf"
        sudo sed -i -e "0,/^airplay=/{s/airplay=.*/airplay=yes/}" ${CONFIG}
        press_enter

    elif [[ ${DISABLE} == 1 ]]; then
        echo "Disabling Airplay (shairport-sync)"
        sudo systemctl stop shairport-sync || /bin/true
        sudo systemctl disable shairport-sync || /bin/true
        echo "Setting airplay=no in /etc/radiod.conf"
        sudo sed -i -e "0,/^airplay=/{s/airplay=.*/airplay=no/}" ${CONFIG}
        press_enter
    fi

done

# Install details
echo "$0 configuration log, $(date) " | tee {LOG}
echo "Using ${DIR}" | tee -a {LOG}
INSTALL="sudo apt-get -y install"
GIT="build-essential git xmltoman"
LIBS1="autoconf automake libtool libdaemon-dev libasound2-dev libpopt-dev libconfig-dev libssl-dev" 
LIBS2="libdaemon-dev libpopt-dev pkgconf libconfig-dev"
AVAHI="avahi-daemon libavahi-client-dev"

echo "Installing Airplay (shairport-sync)" | tee -a ${LOG}
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
echo "Installing GIT"
echo ${INSTALL} ${GIT} 
${INSTALL} ${GIT} 

# Trixie faile to find avahi-client. Using the following workaround to overcome this
sudo apt-get clean
sudo rm -R /var/lib/apt/lists
sudo apt update
#apt install libavahi-client-dev 

echo "Installing shairport libraries" | tee -a ${LOG}
echo ${INSTALL} ${LIBS1}  | tee -a ${LOG}
${INSTALL} ${LIBS1} 
echo ${INSTALL} ${LIBS2}  | tee -a ${LOG}
${INSTALL} ${LIBS2}  | tee -a ${LOG}

echo "Installing Avahi daemon" | tee -a ${LOG}
echo ${INSTALL} ${AVAHI}  | tee -a ${LOG}
${INSTALL} ${AVAHI}  | tee -a ${LOG}

# Remove previous build | tee -a ${LOG}
rm -rf ${BUILD_DIR}/shairport-sync
rm -rf ${BUILD_DIR}/shairport-sync-metadata-reader 

echo "Cloning shairport-sync and metadata reader" | tee -a ${LOG}
git clone https://github.com/mikebrady/shairport-sync.git
git clone https://github.com/mikebrady/shairport-sync-metadata-reader

echo
echo "Building shairport-sync" | tee -a ${LOG}
echo "-----------------------"
echo "Please wait..."
cd ${BUILD_DIR}/shairport-sync
autoreconf -i -f
./configure --sysconfdir=/etc --with-alsa --with-avahi --with-ssl=openssl --with-metadata  --with-systemdcd
make 
sudo make install

echo
echo "Building shairport-sync-metadata-reader" | tee -a ${LOG}
echo "---------------------------------------"
cd ${BUILD_DIR}/shairport-sync-metadata-reader 
autoreconf -vif
./configure 
make 
sudo make install

echo
echo "Configuring Airplay" | tee -a ${LOG}
echo "-------------------"
echo "Setting airplay=yes in ${CONFIG}" | tee -a ${LOG}
sudo sed -i -e "0,/^airplay=/{s/airplay=.*/airplay=yes/}" ${CONFIG}

if [[ ! -f  ${ALSA_CONFIG}.orig ]]; then
	echo "Saving ${ALSA_CONFIG} in ${ALSA_CONFIG}.orig" | tee -a ${LOG}
	sudo cp ${ALSA_CONFIG} ${ALSA_CONFIG}.orig
fi
echo "Setting cards.pcm.default in ${ALSA_CONFIG}" | tee -a ${LOG}
sudo sed -i -e "0,/^pcm.front cards.pcm.front/{s/pcm.front cards.pcm.front/pcm.front cards.pcm.default/}" ${ALSA_CONFIG}
echo
echo "Airplay build complete" | tee -a ${LOG}
echo "A log of this run will be found in ${LOG}"

# End of script


