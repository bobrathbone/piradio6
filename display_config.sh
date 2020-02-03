#!/bin/bash
# Raspberry Pi Internet Radio display configuration for analysis
# $Id: display_config.sh,v 1.5 2020/01/25 10:26:59 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used during installation to set up which
# radio daemon is to be used
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
DIR=/usr/share/radio
LOG=${DIR}/config.log
BOOTCONFIG=/boot/config.txt
MPD_CONFIG=/etc/mpd.conf
OS_RELEASE=/etc/os-release
RADIOLIB=/var/lib/radiod
ASOUND=/etc/asound.conf
SOUND_CARD=0

echo "Configuration log for $(hostname) $(date)" | tee ${LOG}

# Display OS
echo | tee -a ${LOG}
echo "OS Configuration" | tee ${LOG}
echo "----------------" | tee -a ${LOG}
cat ${OS_RELEASE} | tee -a ${LOG}

echo | tee -a ${LOG}
echo "Kernel version " | tee ${LOG}
echo "--------------" | tee -a ${LOG}
uname -a  | tee -a ${LOG}

# Display radio software version
echo | tee -a ${LOG}
echo "Radio version" | tee ${LOG}
echo "-------------" | tee -a ${LOG}
sudo ${DIR}/radiod.py version | tee -a ${LOG}

# Display MPD configuration
echo | tee -a ${LOG}
echo "MPD Configuration" | tee ${LOG}
echo "----------------" | tee -a ${LOG}
grep -A 8 ^audio_output  ${MPD_CONFIG} | tee -a ${LOG}

# Display boot configuration
echo | tee -a ${LOG}
echo ${BOOTCONFIG} | tee -a ${LOG}
echo "----------------" | tee -a ${LOG}
grep ^dtparam=audio ${BOOTCONFIG} | tee -a ${LOG}
grep -A 8  ^dtoverlay ${BOOTCONFIG} | tee -a ${LOG}

# Display configuration
echo | tee -a ${LOG}
echo "----------------" | tee -a ${LOG}
${DIR}/config_class.py | tee -a  ${LOG}

# Display sound devices
echo | tee -a ${LOG}
echo "---------------------------------------" | tee -a ${LOG}
/usr/bin/aplay -l | tee -a ${LOG}

echo | tee -a ${LOG}
echo "Mixer controls" | tee -a ${LOG}
echo "--------------" | tee -a ${LOG}
amixer -c ${SOUND_CARD} controls | tee -a ${LOG}

# Display /etc/asound.conf configuration
if [[ -f ${ASOUND} ]]; then 
	echo | tee -a ${LOG}
	echo "${ASOUND} configuration file" | tee -a ${LOG}
	echo "-----------------------------------" | tee -a ${LOG}
	cat ${ASOUND} | tee -a ${LOG}
fi

# Display mixer ID configuration
echo | tee -a ${LOG}
echo "Mixer ID Configuration (${RADIOLIB}/mixer_volume_id)" | tee ${LOG}
echo "-------------------------------------------------------" | tee -a ${LOG}
echo "mixer_volume_id=$(cat ${RADIOLIB}/mixer_volume_id)" | tee -a ${LOG}

# Create tar file
tar -zcf ${LOG}.tar.gz ${LOG} >/dev/null 2>&1

echo | tee -a ${LOG}
echo "=================== End of run =====================" | tee -a ${LOG}
echo "This configuration has been recorded in ${LOG}"
echo "A compressed tar file has been saved in ${LOG}.tar.gz"
echo "Send ${LOG}.tar.gz to bobrathbone.com if required"
echo | tee -a ${LOG}

