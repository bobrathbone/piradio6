#!/bin/bash
# Raspberry Pi Internet Radio display configuration for analysis
# $Id: display_config.sh,v 1.14 2020/11/15 19:27:08 bob Exp $
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
EMAIL=bob@bobrathbone.com
AUTOSTART=~/.config/lxsession/LXDE-pi/autostart

echo "Configuration log for $(hostname) $(date)" | tee ${LOG}
echo "IP address: $(hostname -I)"  | tee ${LOG}

# Display OS
echo | tee -a ${LOG}
echo "OS Configuration" | tee -a ${LOG}
echo "----------------" | tee -a ${LOG}
cat ${OS_RELEASE} | tee -a ${LOG}

echo | tee -a ${LOG}
echo "Kernel version " | tee -a ${LOG}
echo "--------------" | tee -a ${LOG}
uname -a  | tee -a ${LOG}

# Check for X-Windows graphic radio installation
echo | tee -a ${LOG}
echo "Desktop installation" | tee -a ${LOG}
echo "--------------------" | tee -a ${LOG}
ps -e | grep -E -i "xfce|kde|gnome" >/dev/null 2>&1
if [[ $? == 0 ]]; then
	echo "X-Windows appears to be installed" | tee -a ${LOG}
    if [[ -f ${AUTOSTART} ]]; then
        entry=$(grep -i "radio" ${AUTOSTART})
        if [[ $? == 0 ]]; then
            if [[ ${entry:0:1} == "#" ]]; then
                echo "Graphic version of the radio is disabled in ${AUTOSTART}"
            else
                echo "Graphic version of the radio configured in ${AUTOSTART}"
            fi
            echo ${entry}
        else
            echo "Graphic versions of the radio not configured in ${AUTOSTART}"
        fi
    else
        echo "Error - No ${AUTOSTART} file found" 
    fi
else
	echo "X-Windows is not installed" | tee -a ${LOG}
	echo "Probaly Raspbian-Lite installed" | tee -a ${LOG}
fi 

# Display radio software version
echo | tee -a ${LOG}
echo "Radio version" | tee -a ${LOG}
echo "-------------" | tee -a ${LOG}
sudo ${DIR}/radiod.py version | tee -a ${LOG}

# Display MPD configuration
echo | tee -a ${LOG}
echo "MPD Configuration" | tee -a ${LOG}
echo "----------------" | tee -a ${LOG}
mpd -V | grep Music | tee -a ${LOG}
if [[ -f  ${MPD_CONFIG} ]]; then
	grep -A 8 ^audio_output  ${MPD_CONFIG} | tee -a ${LOG}
else
	echo "FATAL ERROR!"
	echo "MPD (Music Player Daemon) has not been installed" | tee -a ${LOG}
	echo "Install packages mpd,mpc and python-mpd" | tee -a ${LOG}
	echo "and rerun configure_radio.sh to set-up the radio software" | tee -a ${LOG}
	exit 1
fi

if [[ -f /usr/bin/pulseaudio ]];then
	echo | tee -a ${LOG}
	echo "The pulseaudio package appears to be installed" | tee -a ${LOG}
fi

# Display boot configuration
echo | tee -a ${LOG}
echo ${BOOTCONFIG} | tee -a ${LOG}
echo "----------------" | tee -a ${LOG}
grep ^hdmi ${BOOTCONFIG} | tee -a ${LOG}
grep ^dtparam=audio ${BOOTCONFIG} | tee -a ${LOG}
grep -A 8  ^dtoverlay ${BOOTCONFIG} | tee -a ${LOG}

# Display configuration
echo | tee -a ${LOG}
echo "Radio configuration" | tee -a ${LOG}
echo "-------------------" | tee -a ${LOG}
echo "Configuration file /etc/radiod.conf" | tee -a ${LOG}
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
echo "Mixer ID Configuration (${RADIOLIB}/mixer_volume_id)" | tee -a ${LOG}
echo "-------------------------------------------------------" | tee -a ${LOG}
echo "mixer_volume_id=$(cat ${RADIOLIB}/mixer_volume_id)" | tee -a ${LOG}


echo | tee -a ${LOG}
echo "Hardware information" | tee -a ${LOG}
echo "--------------------" | tee -a ${LOG}
sudo ${DIR}/display_model.py version | tee -a ${LOG}

# Create tar file
tar -zcf ${LOG}.tar.gz ${LOG} >/dev/null 2>&1

echo | tee -a ${LOG}
echo "=================== End of run =====================" | tee -a ${LOG}
echo "This configuration has been recorded in ${LOG}" 
echo "A compressed tar file has been saved in ${LOG}.tar.gz" | tee -a ${LOG}
echo "Send ${LOG}.tar.gz to ${EMAIL} if required" | tee -a ${LOG}
echo | tee -a ${LOG}

