#!/bin/bash
# $Id: patch.sh,v 1.28 2022/01/12 09:58:13 bob Exp $
# Patching script for the Raspberry PI radio
export LC_ALL=C

PKGDEF=piradio
VERSION=$(grep ^Version: ${PKGDEF} | awk '{print $2}')
ARCH=$(grep ^Architecture: ${PKGDEF} | awk '{print $2}')
PATCHLOG=patch.log
PATCHFILES="translate_class.py playlist_class.py radiod.py display_wifi.sh config_class.py display_config.sh source_class.py radio_class.py"

sudo chown pi:pi *.py
sudo chmod +x *.py
sudo chown pi:pi *.sh
sudo chmod +x *.sh
sudo chmod -x language/* voice.dist

VERSION=7.3
NUM=4
# Tar build files
PATCHTAR="radiod-patch-${VERSION}-${NUM}.tar.gz" 
echo "Creating patch ${PATCHTAR} $(date)" | tee ${PATCHLOG}
tar -cvzf ${PATCHTAR} ${PATCHFILES} README.patch | tee -a ${PATCHLOG}

# End of patch script
