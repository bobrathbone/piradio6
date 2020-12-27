#!/bin/bash
# Raspberry Pi Internet Radio
# $Id: configure_audio.sh,v 1.54 2020/12/02 14:57:52 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used to select the sound card to be used.
# It configures /etc/mpd.conf
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
# The authors shall not be liable for any loss or damage however caused.
#
# This program uses whiptail. Set putty terminal to use UTF-8 charachter set
# for best results

# Set -s flag to skip package addition or removal (dpkg error otherwise)
# Also prevent running dtoverlay command (Causes hangups on stretch)
SKIP_PKG_CHANGE=$1
SCRIPT=$0

BOOTCONFIG=/boot/config.txt
MPDCONFIG=/etc/mpd.conf
ASOUNDCONF=/etc/asound.conf
MODPROBE=/etc/modprobe.d/alsa-base.conf
MODULES=/proc/asound/modules
DIR=/usr/share/radio
CONFIG=/etc/radiod.conf
ASOUND_DIR=${DIR}/asound
AUDIO_INTERFACE="alsa"
LIBDIR=/var/lib/radiod
PIDFILE=/var/run/radiod.pid
I2SOVERLAY="dtoverlay=i2s-mmap"
PULSEAUDIO=/usr/bin/pulseaudio

LOGDIR=${DIR}/logs
LOG=${LOGDIR}/audio.log

BLUETOOTH_SERVICE=/lib/systemd/system/bluetooth.service

# Audio types
JACK=1	# Audio Jack or Sound Cards
HDMI=2	# HDMI
DAC=3	# DAC card
BLUETOOTH=4	# Bluetooth speakers
USB=5	# USB PnP DAC
TYPE=${JACK}
SCARD="headphones"	# aplay -l string. Set to headphones, HDMI, DAC or bluetooth
			# to configure the audio_out parameter in the configuration file

# dtoverlay parameter in /etc/config.txt
DTOVERLAY=""

# Device and Name
DEVICE="hw:0,0"
CARD=0
NAME="Onboard jack"
MIXER="software"
# Format is Frequency 44100 Hz: 16 bits: 2 channels
FORMAT="44100:16:2"
NUMID=1

# Pulse audio asound.conf
USE_PULSE=0
ASOUND_CONF_DIST=asound.conf.dist

# Create log directory
sudo mkdir -p ${LOGDIR}
sudo chown pi:pi ${LOGDIR}

sudo rm -f ${LOG}
echo "$0 configuration log, $(date) " | tee ${LOG}

# Wheezy not supported
cat /etc/os-release | grep -i wheezy >/dev/null 2>&1
if [[ $? == 0 ]]; then 	# Don't seperate from above
	echo "This prograqm is not supported on Debian Wheezy!"	| tee -a ${LOG}
	echo "Exiting program." | tee -a ${LOG}
	exit 1
fi

# Stop the radio and MPD
CMD="sudo systemctl stop radiod.service"
echo ${CMD};${CMD} | tee -a ${LOG}
CMD="sudo systemctl stop mpd.service"
echo ${CMD};${CMD} | tee -a ${LOG}

sleep 2	# Allow time for service to stop

# If the above fails check pid
if [[ -f  ${PIDFILE} ]];then
	rpid=$(cat ${PIDFILE})
	if [[ $? == 0 ]]; then 	# Don't seperate from above
		sudo kill -TERM ${rpid}  >/dev/null 2>&1
	fi
fi

sudo service mpd stop

