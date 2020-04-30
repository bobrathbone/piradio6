#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: configure_ir_remote.sh,v 1.21 2020/03/14 16:23:13 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
# This program uses whiptail. Set putty terminal to use UTF-8 charachter set
# for best results

SCRIPT=$0
RADIO_DIR=/usr/share/radio
LOG=${RADIO_DIR}/install_ir.log
CONFIG=/etc/radiod.conf
BOOTCONFIG=/boot/config.txt
LIRC_ETC=/etc/lirc
LIRC_OPTIONS=${LIRC_ETC}/lirc_options.conf
LIRCD_CONFIG=${LIRC_ETC}/lircd.conf
CONFIG_DIR=${LIRC_ETC}/lircd.conf.d 
CONVERT_SCRIPT="/usr/share/lirc/lirc-old2new"
KEYMAPS_TOML=/lib/udev/rc_keymaps 
KEYMAPS=/etc/rc_keymaps
ERRORS=(0)

STRETCH=1
BUSTER=2

OS=${STRETCH}
IR_GPIO=9	
IR_REMOTE_LED=0
DT_OVERLAY=""
REMOTE_LED=0

sudo rm -f ${LOG}
echo "$0 configuration log, $(date) " | tee ${LOG}

# Check if user wants to configure IR remote control 
if [[ -f ${CONFIG}.org ]]; then
        ans=0
        ans=$(whiptail --title "Configure IR Remote Control?" --menu "Choose your option" 15 75 9 \
        "1" "Run IR Remote Control configuration?" \
        "2" "Do not change configuration?" 3>&1 1>&2 2>&3)

        exitstatus=$?
        if [[ $exitstatus != 0 ]] || [[ ${ans} == '2' ]]; then
                echo "Current IR remote control configuration unchanged" | tee -a ${LOG}
                exit 0
        fi
fi

# Select the Operating system
ans=0
selection=1
while [ $selection != 0 ]
do
        ans=$(whiptail --title "Select operating system" --menu "Choose your option" 15 75 9 \
        "1" "Rasbian Buster or later" \
        "2" "Rasbian Stretch" \
	3>&1 1>&2 2>&3)

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
                exit 0
        fi

        if [[ ${ans} == '1' ]]; then
                DESC="Rasbian Buster or later selected"
		OS=${BUSTER}

        elif [[ ${ans} == '2' ]]; then
                DESC="Rasbian Stretch selected"
		OS=${STRETCH}
	fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
done

# Select the IR sensor GPIO 
ans=0
selection=1
while [ $selection != 0 ]
do
        ans=$(whiptail --title "Select IR sensor GPIO configuration" --menu "Choose your option" 15 75 9 \
        "1" "Directly connected LCD - No DAC (GPIO 9 pin 21)" \
        "2" "Directly connected LCD with a USB DAC (GPIO 9 pin 21)" \
        "3" "LCD with I2C backpack - No DAC (GPIO 9 pin 21)" \
        "4" "Adafruit RGB plate (GPIO 16)" \
        "5" "All versions using a DAC (GPIO 25)" \
        "6" "IQaudIO Cosmic Controller (GPIO 25)" \
        "7" "PiFace CAD (GPIO 23)" \
	3>&1 1>&2 2>&3)

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
                exit 0
        fi

        if [[ ${ans} == '1' ]]; then
                DESC="Directly connected LCD - No DAC (GPIO 9 pin 21)"
		IR_GPIO=9	

        elif [[ ${ans} == '2' ]]; then
                DESC="Directly connected LCD with a USB DAC (GPIO 9 pin 21)"
		IR_GPIO=9	

        elif [[ ${ans} == '3' ]]; then
                DESC="LCD with I2C backpack - No DAC (GPIO 9)"
		IR_GPIO=9	

        elif [[ ${ans} == '4' ]]; then
                DESC="Adafruit RGB plate (GPIO 16)"
		IR_GPIO=16	

        elif [[ ${ans} == '5' ]]; then
                DESC="All 40 pin versions using a DAC (GPIO 25)"
		IR_GPIO=25	

        elif [[ ${ans} == '6' ]]; then
                DESC="IQaudIO Cosmic Controller (GPIO 25)"
		IR_GPIO=25	

        elif [[ ${ans} == '7' ]]; then
                DESC="Piface CAD (GPIO 23)"
		IR_GPIO=23	
	fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
done

