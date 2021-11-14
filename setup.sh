#!/bin/bash
# set -x
#set -B
# Raspberry Pi Internet Radio setup script
# $Id: setup.sh,v 1.6 2021/11/13 15:25:00 bob Exp $
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
PKGDEF=piradio
VERSION=$(grep ^Version: ${PKGDEF} | awk '{print $2}')
ARCH=$(grep ^Architecture: ${PKGDEF} | awk '{print $2}')
DEBPKG=${PKG}_${VERSION}_${ARCH}.deb
MPD=/usr/bin/mpd
MPD_PACKAGES="mpd mpc python3-mpd python3-rpi.gpio"
OTHER_PACKAGES="python3-requests python-configparser python"

# Check running as sudo
if [[ "$EUID" -eq 0 ]];then
    echo "Do not run ${0} with sudo"
    exit 1
fi

echo "Radio package set-up script - $(date)"
echo "Building ${DEBPKG}"

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

echo "Installing other required packages"
sudo apt-get -y install ${OTHER_PACKAGES}
if [[ $? -ne 0 ]]; then
    echo "Installation of ${OTHER_PACKAGES} failed - Aborting"
    exit 1
fi

# Remove redundant packages
sudo apt -y autoremove

# Update file cache
sudo apt-file update

# Build the pakage
./build.sh

echo
echo "Now install the ${DEBPKG} package with the following command:"
echo "sudo dpkg -i ${DEBPKG}"

# End of setup script