selection=1 
while [ $selection != 0 ]
do
	ans=$(whiptail --title "Select audio output" --menu "Choose your option" 18 75 12 \
	"1" "On-board audio output jack" \
	"2" "HDMI output" \
	"3" "USB DAC" \
	"4" "HiFiBerry DAC/Miniamp/Pimoroni pHat" \
	"5" "HiFiBerry DAC plus" \
	"6" "HiFiBerry DAC Digi" \
	"7" "HiFiBerry Amp" \
	"8" "IQAudio DAC/Zero DAC" \
	"9" "IQAudio DAC plus and Digi/AMP " \
	"10" "JustBoom DAC/Zero/Amp" \
	"11" "JustBoom Digi HAT/zero" \
	"12" "Bluetooth device" \
	"13" "Adafruit speaker bonnet" \
	"14" "Pimoroni Pirate Audio (HiFiBerry DAC)" \
	"15" "Manually configure" 3>&1 1>&2 2>&3)

	exitstatus=$?
	if [[ $exitstatus != 0 ]]; then
		exit 0
	fi

	if [[ ${ans} == '1' ]]; then
		DESC="On-board audio output Jack"

	elif [[ ${ans} == '2' ]]; then
		DESC="HDMI output"
		TYPE=${HDMI}
		NUMID=3

	elif [[ ${ans} == '3' ]]; then
		DESC="USB PnP DAC"
		NAME="USB PnP"
		DEVICE="plughw:1,0"
		CARD=1
		MIXER="software"
		TYPE=${USB}
		NUMID=6

	elif [[ ${ans} == '4' ]]; then
		DESC="HiFiBerry DAC\/Miniamp\/Pimoroni pHat"
		NAME=${DESC}
		DTOVERLAY="hifiberry-dac"
		MIXER="software"
		USE_PULSE=1
		ASOUND_CONF_DIST=${ASOUND_CONF_DIST}.pivumeter
		TYPE=${DAC}

	elif [[ ${ans} == '5' ]]; then
		DESC="HiFiBerry DAC Plus"
		NAME=${DESC}
		DTOVERLAY="hifiberry-dacplus"
		MIXER="software"
		TYPE=${DAC}

	elif [[ ${ans} == '6' ]]; then
		DESC="HiFiBerry Digi"
		NAME=${DESC}
		DTOVERLAY="hifiberry-digi"
		MIXER="software"
		TYPE=${DAC}

	elif [[ ${ans} == '7' ]]; then
		DESC="HiFiBerry Amp"
		NAME=${DESC}
		DTOVERLAY="hifiberry-amp"
		MIXER="software"
		TYPE=${DAC}

	elif [[ ${ans} == '8' ]]; then
		DESC="IQAudio DAC\/Zero DAC"
		NAME=${DESC}
		DTOVERLAY="iqaudio-dac"
		MIXER="software"
		TYPE=${DAC}

	elif [[ ${ans} == '9' ]]; then
		DESC="IQAudio DAC plus or DigiAMP"
		NAME="IQAudio DAC+"
		TYPE=${DAC}
		DTOVERLAY="iqaudio-dacplus,unmute_amp"
		MIXER="software"
		TYPE=${DAC}

	elif [[ ${ans} == '10' ]]; then
		DESC="JustBoom DAC\/Amp"
		NAME="JustBoom DAC"
		DTOVERLAY="justboom-dac"
		MIXER="software"
		TYPE=${DAC}

	elif [[ ${ans} == '11' ]]; then
		DESC="JustBoom DAC\/Amp"
		NAME="JustBoom Digi HAT"
		DTOVERLAY="justboom-digi"
		MIXER="software"
		TYPE=${DAC}

	elif [[ ${ans} == '12' ]]; then
		DESC="Bluetooth device"
		# NAME is set up later
		MIXER="software"
		USE_PULSE=0
		TYPE=${BLUETOOTH}

	elif [[ ${ans} == '13' ]]; then
		DESC="Adafruit speaker bonnet"
		NAME=${DESC}
		DTOVERLAY="hifiberry-dac"
		MIXER="software"
		USE_PULSE=1
		ASOUND_CONF_DIST=${ASOUND_CONF_DIST}.bonnet
		TYPE=${DAC}

	elif [[ ${ans} == '14' ]]; then
		DESC="Pimoroni Pirate Audio (HiFiBerry DAC)"
		NAME=${DESC}
		DTOVERLAY="hifiberry-dac"
		MIXER="software"
		TYPE=${DAC}

	elif [[ ${ans} == '15' ]]; then
		DESC="Manual configuration"
	fi

	whiptail --title "$DESC selected" --yesno "Is this correct?" 10 60
	selection=$?
done 

# Summarise selection
echo "${DESC} selected" | tee -a ${LOG}
echo "Card ${CARD}, Device ${DEVICE}, Mixer ${MIXER}" | tee -a ${LOG}
if [[ ${DTOVERLAY} != "" ]]; then
	echo "dtoverlay=${DTOVERLAY}" | tee -a ${LOG}
fi

# Install alsa-utils if not already installed
PKG="alsa-utils"
if [[ ! -f /usr/bin/amixer && ${SKIP_PKG_CHANGE} != "-s" ]]; then
	echo "Installing ${PKG} package" | tee -a ${LOG}
	sudo apt-get --yes install ${PKG}