if [[ ${OS} == ${STRETCH} ]]; then
	echo "" | tee -a ${LOG}
	echo "You have selected Stretch as the OS version you are using."  | tee -a ${LOG}
	echo "Please note the release date of the kernel you are using from the line below:"  | tee -a ${LOG}
	echo -n "    " | tee -a ${LOG}
	uname -s -r -v | tee -a ${LOG}
	echo -n "Enter to continue:"
	read ans

	ans=0
	selection=1
	while [ $selection != 0 ]
	do
		ans=$(whiptail --title "Select kernel version" --menu "Choose your option" 15 75 9 \
		"1" "Kernel is April 2019 or later" \
		"2" "Kernel is before April 2019" \
		3>&1 1>&2 2>&3)

		exitstatus=$?
		if [[ $exitstatus != 0 ]]; then
			exit 0
		fi

		if [[ ${ans} == '1' ]]; then
			DESC="Kernel is April 2019 or later"
			DT_OVERLAY="dtoverlay=gpio-ir,gpio_pin=${IR_GPIO}"
			DT_COMMAND="sudo dtoverlay gpio-ir gpio_pin=${IR_GPIO}"

		elif [[ ${ans} == '2' ]]; then
			DESC="Kernel is before April 2019"
			DT_OVERLAY="dtoverlay=lirc-rpi,gpio_in_pin=${IR_GPIO},gpio_in_pull=up"
			DT_COMMAND="sudo dtoverlay lirc-rpi gpio_in_pin=${IR_GPIO} gpio_in_pull=up"
		fi

		whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
		selection=$?
	done
else
	# OS is Raspbian Buster or later
	DT_OVERLAY="dtoverlay=gpio-ir,gpio_pin=${IR_GPIO}"
	DT_COMMAND="sudo dtoverlay gpio-ir gpio_pin=${IR_GPIO}"
fi

# Configure remote activity LED
ans=0
selection=1
while [ $selection != 0 ]
do
        ans=$(whiptail --title "Configure remote activity LED" --menu "Choose your option" 15 75 9 \
        "1" "Default GPIO 11 (pin 23)" \
        "2" "All designs using DAC sound card GPIO 16 (pin 36)" \
        "3" "Adafruit plate  GPIO 13 (pin 33)" \
        "4" "IQaudIO Cosmic Controller GPIO 14 (pin 8)" \
	"5" "No remote activity LED or manually configure" \
	3>&1 1>&2 2>&3)

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
                exit 0
        fi

        if [[ ${ans} == '1' ]]; then
                DESC="Default GPIO 11 selected"
		REMOTE_LED=11	

        elif [[ ${ans} == '2' ]]; then
                DESC="All designs using DAC sound cards, GPIO 16 (pin 36)"
		REMOTE_LED=16	

        elif [[ ${ans} == '3' ]]; then
                DESC="Adafruit plate/PiFace CAD, GPIO 13 (pin 33)"
		REMOTE_LED=13	

        elif [[ ${ans} == '4' ]]; then
                DESC="IQaudIO Cosmic controller, GPIO 14 (pin 8)"
		REMOTE_LED=14	

        elif [[ ${ans} == '4' ]]; then
                DESC="No remote activity LED"
		REMOTE_LED=0	
	fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
done

# Display configuration changes
echo "Selected GPIO is ${IR_GPIO}" | tee -a ${LOG}
echo "Remote activity LED is GPIO ${REMOTE_LED}" | tee -a ${LOG}
echo "" | tee -a ${LOG}

# Commit changes 

# Delete any old IR overlays
sudo sed -i -e /^dtoverlay=gpio-ir/d ${BOOTCONFIG}
sudo sed -i -e /^dtoverlay=lirc-rpi/d ${BOOTCONFIG}
sudo sed -i -e /^dtoverlay=gpio-ir/d ${BOOTCONFIG}

# Write the new one to /boot/config.txt
sudo sed -i -e "$ a ${DT_OVERLAY}" ${BOOTCONFIG}
echo "Added following line to ${BOOTCONFIG}:" | tee -a ${LOG}
echo ${DT_OVERLAY} | tee -a ${LOG}

# Load Device Tree overlay
echo ${DT_COMMAND} | tee -a ${LOG}
${DT_COMMAND}
if [[ $? -ne '0' ]]; then       # Do not seperate from above
	# The overlay may be already loaded
	echo "Warning: Failed to run ${DT_COMMAND}" | tee -a ${LOG}
fi
echo "" | tee -a ${LOG}

# Configure the remote LED
sudo sed -i -e "0,/^remote_led/{s/remote_led.*/remote_led=${REMOTE_LED}/}" ${CONFIG}
echo "Configured remote_led=${REMOTE_LED} in ${CONFIG}" | tee -a ${LOG}

# Install LIRC packages
echo "" | tee -a ${LOG}
if [[ ${OS} == ${STRETCH} ]]; then
	packages="lirc ir-keytable python-lirc"
	lirc_service="lirc"
else
	# Buster or later
	packages="lirc ir-keytable python-pylirc lirc-compat-remotes lirc-drv-irman lirc-doc "
	lirc_service="lircd"
fi

