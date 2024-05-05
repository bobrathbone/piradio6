#!/bin/bash
# Raspberry Pi Internet Radio - Install Waveshare WM8960 DAC driver
# $Id: install_wm8960.sh,v 1.10 2024/03/13 15:58:21 bob Exp $
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

BOOTCONFIG=/boot/config.txt
BOOTCONFIG_2=/boot/firmware/config.txt
OS_RELEASE=/etc/os-release
DIR=/usr/share/radio
LOGDIR=${DIR}/logs
LOG=${LOGDIR}/wm8960.log

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

function install_module {
  src=$1
  mod=$2

  if [[ -d /var/lib/dkms/$mod/$ver/$marker ]]; then
    rmdir /var/lib/dkms/$mod/$ver/$marker
  fi

  if [[ -e /usr/src/$mod-$ver || -e /var/lib/dkms/$mod/$ver ]]; then
    dkms remove --force -m $mod -v $ver --all
    rm -rf /usr/src/$mod-$ver
  fi
  mkdir -p /usr/src/$mod-$ver
  cp -a $src/* /usr/src/$mod-$ver/
  dkms add -m $mod -v $ver
  dkms build $uname_r -m $mod -v $ver && dkms install --force $uname_r -m $mod -v $ver

  mkdir -p /var/lib/dkms/$mod/$ver/$marker
}

# In Bookworm (Release ID 12) the configuration has been moved to /boot/firmware/config.txt
if [[ $(release_id) -ge 12 ]]; then
    BOOTCONFIG=${BOOTCONFIG_2}
    echo "Configuring ${BOOTCONFIG} parameters"
fi

echo "$0 WM8960 configuration log, $(date) " | tee ${LOG}

#download the archive
echo "Cloning https://github.com/waveshare/WM8960-Audio-HAT"  | tee -a ${LOG}
rm -rf WM8960-Audio-HAT
git clone https://github.com/waveshare/WM8960-Audio-HAT

apt update
apt-get -y install raspberrypi-kernel-headers raspberrypi-kernel
apt-get -y install  dkms git i2c-tools libasound2-plugins

# Change to WM8960-Audio-HAT directory
cd WM8960-Audio-HAT
pwd | tee -a ${LOG}

# install WM8960 overlay 
cmd="cp wm8960-soundcard.dtbo /boot/overlays" 
echo ${cmd}  | tee -a ${LOG}
${cmd}

#set kernel modules
grep -q "i2c-dev" /etc/modules || \
  echo "i2c-dev" >> /etc/modules  
grep -q "snd-soc-wm8960" /etc/modules || \
  echo "snd-soc-wm8960" >> /etc/modules  
grep -q "snd-soc-wm8960-soundcard" /etc/modules || \
  echo "snd-soc-wm8960-soundcard" >> /etc/modules  
  
#set dtoverlays
sed -i -e 's:#dtparam=i2s=on:dtparam=i2s=on:g' ${BOOTCONFIG} || true
sed -i -e 's:#dtparam=i2c_arm=on:dtparam=i2c_arm=on:g' ${BOOTCONFIG} || true
grep -q "dtoverlay=i2s-mmap" ${BOOTCONFIG} || \
  echo "dtoverlay=i2s-mmap" >> ${BOOTCONFIG} 

#grep -q "dtparam=i2s=on" ${BOOTCONFIG} || \
#  echo "dtparam=i2s=on" >> ${BOOTCONFIG}

grep -q "dtoverlay=wm8960-soundcard" ${BOOTCONFIG} || \
  echo "dtoverlay=wm8960-soundcard" >> ${BOOTCONFIG} 
  
#install config files
mkdir -p /etc/wm8960-soundcard 

cp *.conf /etc/wm8960-soundcard
cp *.state /etc/wm8960-soundcard

#set service 
# Amended by Bob Rathbone - Don't try to start the wm8960-soundcard.service
# Only copy it and disable wm8960-soundcard.service. Not working in Bookworm
cp wm8960-soundcard /usr/bin/
cp wm8960-soundcard.service /lib/systemd/system/
echo "Enabling wm8960-soundcard.service" | tee -a ${LOG}
sudo systemctl enable wm8960-soundcard.service

echo "----------------------------------------------------------------------------------"
echo "A log of this installation will be found in ${LOG} "
echo "----------------------------------------------------------------------------------"

echo
echo "Now run the audio configuration program (configure_audio.sh)"
echo " and select option 17 Waveshare WM8960 DAC"
echo -n "Run audio configuration tool y/n: "
read ans
if [[ ${ans} == 'y' ]]; then
    ${DIR}/configure_audio.sh  
fi
# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