fi

# Install pulsaudio if required
PKG="pulseaudio"
if [[ ! -f /usr/bin/pulseaudio && ${SKIP_PKG_CHANGE} != "-s" && ${USE_PULSE} == 1 ]]; then
	echo "Installing ${PKG} package" | tee -a ${LOG}
	sudo apt-get --yes install ${PKG}
fi

# Configure pulseaudio package
PKG="pulseaudio"
if [[ -x /usr/bin/${PKG} && ${USE_PULSE} == 1 ]]; then
	AUDIO_INTERFACE="pulse"
	echo "Package ${PKG} found" | tee -a ${LOG}
	echo "Configuring ${MPDCONFIG} for ${PKG} support" | tee -a ${LOG}
else
	echo "Configuring ${MPDCONFIG} for ${AUDIO_INTERFACE} support" | tee -a ${LOG}
fi

# Select HDMI or audio jack/DACs Alsa output
# Also setup audio_out parameter in the config file
if [[ ${TYPE} == ${HDMI} ]]; then
	echo "Configuring HDMI as output" | tee -a ${LOG}
	sudo touch ${LIBDIR}/hdmi 
	sudo amixer cset numid=3 2
	sudo alsactl store
	SCARD="HDMI"

elif [[ ${TYPE} == ${JACK} ]]; then
	echo "Configuring on-board jack as output" | tee -a ${LOG}
	sudo amixer cset numid=3 1
	sudo alsactl store
	SCARD="headphones"

elif [[ ${TYPE} == ${DAC} ]]; then
	echo "Configuring DAC as output" | tee -a ${LOG}
	SCARD="DAC"

elif [[ ${TYPE} == ${USB} ]]; then
	echo "Configuring USB PnP as output" | tee -a ${LOG}
	SCARD="USB"

# Configure bluetooth device
elif [[ ${TYPE} == ${BLUETOOTH} ]]; then
 
	# Install Bluetooth packages 	
	if [[ ${SKIP_PKG_CHANGE} != "-s" ]]; then
		echo "Checking Bluetooth packages have been installed" | tee -a ${LOG}
		sudo apt-get --yes install bluez bluez-firmware pi-bluetooth bluealsa
		sudo apt --yes autoremove
	fi

	echo "Configuring Blutooth device as output" | tee -a ${LOG}

	# Configure bluealsa
	echo |  tee -a ${LOG}
	echo "Bluetooth device configuration"  |  tee -a ${LOG}
	echo "------------------------------"  |  tee -a ${LOG}
	PAIRED=$(bluetoothctl paired-devices)
	echo ${PAIRED} |  tee -a ${LOG}
	BT_NAME=$(echo ${PAIRED} | awk '{print $3}')
	BT_DEVICE=$( echo ${PAIRED} | awk '{print $2}')

	# Disable Sap initialisation in bluetooth.service 	
	grep "noplugin=sap" ${BLUETOOTH_SERVICE}
	if [[ $? != 0 ]]; then  # Do not seperate from above
		echo "Disabling Sap driver in  ${BLUETOOTH_SERVICE}" | tee -a ${LOG}
		sudo sed -i -e 's/^ExecStart.*/& --noplugin=sap/' ${BLUETOOTH_SERVICE} | tee -a ${LOG}
	fi

	if [[  ${BT_DEVICE} != '' ]];then
		echo "Bluetooth device ${BT_NAME} ${BT_DEVICE} found"  |  tee -a ${LOG}
		NAME=${BT_NAME}
		DEVICE="bluealsa:DEV=${BT_DEVICE},PROFILE=a2dp"
		cmd="bluetoothctl trust ${BT_DEVICE}" 
		echo $cmd | tee -a ${LOG}
		$cmd | tee -a ${LOG}
		cmd="bluetoothctl connect ${BT_DEVICE}" 
		echo $cmd | tee -a ${LOG}
		$cmd | tee -a ${LOG}
		cmd="bluetoothctl discoverable on" 
		echo $cmd | tee -a ${LOG}
		$cmd | tee -a ${LOG}
		cmd="bluetoothctl info ${BLUEDEV}" 
		echo $cmd | tee -a ${LOG}
		$cmd | tee -a ${LOG}

		# Configure bluetooth device in /etc/radiod.conf 
		sudo sed -i -e "0,/^bluetooth_device/{s/bluetooth_device.*/bluetooth_device=${BT_DEVICE}/}" ${CONFIG}
	else
		echo "Error: No paired bluetooth devices found" | tee -a ${LOG}
		echo "Use bluetoothctl to pair Bluetooth device" | tee -a ${LOG}
		echo "and re-run this program with the following commands" | tee -a ${LOG}
		echo "	cd ${DIR} " | tee -a ${LOG}
		echo "	sudo ./configure_adio.sh  " | tee -a ${LOG}
		echo -n "Press enter to continue: "
		read ans
		exit 1
	fi
	SCARD="bluetooth"
