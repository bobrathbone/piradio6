#!/bin/bash
# $Id: patch.sh,v 1.40 2024/03/04 16:22:58 bob Exp $
# Patching script for the Raspberry PI radio
export LC_ALL=C

# Version 7.5 onwards allows any user with sudo permissions to install the software
USR=$(logname)
GRP=$(id -g -n ${USR})

PKGDEF=piradio
VERSION=$(grep ^Version: ${PKGDEF} | awk '{print $2}')
ARCH=$(grep ^Architecture: ${PKGDEF} | awk '{print $2}')
PATCHLOG=patch.log
PATCHFILES="station.urls configure_ir_remote.sh install_wm8960.sh"

sudo chown ${USR}:${GRP} *.py
sudo chmod +x *.py
sudo chown ${USR}:${GRP} *.sh
sudo chmod +x *.sh
sudo chmod -x language/* voice.dist 

VERSION=7.6
NUM=3
# Tar build files
PATCHTAR="radiod-patch-${VERSION}-${NUM}.tar.gz" 
echo "Creating patch ${PATCHTAR} $(date)" | tee ${PATCHLOG}
tar -cvzf ${PATCHTAR} ${PATCHFILES} README.patch | tee -a ${PATCHLOG}

# End of patch script
