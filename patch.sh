#!/bin/bash
# $Id: patch.sh,v 1.15 2021/04/29 14:14:37 bob Exp $
# Patching script for the Raspberry PI radio
export LC_ALL=C

PKGDEF=piradio
VERSION=$(grep ^Version: ${PKGDEF} | awk '{print $2}')
ARCH=$(grep ^Architecture: ${PKGDEF} | awk '{print $2}')
PATCHLOG=patch.log
PATCHFILES="display_model.py display_config.sh configure_audio.sh remote_control.py rotary_class_alternative.py radiod.conf"

sudo chown pi:pi *.py
sudo chmod +x *.py
sudo chown pi:pi *.sh
sudo chmod +x *.sh
sudo chmod -x language/* voice.dist

VERSION=7.1
NUM=2
# Tar build files
PATCHTAR="radiod-patch-${VERSION}-${NUM}.tar.gz" 
echo "Creating patch ${PATCHTAR} $(date)" | tee ${PATCHLOG}
tar -cvzf ${PATCHTAR} ${PATCHFILES} README.patch | tee -a ${PATCHLOG}

# End of patch script