fi

# Configure the audio_out parameter
echo |  tee -a ${LOG}
echo "Configuring audio_out parameter in ${CONFIG} with ${SCARD} " | tee -a ${LOG}
sudo sed -i -e "0,/audio_out=/{s/^#aud/aud/}" ${CONFIG}
sudo sed -i -e "0,/audio_out=/{s/^audio_out=.*/audio_out=\"${SCARD}\"/}" ${CONFIG}
grep -i "audio_out="  ${CONFIG} | tee -a ${LOG}

# Set up asound configuration for espeak and aplay
echo |  tee -a ${LOG}
echo "Configuring card ${CARD} for aplay (${ASOUNDCONF})" | tee -a ${LOG}
if [[ ! -f ${ASOUNDCONF}.org && -f ${ASOUNDCONF} ]]; then
	echo "Saving ${ASOUNDCONF} to ${ASOUNDCONF}.org" | tee -a ${LOG}
	sudo cp -f ${ASOUNDCONF} ${ASOUNDCONF}.org
fi
echo "Copying ${ASOUND_CONF_DIST} to ${ASOUNDCONF}" | tee -a ${LOG}
sudo cp -f ${ASOUND_DIR}/${ASOUND_CONF_DIST} ${ASOUNDCONF}

if [[ ${CARD} == 0 ]]; then
        sudo sed -i -e "0,/card/s/1/0/" ${ASOUNDCONF}
        sudo sed -i -e "0,/plughw/s/1,0/0,0/" ${ASOUNDCONF}
else
        sudo sed -i -e "0,/card/s/0/1/" ${ASOUNDCONF}
        sudo sed -i -e "0,/plughw/s/0,0/1,0/" ${ASOUNDCONF}
fi

# Save original configuration 
if [[ ! -f ${MPDCONFIG}.orig ]]; then
	sudo cp -f -p ${MPDCONFIG} ${MPDCONFIG}.orig
fi

# Configure name device and mixer type in mpd.conf
sudo cp -f -p ${MPDCONFIG}.orig ${MPDCONFIG}
sudo sed -i -e "0,/^\sname/{s/\sname.*/\tname\t\t\"${NAME}\"/}" ${MPDCONFIG}
sudo sed -i -e "0,/device/{s/.*device.*/\tdevice\t\t\"${DEVICE}\"/}" ${MPDCONFIG}
sudo sed -i -e "0,/mixer_type/{s/.*mixer_type.*/\tmixer_type\t\"${MIXER}\"/}" ${MPDCONFIG}
sudo sed -i -e "/^#/ ! {s/\stype.*/\ttype\t\t\"${AUDIO_INTERFACE}\"/}" ${MPDCONFIG}
if [[ ${TYPE} == ${BLUETOOTH} ]]; then
	sudo sed -i -e '/bluealsa:/a \\tformat\t\t\"44100:16:2\"'  ${MPDCONFIG}
fi

# Save all new alsa settings
sudo alsactl store
if [[ $? != 0 ]]; then 	# Don't seperate from above
	echo "Failed to alsa settings"
fi

# Bind address  to any
sudo sed -i -e "0,/bind_to_address/{s/.*bind_to_address.*/bind_to_address\t\t\"any\"/}" ${MPDCONFIG}

# Save original boot config
if [[ ! -f ${BOOTCONFIG}.orig ]]; then
	sudo cp ${BOOTCONFIG} ${BOOTCONFIG}.orig
fi

# Delete existing dtoverlays
echo "Delete old audio overlays" | tee -a ${LOG}
sudo sed -i '/dtoverlay=iqaudio/d' ${BOOTCONFIG}
sudo sed -i '/dtoverlay=hifiberry/d' ${BOOTCONFIG}
sudo sed -i '/dtoverlay=justboom/d' ${BOOTCONFIG}

