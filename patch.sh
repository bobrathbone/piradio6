#!/bin/bash
# $Id: patch.sh,v 1.9 2021/03/22 13:31:43 bob Exp $
# Patching script for the Raspberry PI radio
export LC_ALL=C

PKGDEF=piradio
VERSION=$(grep ^Version: ${PKGDEF} | awk '{print $2}')
ARCH=$(grep ^Architecture: ${PKGDEF} | awk '{print $2}')
PATCHLOG=patch.log
PATCHFILES="radio_class.py gradio.py udp_server_class.py remote_control.py rc_daemon.py get_shoutcast.py web_config_class.py config_class.py create_stations.py set_mixer_id.sh configure_audio.sh configure_audio_device.sh display_config.sh images/raspberrypi.png asound/asound.conf.dist.pipe"

sudo chown pi:pi *.py
sudo chmod +x *.py
sudo chown pi:pi *.sh
sudo chmod +x *.sh
sudo chmod -x language/* voice.dist

VERSION=7.0
NUM=5
# Tar build files
PATCHTAR="radiod-patch-${VERSION}-${NUM}.tar.gz" 
echo "Creating patch ${PATCHTAR} $(date)" | tee ${PATCHLOG}
tar -cvzf ${PATCHTAR} ${PATCHFILES} README.patch | tee -a ${PATCHLOG}

# End of patch script
