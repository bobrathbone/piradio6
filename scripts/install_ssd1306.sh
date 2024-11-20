#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: install_ssd1306.sh,v 1.1 2002/02/24 14:42:37 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This install the Adafruit SSD1306 package for the Systech SSD1306 OLED display
# It configures /etc/mpd.conf
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
# The authors shall not be liable for any loss or damage however caused.
#
# Acknowledgement: Tony DiCola & James Divito Adafruit Industries for the SSD1306 libraries

export LC_ALL=C
ADAFRUIT_DIR="Adafruit_Python_SSD1306"

echo "Installing Adafruit SSD1306 Python3 package $(date)"

if [[ -d ${ADAFRUIT_DIR} ]]; then
    echo "${ADAFRUIT_DIR} package  is already installed" 
    echo " Do you wish to re-install ${ADAFRUIT_DIR} package" 
    echo -n "Re-install y/n: "
    read ans
    if [[ "${ans}" -eq 'y' ]]; then
	echo "Removing ${ADAFRUIT_DIR}" 
	sudo rm -rf ${ADAFRUIT_DIR}
    fi
    echo
fi

echo "This may take a while......" 
sleep 2

echo "Installing required setup tools"
sudo pip3 install setuptools

# Clone Adafruit_Python_SSD1306
git clone https://github.com/adafruit/Adafruit_Python_SSD1306.git
cd Adafruit_Python_SSD1306
sudo python3 setup.py install