# Add dtoverlay for sound cards
if [[ ${DTOVERLAY} != "" ]]; then
	sudo sed -i "/\[all\]/a dtoverlay=${DTOVERLAY}" ${BOOTCONFIG} 

	# Set up the dtoverlay command
	if [[ ${SKIP_PKG_CHANGE} != "-s" ]]; then
		dtcommand=$(echo ${DTOVERLAY} | sudo sed 's/\,/ /' )
		cmd="sudo dtoverlay ${dtcommand}"
		echo ${cmd} | tee -a ${LOG}
		${cmd}
	else
		echo "Skipping dtoverlay command" | tee -a ${LOG}
	fi
	echo "Disable on-board audio" | tee -a ${LOG}
	sudo sed -i 's/^dtparam=audio=.*$/dtparam=audio=off/g'  ${BOOTCONFIG}
	sudo sed -i 's/^#dtparam=audio=.*$/dtparam=audio=off/g'  ${BOOTCONFIG}

else
	sudo sed -i 's/^dtparam=audio=.*$/dtparam=audio=on/g'  ${BOOTCONFIG}
	sudo sed -i 's/^#dtparam=audio=.*$/dtparam=audio=on/g'  ${BOOTCONFIG}
fi

# Configure I2S overlay
grep "^#${I2SOVERLAY}" ${BOOTCONFIG} >/dev/null 2>&1
if [[ $?  == 0 ]]; then
        sudo sed -i 's/^#dtoverlay=i2s-mmap/dtoverlay=i2s-mmap/g'  ${BOOTCONFIG}
fi

grep "^${I2SOVERLAY}" ${BOOTCONFIG} >/dev/null 2>&1
if [[ $?  == 1 ]]; then
	sudo  bash -c "echo ${I2SOVERLAY} >> ${BOOTCONFIG}"
fi

echo; echo ${BOOTCONFIG} | tee -a ${LOG}
echo "----------------" | tee -a ${LOG}
grep ^dtparam=audio ${BOOTCONFIG} | tee -a ${LOG}
grep ^dtoverlay ${BOOTCONFIG} | tee -a ${LOG}

echo | tee -a ${LOG}
DESC=$(echo ${DESC} | sed 's/\\\//\//g')
echo "${DESC} configured" | tee -a ${LOG}

# Remove the mixer volume ID from /var/lib/radiod 
# This forces the radiod program run set_mixer_id.sh on the next run
sudo rm -f ${LIBDIR}/mixer_volume_id >/dev/null 2>&1

# Check if required pulse audio installed
if [[ ${USE_PULSE} == 1 ]]; then
	if [[ ! -f ${PULSEAUDIO} ]]; then
		echo "${DESC} requires pulseaudio to run correctly" | tee -a ${LOG}
		echo "Run: sudo apt-get install pulseaudio" | tee -a ${LOG}
		echo "and re-run ${SCRIPT}" | tee -a ${LOG}
		exit 1
	fi
fi

# Check if audio_out parameter in configuration file
grep ^audio_out= ${CONFIG}
if [[ $? != 0 ]]; then  # Don't seperate from above
        echo "ERROR: audio_out parameter missing from ${CONFIG}" | tee -a ${LOG}
        echo "At the end of this program run \"amixer controls | grep card\" " | tee -a ${LOG}
        echo "to display available audio output devices" | tee -a ${LOG}
	echo '' | tee -a ${LOG}
        echo "Add the audio_out parameter to ${CONFIG} as shown below" | tee -a ${LOG}
        echo "     audio_out=\"<unique string>\"" | tee -a ${LOG}
        echo "     Where: <unique string> is a unique string from the amixer command output" | tee -a ${LOG}
        echo "Enter to continue: "
        read ans
fi

# Reboot dialogue
if [[ ${SKIP_PKG_CHANGE} != "-s" ]]; then
	if (whiptail --title "Audio selection" --yesno "Reboot Raspberry Pi (Recommended)" 10 60) then
		echo "Rebooting Raspberry Pi" | tee -a ${LOG}
		sudo reboot 
	else
		echo | tee -a ${LOG}
		echo "You chose not to reboot!" | tee -a ${LOG}
		echo "Changes made will not become active until the next reboot" | tee -a ${LOG}
	fi
fi

echo "A log of these changes has been written to ${LOG}"
exit 0
# End of script

