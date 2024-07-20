#!/bin/bash
# $Id: patch.sh,v 1.45 2024/07/14 10:40:59 bob Exp $
# Patching script for the Raspberry PI radio
export LC_ALL=C

# Version 7.5 onwards allows any user with sudo permissions to install the software
USR=$(logname)
GRP=$(id -g -n ${USR})

PKGDEF=piradio
VERSION=$(grep ^Version: ${PKGDEF} | awk '{print $2}')
ARCH=$(grep ^Architecture: ${PKGDEF} | awk '{print $2}')
PATCHLOG=patch.log
PATCHFILES="radiod.py radiod.conf rotary_class.py rotary_class_rgb_i2c.py constants.py menu_class.py radio_class.py lcd_i2c_jhd1313.py lcd_i2c_jhd1313_sgm31323.py README"

sudo chown ${USR}:${GRP} *.py
sudo chmod +x *.py
sudo chown ${USR}:${GRP} *.sh
sudo chmod +x *.sh
sudo chmod -x language/* voice.dist 

VERSION=7.7
NUM=1
# Tar build files
PATCHTAR="radiod-patch-${VERSION}-${NUM}.tar.gz" 
echo "Creating patch ${PATCHTAR} $(date)" | tee ${PATCHLOG}
tar -cvzf ${PATCHTAR} ${PATCHFILES} README.patch | tee -a ${PATCHLOG}

# End of patch script