for package in ${packages}
do
	echo "Installing ${package}"  | tee -a ${LOG}
	sudo apt-get -y install ${package}
	if [[ $? -ne '0' ]]; then       # Do not seperate from above
		if [[  ${package} == "lirc" || ${package} == "lircd" ]]; then
			# Set up lirc(d) package
			echo "Setting up ${package}" | tee -a ${LOG}
			
			# Set-up remotes config directory
			if [[ -f ${LIRCD_CONFIG}  &&  ${OS} == ${BUSTER} ]]; then
				CMD="sudo cp ${LIRCD_CONFIG}.dist ${LIRCD_CONFIG}"
				echo ${CMD};${CMD} | tee -a ${LOG}
			fi

			# Run the configuration conversion script
			CMD="sudo ${CONVERT_SCRIPT}"
			echo ${CMD};${CMD}  | tee -a ${LOG}

			# Start LIRC
			CMD="sudo systemctl start ${lirc_service}"
			echo ${CMD};${CMD}
			if [[ $? -ne '0' ]]; then       # Do not seperate from above
				echo "Warning: Failed to start ${lirc_service}" | tee -a ${LOG}
			fi
		else
			echo "Failed to install ${package}" | tee -a ${LOG}
			ERRORS=$(($ERRORS+1))
		fi
	fi
done

# Copy options file 
CMD="sudo cp ${LIRC_OPTIONS}.dist ${LIRC_OPTIONS}"  
echo ${CMD} | tee -a ${LOG}
${CMD}
if [[ $? -ne '0' ]]; then       # Do not seperate from above
	echo "Failed to copy ${LIRC_OPTIONS}" | tee -a ${LOG}
	ERRORS=$(($ERRORS+1))
fi

# Configure driver and device in lirc_options.conf
sudo sed -i -e '/^driver/s/devinput/default/' ${LIRC_OPTIONS}
sudo sed -i -e '/^device/s/auto/\/dev\/lirc0/' ${LIRC_OPTIONS}

# Re-install default configuration file if lirc previously
# installed using an old procedure
#${CMD} >/dev/null 2>&1

# Copy keymaps
echo "" | tee -a ${LOG}
if [[ -f  ${KEYMAPS_TOML}/rc6_mce.toml ]]; then
	CMD="sudo cp ${KEYMAPS_TOML}/rc6_mce.toml ${KEYMAPS}/rc6_mce"
	echo ${CMD} | tee -a ${LOG}
	${CMD}
	if [[ $? -ne '0' ]]; then       # Do not seperate from above
		echo "Failed to copy keymaps" | tee -a ${LOG}
		ERRORS=$(($ERRORS+1))
	fi
fi

# Copy lircrc (IR remote control button definitions) to /etc/lirc 
CMD="sudo cp ${RADIO_DIR}/lircrc.dist /etc/lirc/lircrc"
echo ${CMD} | tee -a ${LOG}
${CMD}
if [[ $? -ne '0' ]]; then       # Do not seperate from above
	echo "Failed to copy ${RADIO_DIR}/lircrc.dist to /etc/lirc" | tee -a ${LOG}
	ERRORS=${ERRORS}+1
fi

# Disable devinput.lircd.conf
DEVINPUT=${CONFIG_DIR}/devinput.lircd.conf
if [[ -f ${DEVINPUT} ]]; then
	CMD="sudo mv ${DEVINPUT} ${DEVINPUT}.dist"
	echo ${CMD} | tee -a ${LOG}
	${CMD}
	if [[ $? -ne '0' ]]; then       # Do not seperate from above
		echo "Warning: failed to disable ${CONFIG_DIR}/devinput.lircd.conf" | tee -a ${LOG}
		exit 1
	fi
fi

# Make configuration file readable to all
sudo chmod og+r ${LIRCD_CONFIG}


if [[ ${ERRORS} > 0 ]]; then
	echo "There were ${ERRORS} errors" | tee -a ${LOG}
fi

# Print configuration instructions
echo "" |  tee -a ${LOG}
echo "Configuration of LIRC completed OK" |  tee -a ${LOG}
echo "Reboot the system and then run the following " |  tee -a ${LOG}
echo "to configure your IR remote control" |  tee -a ${LOG}
echo "	  sudo irrecord -f -d /dev/lirc0 ~/lircd.conf " |  tee -a ${LOG}
echo "" |  tee -a ${LOG}
if [[ ${OS} == ${STRETCH} ]]; then
	echo "Then copy your configuration file (myremote.conf) to  ${LIRCD_CONFIG}" |  tee -a ${LOG}
	echo "	  sudo cp myremote.conf ${LIRCD_CONFIG}" |  tee -a ${LOG}
else
	# OS Buster or later
	echo "Then copy your configuration file (myremote.conf) to  ${CONFIG_DIR}" |  tee -a ${LOG}
	echo "	  sudo cp myremote.conf ${CONFIG_DIR}/." |  tee -a ${LOG}
fi
echo "" |  tee -a ${LOG}
echo "Reboot the Raspberry Pi " |  tee -a ${LOG}
echo "" |  tee -a ${LOG}
echo "A log of this run will be found in ${LOG}"

exit 0

