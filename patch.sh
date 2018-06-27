#!/bin/bash
# $Id: patch.sh,v 1.6 2018/06/02 11:50:19 bob Exp $
# Patching script for the Raspberry PI radio

PKGDEF=piradio
VERSION=$(grep ^Version: ${PKGDEF} | awk '{print $2}')
ARCH=$(grep ^Architecture: ${PKGDEF} | awk '{print $2}')
PATCHLOG=patch.log
PATCHFILES="vgradio.py gradio.py radio_class.py"

sudo chown pi:pi *.py
sudo chmod +x *.py
sudo chown pi:pi *.sh
sudo chmod +x *.sh
sudo chmod -x language/* voice.dist

VERSION=6.6
# Tar build files
NUM=2
PATCHTAR="radiod-patch-${VERSION}-${NUM}.tar.gz" 
echo "Creating patch ${PATCHTAR} $(date)" | tee ${PATCHLOG}
tar -cvzf ${PATCHTAR} ${PATCHFILES} | tee -a ${PATCHLOG}

# End of patch script
