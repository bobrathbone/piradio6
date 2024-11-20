#!/bin/bash
# set -x
# Raspberry Pi Internet Radio Web Interface
# $Id: install_web_interface.sh,v 1.1 2002/02/24 14:42:37 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used during installation to set up which
# radio daemon and periperals are to be used
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.

FLAGS=$1
DIR=/usr/share/radio
# Test flag - change to current directory
if [[ ${FLAGS} == "-t" ]]; then
    DIR=$(pwd)
fi

LOGDIR=${DIR}/logs
LOG=${LOGDIR}/install_web.log
USER=$(logname)
GRP=$(id -g -n ${USER})
OS_RELEASE=/etc/os-release

# Get OS release ID
function release_id
{
    VERSION_ID=$(grep VERSION_ID $OS_RELEASE)
    arr=(${VERSION_ID//=/ })
    ID=$(echo "${arr[1]}" | tr -d '"')
    ID=$(expr ${ID} + 0)
    echo ${ID}
}

# Get OS release name
function codename
{
    VERSION_CODENAME=$(grep VERSION_CODENAME $OS_RELEASE)
    arr=(${VERSION_CODENAME//=/ })
    CODENAME=$(echo "${arr[1]}" | tr -d '"')
    echo ${CODENAME}
}

# Create log directory
sudo mkdir -p ${LOGDIR}
sudo chown ${USER}:${GRP} ${LOGDIR}

if [[ ! -d ${DIR} ]]; then
    echo "Error: Radio software not installed - Exiting."
    exit 1
fi

ans=0
ans=$(whiptail --title "Radio Web interface" --menu "Choose your option" 15 75 9 \
"1" "Install radio Web interface" \
"2" "Do not install Web Interface" 3>&1 1>&2 2>&3)

exitstatus=$?
if [[ $exitstatus != 0 ]] || [[ ${ans} == '2' ]]; then
    echo "Current configuration in ${CONFIG} unchanged" | tee -a ${LOG}
    exit 0
fi

# Normal cofiguration start
echo "$0 configuration log, $(date) " | tee ${LOG}
echo "Installing radio Web interface for $(codename) OS " | tee -a ${LOG}

# Apache Web server installation
echo "Installing Apache Web server" | tee -a ${LOG}
sudo apt-get -y install apache2 php libapache2-mod-php  | tee -a ${LOG}

# Install PHP
if [[ $(release_id) -ge 12 ]]; then
    echo "Installing PHP8.2" | tee -a ${LOG}
    sudo apt-get -y install php8.2-gd php8.2-mbstring | tee -a ${LOG}
else
    echo "Installing PHP7.4" | tee -a ${LOG}
    sudo apt-get -y install php7.4-gd php7.4-mbstring | tee -a ${LOG}
fi

# Remove redundant packages
#sudo apt-get -y autoremove | tee -a ${LOG}

# Install MariaDB database.
echo "Installing MariaDB database" | tee -a ${LOG}
if [[ $(release_id) -ge 12 ]]; then
    sudo apt-get -y install php8.2-gd php8.2-mbstring mariadb-server php-mysql | tee -a ${LOG}
    sudo apt-get -y install php8.2-curl | tee -a ${LOG}
    rm -f radiodweb_3.1_arm64.deb*
    wget http://bobrathbone.com/raspberrypi/packages/radiodweb_3.1_arm64.deb | tee -a ${LOG}
    sudo dpkg -i radiodweb_3.1_arm64.deb | tee -a ${LOG}
else
    sudo apt-get -y install php7.4-gd php7.4-mbstring mariadb-server php-mysql | tee -a ${LOG}
    sudo apt-get -y install php7.4-curl | tee -a ${LOG}
    rm -f radiodweb_2.3_armhf.deb*
    wget http://bobrathbone.com/raspberrypi/packages/radiodweb_2.3_armhf.deb | tee -a ${LOG}
    sudo dpkg -i radiodweb_2.3_armhf.deb | tee -a ${LOG}
fi

sudo apt-get -y --fix-broken install | tee -a ${LOG}

# Enable modules
sudo phpenmod gd mbstring | tee -a ${LOG}

#sudo apachectl restart | tee -a ${LOG}

echo "Setting up MariaDB database" | tee -a ${LOG}
sudo mysql --execute="SELECT PASSWORD('raspberry')" | tee -a ${LOG}
sudo mysql --execute="GRANT USAGE ON *.* TO 'pi'@'localhost' IDENTIFIED BY PASSWORD '*1844F2B11CCAEF3B31F573A1384F608BB6DE3DF9'" | tee -a ${LOG}
sudo mysql --execute="GRANT ALL PRIVILEGES ON ompd.* TO 'pi'@'localhost'"| tee -a ${LOG}
sudo mysql --execute="FLUSH PRIVILEGES" | tee -a ${LOG}

echo "A log of these changes has been written to ${LOG}"
exit 0

# End of configuration script

# set tabstop=4 shiftwidth=4 expandtab
# retab


