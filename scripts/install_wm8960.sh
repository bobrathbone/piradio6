#!/bin/bash
# Raspberry Pi Internet Radio - Install Waveshare WM8960 DAC driver
# $Id: install_wm8960.sh,v 1.1 2002/02/24 14:42:37 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# Based on Waveshare WM8960 install script
# See  https://github.com/waveshare/WM8960-Audio-HAT
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.

OS_RELEASE=/etc/os-release
DIR="/usr/share/radio"
LOGDIR=${DIR}/logs
mkdir -p ${LOGDIR}
LOG=${LOGDIR}/wm8960.log
BOOTCONFIG="/boot/firmware/config.txt"

# we create a dir with this version to ensure that 'dkms remove' won't delete
# the sources during kernel updates
marker="0.0.0"

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 1>&2
   exit 1
fi

is_Raspberry=$(cat /proc/device-tree/model | awk  '{print $1}')
if [ "${is_Raspberry}" != "Raspberry" ] ; then
  echo "Sorry, this driver only works on raspberry pi"  
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


echo "$0 WM8960 configuration log, $(date) " | tee ${LOG}

# In Bookworm (Release ID 12) the configuration has been moved to /boot/firmware/config.txt
if [[ $(release_id) -lt 12 ]]; then
    echo "This script only runs on Bookworm or later - Exiting" | tee -a ${LOG}
    exit 1
fi

# Check if this machine is 32-bit if so set arm_64bit=0 in config.txt
BIT=$(getconf LONG_BIT)
if [[ ${BIT} == "32" ]]; then
    grep "arm_64bit=0" ${BOOTCONFIG} >/dev/null 2>&1
    if [[ $? != 0 ]]; then
        echo "# Disable 64-bit for the Waveshare WM8960 sound-card" >> ${BOOTCONFIG}
        echo "Setting arm_64bit=0 in ${BOOTCONFIG}" | tee -a ${LOG}
        echo "arm_64bit=0" >> ${BOOTCONFIG} 
    fi
fi

# Disable VC4 KMS V3D audio
grep "^dtoverlay=vc4-kms-v3d" ${BOOTCONFIG} >/dev/null 2>&1
if [[ $? == 0 ]]; then
    echo "Disabling VC4 KMS V3D audio in ${BOOTCONFIG}" | tee -a ${LOG}
    sed -i -e "0,/^dtoverlay=vc4-kms-v3d/{s/dtoverlay.*/#dtoverlay=vc4-kms-v3d/}" ${BOOTCONFIG} 
fi

echo "Disable on-board audio" | tee -a ${LOG}
sudo sed -i 's/^dtparam=audio=.*$/dtparam=audio=off/g'  ${BOOTCONFIG}
sudo sed -i 's/^#dtparam=audio=.*$/dtparam=audio=off/g'  ${BOOTCONFIG}

# Install git download the archive
sudo apt-get -y install git 
echo "Cloning https://github.com/waveshare/WM8960-Audio-HAT" | tee -a ${LOG}
rm -rf WM8960-Audio-HAT
git clone https://github.com/waveshare/WM8960-Audio-HAT  | tee -a ${LOG}

# Change to WM8960-Audio-HAT directory
cd WM8960-Audio-HAT
pwd | tee -a ${LOG}

echo | tee -a ${LOG}
echo "============== Running Waveshare installation script ==============" | tee -a ${LOG}
./install.sh | tee -a ${LOG}
echo "============== End of Waveshare installation script ==============" | tee -a ${LOG}
echo | tee -a ${LOG}

echo
echo "----------------------------------------------------------------------------------"
echo "A log of this installation will be found in ${LOG} "
echo "----------------------------------------------------------------------------------"
echo

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
