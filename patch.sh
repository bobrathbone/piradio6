#!/bin/bash
# $Id: patch.sh,v 1.20 2021/09/27 11:20:18 bob Exp $
# Patching script for the Raspberry PI radio
export LC_ALL=C

PKGDEF=piradio
VERSION=$(grep ^Version: ${PKGDEF} | awk '{print $2}')
ARCH=$(grep ^Architecture: ${PKGDEF} | awk '{print $2}')
PATCHLOG=patch.log
PATCHFILES="configure_audio.sh"

sudo chown pi:pi *.py
sudo chmod +x *.py
sudo chown pi:pi *.sh
sudo chmod +x *.sh
sudo chmod -x language/* voice.dist

VERSION=7.2
NUM=1
# Tar build files
PATCHTAR="radiod-patch-${VERSION}-${NUM}.tar.gz" 
echo "Creating patch ${PATCHTAR} $(date)" | tee ${PATCHLOG}
tar -cvzf ${PATCHTAR} ${PATCHFILES} README.patch | tee -a ${PATCHLOG}

# End of patch script
