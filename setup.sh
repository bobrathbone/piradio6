#!/bin/bash
#set -x
#set -B
# Raspberry Pi Internet Radio setup script
# $Id: setup.sh,v 1.18 2025/02/12 12:28:03 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used to create and install the radiod program 
# if the source has been downloaded from GitHub
# See https://github.com/bobrathbone/piradio6
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#

BUILD_TOOLS="equivs apt-file lintian"
PKG=radiod
MPD=/usr/bin/mpd
MPD_PACKAGES="mpd mpc python3-mpd python3-rpi.gpio"
OS_RELEASE=/etc/os-release
CONFIGPARSER="python-configparser"
PYTHON_REQUESTS="python3-requests"
HOME_DIR=/home/pi

# Check running as sudo
if [[ "$EUID" -eq 0 ]];then
    echo "Do not run ${0} with sudo"
    exit 1
fi

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
function osname
{
    VERSION_OSNAME=$(grep VERSION_CODENAME $OS_RELEASE)
    arr=(${VERSION_OSNAME//=/ })
    OSNAME=$(echo "${arr[1]}" | tr -d '"')
    echo ${OSNAME}
}

echo "Radio package set-up script - $(date)"

echo "Installing build tools ${BUILD_TOOLS}" 
sudo apt-get -y install ${BUILD_TOOLS}
if [[ $? -ne 0 ]]; then
    echo "Installation of  ${BUILD_TOOLS} failed - Aborting"
    exit 1
fi

# Install MPD packages
if [[ ! -f ${MPD} ]]; then
    echo "Installing mpd packages"
    sudo apt-get -y install ${MPD_PACKAGES}
    if [[ $? -ne 0 ]]; then
        echo "Installation of  ${MPD_PACKAGES} failed - Aborting"
        exit 1
    fi
fi

echo "Setting execute bit on all executables (*.py *.sh)" 
sudo chmod -R +x *.py *.sh

REL_ID=$(release_id)
echo "Installing other required packages"
if [[ ${REL_ID} -lt 12 ]]; then
     PKGS="${PYTHON_REQUESTS} ${CONFIGPARSER}"
else 
     PKGS="${PYTHON_REQUESTS}"
fi
sudo apt-get -y install ${PKGS}
if [[ $? -ne 0 ]]; then
    echo "Installation of ${PKGS} failed - Aborting"
    exit 1
fi

# Remove redundant packages
sudo apt-get -y autoremove

# Update file cache
sudo apt-file update

# Setup .vimrc if it doesn't exist
if [[ ! -f ${HOME_DIR}/.vimrc ]]; then
    echo "set tabstop=4 shiftwidth=4 expandtab" > ${HOME_DIR}/.vimrc
    echo "retab " >> ${HOME_DIR}/.vimrc
fi

# Build software
./build.sh

# End of setup script

# :set tabstop=4 shiftwidth=4 expandtab
# :retab
