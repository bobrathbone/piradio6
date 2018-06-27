#!/bin/bash
# Raspberry Pi Internet Radio
# $Id: configure_radio.sh,v 1.50 2018/06/23 08:36:14 bob Exp $
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
#	     The authors shall not be liable for any loss or damage however caused.
#
# This program uses whiptail. Set putty terminal to use UTF-8 charachter set
# for best results

# If -s flag specified (See piradio.postinst script)
FLAGS=$1

INIT=/etc/init.d/radiod
SERVICE=/lib/systemd/system/radiod.service
BINDIR="\/usr\/share\/radio\/"	# Used for sed so \ needed
DIR=/usr/share/radio
CONFIG=/etc/radiod.conf
LXSESSION=""	# Start desktop radio at boot time
FULL_SCREEN=""	# Start graphic radio fullscreen
SCREENSIZE="800x480"	# Screen size 800x480 or 720x480
PROGRAM="Daemon radiod configured"
GPROG=""	# Which graphical radio (gradio or vgradio)

# Wiring type
WIRING_TYPE=0

# Display type
DISPLAY_TYPE=""
I2C_REQUIRED=0
I2C_ADDRESS="0x0"

# Display characteristics
I2C_ADDRESS=0x00	# I2C device address
LINES=4			# Number of display lines
WIDTH=20		# Display character width

# User interface
USER_INTERFACE=0

# Old wiring down switch
DOWN_SWITCH=10

# Check if user wants to configure radio if upgrading
if [[ -f ${CONFIG}.org ]]; then
	ans=0
	ans=$(whiptail --title "Upgrading, Re-configure radio?" --menu "Choose your option" 15 75 9 \
	"1" "Run radio configuration?" \
	"2" "Do not change configuration?" 3>&1 1>&2 2>&3) 

	exitstatus=$?
	if [[ $exitstatus != 0 ]] || [[ ${ans} == '2' ]]; then
		echo "Current configuration in ${CONFIG} unchanged"
		exit 0
	fi
fi

# Copy the distribution configuration
ans=$(whiptail --title "Replace your configuration file ?" --menu "Choose your option" 15 75 9 \
"1" "Replace configuration file" \
"2" "Do not replace configuration" 3>&1 1>&2 2>&3) 

exitstatus=$?
if [[ $exitstatus != 0 ]]; then
	exit 0

elif [[ ${ans} == '1' ]]; then
	pwd 
	sudo mv ${CONFIG} ${CONFIG}.save	
	echo "Existing configuration  copied to ${CONFIG}.save"
	sudo cp ${DIR}/radiod.conf ${CONFIG}
	echo "Current configuration ${CONFIG} replaced with distribution"
fi

# Select the user interface (Buttons or Rotary encoders)
ans=0
selection=1 
while [ $selection != 0 ]
do
	ans=$(whiptail --title "Select user interface" --menu "Choose your option" 15 75 9 \
	"1" "Push button radio" \
	"2" "Radio with Rotary Encoders" \
	"3" "HDMI or touch screen only" \
	"4" "IQAudio Cosmic Controller" \
	"5" "Do not change configuration" 3>&1 1>&2 2>&3) 

	exitstatus=$?
	if [[ $exitstatus != 0 ]]; then
		exit 0
	fi

	if [[ ${ans} == '1' ]]; then
		DESC="Push buttons selected"
		USER_INTERFACE=1

	elif [[ ${ans} == '2' ]]; then
		DESC="Rotary encoders selected"
		USER_INTERFACE=2

	elif [[ ${ans} == '3' ]]; then
		DESC="HDMI or touch screen only"
		USER_INTERFACE=3

	elif [[ ${ans} == '4' ]]; then
		DESC="IQAudio Cosmic Controller"
		USER_INTERFACE=4
		WIRING_TYPE=3
	else
		DESC="User interface in ${CONFIG} unchanged"	
		echo ${DESC}
	fi

	whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
	selection=$?
done

# Select the wiring type (40 or 26 pin)
if [[ ${WIRING_TYPE} == "0" ]]; then
	ans=0
	selection=1 
	while [ $selection != 0 ]
	do
		ans=$(whiptail --title "Select wiring version" --menu "Choose your option" 15 75 9 \
		"1" "40 pin version wiring" \
		"2" "26 pin version wiring" \
		"3" "Do not change configuration" 3>&1 1>&2 2>&3) 

		exitstatus=$?
		if [[ $exitstatus != 0 ]]; then
			exit 0
		fi

		if [[ ${ans} == '1' ]]; then
			DESC="40 pin version selected"
			WIRING_TYPE=1

		elif [[ ${ans} == '2' ]]; then
			DESC="26 pin version selected"
			WIRING_TYPE=2

		else
			DESC="Wiring configuration in ${CONFIG} unchanged"	
			echo ${DESC}
		fi

		whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
		selection=$?
	done
fi

# Configure the down switch
if [[ ${WIRING_TYPE} == "2" ]]; then
	ans=0
	selection=1 
	while [ $selection != 0 ]
	do
		ans=$(whiptail --title "How is the down switch wired?" --menu "Choose your option" 15 75 9 \
		"1" "GPIO 10 - Physical pin 19 (Select this if using a DAC)" \
		"2" "GPIO 18 - Physical pin 12 (Old wiring configuration)" \
		"3" "Do not change configuration" 3>&1 1>&2 2>&3) 

		exitstatus=$?
		if [[ $exitstatus != 0 ]]; then
			exit 0
		fi

		if [[ ${ans} == '1' ]]; then
			DESC="Down switch -> GPIO 10 - Physical pin 19"
			DOWN_SWITCH=10

		elif [[ ${ans} == '2' ]]; then
			DESC="Down switch -> GPIO 18 - Physical pin 12"
			DOWN_SWITCH=18

		else
			DESC="Down switch configuration in ${CONFIG} unchanged"	
			echo {DESC}
		fi

		whiptail --title "${DESC} " --yesno "Is this correct?" 10 60
		selection=$?
	done
fi 


# Select the display interface type
ans=0
selection=1 
while [ $selection != 0 ]
do
	ans=$(whiptail --title "Select display interface type" --menu "Choose your option" 15 75 9 \
	"1" "LCD wired directly to GPIO pins" \
	"2" "LCD with Arduino (PCF8574) backpack" \
	"3" "LCD with Adafruit (MCP23017) backpack" \
	"4" "Adafruit RGB LCD plate with 5 push buttons" \
	"5" "HDMI or touch screen display" \
	"6" "Olimex 128x64 pixel OLED display" \
	"7" "No display used" \
	"8" "Do not change display type" 3>&1 1>&2 2>&3) 

	exitstatus=$?
	if [[ $exitstatus != 0 ]]; then
		exit 0
	fi

	if [[ ${ans} == '1' ]]; then
		DISPLAY_TYPE="LCD"
		DESC="LCD wired directly to GPIO pins"

	elif [[ ${ans} == '2' ]]; then
		DISPLAY_TYPE="LCD_I2C_PCF8574"
		I2C_ADDRESS="0x27"
		I2C_REQUIRED=1
		DESC="LCD with Arduino (PCF8574) backpack"

	elif [[ ${ans} == '3' ]]; then
		DISPLAY_TYPE="LCD_I2C_ADAFRUIT"
		I2C_ADDRESS="0x20"
		I2C_REQUIRED=1
		DESC="LCD with Adafruit (MCP23017) backpack"

	elif [[ ${ans} == '4' ]]; then
		DISPLAY_TYPE="LCD_ADAFRUIT_RGB"
		I2C_ADDRESS="0x20"
		I2C_REQUIRED=1
		DESC="Adafruit RGB LCD plate with 5 push buttons" 

	elif [[ ${ans} == '5' ]]; then
		DISPLAY_TYPE="GRAPHICAL"
		DESC="HDMI or touch screen display"
		LINES=0
		WIDTH=0

	elif [[ ${ans} == '6' ]]; then
		DISPLAY_TYPE="OLED_128x64"
		I2C_ADDRESS="0x3C"
		I2C_REQUIRED=1
		DESC="Olimex 128x64 pixel OLED display"
		LINES=5
		WIDTH=20

	elif [[ ${ans} == '7' ]]; then
		DISPLAY_TYPE="NO_DISPLAY"
		DESC="No display used"

	else
		DESC="Display type unchanged"
		echo ${DESC}

	fi

	whiptail --title "$DESC" --yesno "Is this correct?" 10 60
	selection=$?
done 


if [[ ${I2C_REQUIRED} != 0 ]]; then
	# Select the I2C address
	ans=0
	selection=1 
	while [ $selection != 0 ]
	do
		ans=$(whiptail --title "Select I2C hex address" --menu "Choose your option" 15 75 9 \
		"1" "Hex 0x20 (Adafruit devices)" \
		"2" "Hex 0x27 (PCF8574 devices)" \
		"3" "Hex 0x37 (PCF8574 devices alternative address)" \
		"4" "Hex 0x3C (Olimex OLED with Cosmic controller)" \
		"5" "Manually configure i2c_address in ${CONFIG}" \
		"6" "Do not change configuration" 3>&1 1>&2 2>&3) 

		exitstatus=$?
		if [[ $exitstatus != 0 ]]; then
			exit 0
		fi

		if [[ ${ans} == '1' ]]; then
			DESC="Hex 0x20 selected"
			I2C_ADDRESS="0x20"

		elif [[ ${ans} == '2' ]]; then
			DESC="Hex 0x27 selected"
			I2C_ADDRESS="0x27"

		elif [[ ${ans} == '3' ]]; then
			DESC="Hex 0x37 selected"
			I2C_ADDRESS="0x37"

		elif [[ ${ans} == '4' ]]; then
			DESC="Hex 0x3C selected"
			I2C_ADDRESS="0x3C"

		elif [[ ${ans} == '5' ]]; then
			DESC="Manually configure i2c_address in ${CONFIG} "
			echo ${DESC}

		else
			echo "Wiring configuration in ${CONFIG} unchanged"	
		fi

		whiptail --title "$DESC" --yesno "Is this correct?" 10 60
		selection=$?
	done

	echo
	echo "The selected display interface type requires the"
	echo "I2C kernel libraries to be loaded at boot time."
	echo "The program will call the raspi-config program"
	echo "Select the following options on the next screens:"
	echo "   1 Enable I2C libraries radio"
	echo "   5 Interfacing options"
 	echo "   P5 Enable/Disable automatic loading of I2C kernel module"
	echo; echo -n "Press enter to continue: "

	 read ans

	# Enable the I2C libraries 
	ans=0
	ans=$(whiptail --title "Enable I2C interface" --menu "Choose your option" 15 75 9 \
	"1" "Enable I2C libraries " \
	"2" "Do not change configuration" 3>&1 1>&2 2>&3) 

	exitstatus=$?
	if [[ $exitstatus != 0 ]]; then
		exit 0
	fi

	if [[ ${ans} == '1' ]]; then
		sudo raspi-config
	else
		echo "I2C configuration unchanged"	
	fi

	if [[ ${ans} == '1' ]]; then
		echo "The selected interface requires the Python I2C libraries"
		echo "It is necessary to install the python-smbus library"
		echo "After this program finishes carry out the following command:"
		echo "   sudo apt-get install python-smbus"
		echo "and reboot the system."
		echo; echo -n "Press enter to continue: "
	fi
fi

# Select the display type (Lines and Width)
if [[ ${DISPLAY_TYPE} != "GRAPHICAL" ]]; then
	ans=0
	selection=1 
	while [ $selection != 0 ]
	do
		ans=$(whiptail --title "Select display type" --menu "Choose your option" 15 75 9 \
		"1" "Four line 20 character LCD" \
		"2" "Four line 16 character LCD" \
		"3" "Two line 16 character LCD" \
		"4" "Two line 8 character LCD" \
		"5" "Olimex 128x64 pixel OLED" \
		"6" "Do not change display type" 3>&1 1>&2 2>&3) 

		exitstatus=$?
		if [[ $exitstatus != 0 ]]; then
			exit 0
		fi

		if [[ ${ans} == '1' ]]; then
			DESC="Four line 20 character LCD" 
			LINES=4;WIDTH=20

		elif [[ ${ans} == '2' ]]; then
			DESC="Four line 16 character LCD" 
			LINES=4;WIDTH=16

		elif [[ ${ans} == '3' ]]; then
			DESC="Two line 16 character LCD" 
			LINES=2;WIDTH=16

		elif [[ ${ans} == '4' ]]; then
			DESC="Two line 8 character LCD" 
			LINES=2;WIDTH=8

		elif [[ ${ans} == '5' ]]; then
			DESC="Olimex 128x64 OLED display" 
			LINES=5;WIDTH=20

		else
			echo "Wiring configuration in ${CONFIG} unchanged"	
		fi

		whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
		selection=$?
	done
else
	# Configure graphical display
	ans=0
	selection=1 
	while [ $selection != 0 ]
	do
		ans=$(whiptail --title "Select graphical display type?" --menu "Choose your option" 15 75 9 \
		"1" "Raspberry Pi 7 inch touch-screen (800x480)" \
		"2" "Adafruit 3.5 inch TFT touch-screen (720x480)" \
		"3" "HDMI television or monitor (800x480)" \
		"4" "Do not change configuration" 3>&1 1>&2 2>&3) 

		exitstatus=$?
		if [[ $exitstatus != 0 ]]; then
			exit 0
		fi

		if [[ ${ans} == '1' ]]; then
			DESC="Raspberry Pi 7 inch touch-screen"
			SCREEN_SIZE="800x480"

		elif [[ ${ans} == '2' ]]; then
			DESC="Adafruit 3.5 inch TFT touch-screen"
			SCREEN_SIZE="720x480"

		elif [[ ${ans} == '3' ]]; then
			DESC="HDMI television or monitor"
			SCREEN_SIZE="800x480"

		else
			DESC="Graphical displayn type unchanged"	
			echo {DESC}
			GPROG=""
		fi

		whiptail --title "${DESC} " --yesno "Is this correct?" 10 60
		selection=$?
		
	done
	
	ans=0
	selection=1 
	while [ $selection != 0 ]
	do
		ans=$(whiptail --title "Which type of graphical display?" --menu "Choose your option" 15 75 9 \
		"1" "Full feature radio" \
		"2" "Vintage look-alike (Radio only)" \
		"3" "Do not change configuration" 3>&1 1>&2 2>&3) 

		exitstatus=$?
		if [[ $exitstatus != 0 ]]; then
			exit 0
		fi

		if [[ ${ans} == '1' ]]; then
			DESC="Full feature radio"
			GPROG="gradio"

		elif [[ ${ans} == '2' ]]; then
			DESC="Vintage look-alike (Radio only)"
			GPROG="vgradio"

		else
			DESC="Graphical display unchanged"	
			echo {DESC}
			GPROG=""
		fi

		whiptail --title "${DESC} " --yesno "Is this correct?" 10 60
		selection=$?
		
	done
	
	if [[ ${GPROG}  != "" ]];then
		PROGRAM="Graphical/touch-screen program ${GPROG} configured"
	else
		PROGRAM="Graphical/touch-screen program unchanged"
	fi

	# Set up boot option for graphical radio
	ans=0
	selection=1 
	while [ $selection != 0 ]
	do
		ans=$(whiptail --title "Boot option" --menu "Choose your option" 15 75 9 \
		"1" "Start radio at boot time" \
		"2" "Do not start at boot time" \
		"3" "Do not change configuration" 3>&1 1>&2 2>&3) 

		exitstatus=$?
		if [[ $exitstatus != 0 ]]; then
			exit 0
		fi

		if [[ ${ans} == '1' ]]; then
			DESC="Start radio at boot time" 
			LXSESSION="yes"

		elif [[ ${ans} == '2' ]]; then
			DESC="Do not start radio at boot time" 
			LXSESSION="no"

		else
			echo "Boot configuration unchanged"	
		fi

		whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
		selection=$?
	done

	ans=0
	selection=1 
	while [ $selection != 0 ]
	do
		ans=$(whiptail --title "Full screen option" --menu "Choose your option" 15 75 9 \
		"1" "Start graphical radio full screen" \
		"2" "Start graphical radio in a desktop window" \
		"3" "Do not change configuration" 3>&1 1>&2 2>&3) 

		exitstatus=$?
		if [[ $exitstatus != 0 ]]; then
			exit 0
		fi

		if [[ ${ans} == '1' ]]; then
			DESC="Start graphical radio full screen"
			FULLSCREEN="yes"

		elif [[ ${ans} == '2' ]]; then
			DESC="Do not start radio at boot time" 
			FULLSCREEN="no"

		else
			echo "Desktop configuration unchanged"	
		fi

		whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
		selection=$?
	done

	echo "Desktop program ${GPROG}.py configured"
fi

# Configure desktop autostart
cmd="@sudo /usr/share/radio/${GPROG}.py"
AUTOSTART="/home/pi/.config/lxsession/LXDE-pi/autostart"
if [[ ${LXSESSION} == "yes" ]]; then
	# Delete old entry if it exists
	sudo sed -i -e "/radio/d" ${AUTOSTART}
	echo "Configuring ${AUTOSTART} for automatic start"
	sudo echo ${cmd} | sudo tee -a  ${AUTOSTART}
#elif [[ ${LXSESSION} == "no" ]]; then
else
	sudo sed -i -e "/radio/d" ${AUTOSTART}
fi


#######################################
# Commit changes to radio config file #
#######################################

# Save original configuration file
if [[ ! -f ${CONFIG}.org ]]; then
	sudo cp ${CONFIG} ${CONFIG}.org
	echo "Original ${CONFIG} copied to ${CONFIG}.org"
fi

# Configure display width and lines
if [[ $DISPLAY_TYPE != "" ]]; then
	sudo sed -i -e "0,/^display_type/{s/display_type.*/display_type=${DISPLAY_TYPE}/}" ${CONFIG}
	sudo sed -i -e "0,/^display_lines/{s/display_lines.*/display_lines=${LINES}/}" ${CONFIG}
	sudo sed -i -e "0,/^display_width/{s/display_width.*/display_width=${WIDTH}/}" ${CONFIG}
fi

# Set up graphical screen size
if [[ $DISPLAY_TYPE == "GRAPHICAL" ]]; then
	sudo sed -i -e "0,/^screen_size/{s/screen_size.*/screen_size=${SCREEN_SIZE}/}" ${CONFIG}
fi

# Configure user interface (Buttons or Rotary encoders)
if [[ ${USER_INTERFACE} == "1" ]]; then
	sudo sed -i -e "0,/^user_interface/{s/user_interface.*/user_interface=buttons/}" ${CONFIG}

elif [[ ${USER_INTERFACE} == "2" ]]; then
	sudo sed -i -e "0,/^user_interface/{s/user_interface.*/user_interface=rotary_encoder/}" ${CONFIG}

elif [[ ${USER_INTERFACE} == "3" ]]; then
	sudo sed -i -e "0,/^user_interface/{s/user_interface.*/user_interface=graphical/}" ${CONFIG}

elif [[ ${USER_INTERFACE} == "4" ]]; then
	sudo sed -i -e "0,/^user_interface/{s/user_interface.*/user_interface=cosmic_controller/}" ${CONFIG}
fi

# Configure user interface (Buttons or Rotary encoders)
if [[ ${I2C_ADDRESS} != "0x00" ]]; then
	sudo sed -i -e "0,/^i2c_address/{s/i2c_address.*/i2c_address=${I2C_ADDRESS}/}" ${CONFIG}
fi

# Configure wiring for directly connected LCD displays
if [[ ${WIRING_TYPE} == "1" ]]; then
	echo "Configuring 40 Pin wiring" 
	# Switches
	sudo sed -i -e "0,/^menu_switch=/{s/menu_switch=.*/menu_switch=17/}" ${CONFIG}
	sudo sed -i -e "0,/^mute_switch/{s/mute_switch.*/mute_switch=4/}" ${CONFIG}
	sudo sed -i -e "0,/^up_switch/{s/up_switch.*/up_switch=24/}" ${CONFIG}
	sudo sed -i -e "0,/^down_switch/{s/down_switch.*/down_switch=23/}" ${CONFIG}
	sudo sed -i -e "0,/^left_switch/{s/left_switch.*/left_switch=14/}" ${CONFIG}
	sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=15/}" ${CONFIG}
	# LCD pinouts
	sudo sed -i -e "0,/^lcd_select/{s/lcd_select.*/lcd_select=7/}" ${CONFIG}
	sudo sed -i -e "0,/^lcd_enable/{s/lcd_enable.*/lcd_enable=8/}" ${CONFIG}
	sudo sed -i -e "0,/^lcd_data4/{s/lcd_data4.*/lcd_data4=5/}" ${CONFIG}
	sudo sed -i -e "0,/^lcd_data5/{s/lcd_data5.*/lcd_data5=6/}" ${CONFIG}
	sudo sed -i -e "0,/^lcd_data6/{s/lcd_data6.*/lcd_data6=12/}" ${CONFIG}
	sudo sed -i -e "0,/^lcd_data7/{s/lcd_data7.*/lcd_data7=13/}" ${CONFIG}

elif [[ ${WIRING_TYPE} == "2" ]]; then
	echo "Configuring 26 Pin wiring" 
	# Switches
	sudo sed -i -e "0,/^menu_switch=/{s/menu_switch=.*/menu_switch=25/}" ${CONFIG}
	sudo sed -i -e "0,/^mute_switch/{s/mute_switch.*/mute_switch=4/}" ${CONFIG}
	sudo sed -i -e "0,/^up_switch/{s/up_switch.*/up_switch=17/}" ${CONFIG}
	sudo sed -i -e "0,/^down_switch/{s/down_switch.*/down_switch=${DOWN_SWITCH}/}" ${CONFIG}
	sudo sed -i -e "0,/^left_switch/{s/left_switch.*/left_switch=14/}" ${CONFIG}
	sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=15/}" ${CONFIG}
	# LCD pinouts
	sudo sed -i -e "0,/^lcd_select/{s/lcd_select.*/lcd_select=7/}" ${CONFIG}
	sudo sed -i -e "0,/^lcd_enable/{s/lcd_enable.*/lcd_enable=8/}" ${CONFIG}
	sudo sed -i -e "0,/^lcd_data4/{s/lcd_data4.*/lcd_data4=27/}" ${CONFIG}
	sudo sed -i -e "0,/^lcd_data5/{s/lcd_data5.*/lcd_data5=22/}" ${CONFIG}
	sudo sed -i -e "0,/^lcd_data6/{s/lcd_data6.*/lcd_data6=23/}" ${CONFIG}
	sudo sed -i -e "0,/^lcd_data7/{s/lcd_data7.*/lcd_data7=24/}" ${CONFIG}

elif [[ ${WIRING_TYPE} == "3" ]]; then
	echo "Configuring Cosmic Controller Pin wiring" 
	# Switches
	sudo sed -i -e "0,/^menu_switch/{s/menu_switch.*/menu_switch=5/}" ${CONFIG}
	sudo sed -i -e "0,/^mute_switch/{s/mute_switch.*/mute_switch=27/}" ${CONFIG}
	sudo sed -i -e "0,/^up_switch/{s/up_switch.*/up_switch=6/}" ${CONFIG}
	sudo sed -i -e "0,/^down_switch/{s/down_switch.*/down_switch=4/}" ${CONFIG}
	sudo sed -i -e "0,/^left_switch/{s/left_switch.*/left_switch=23/}" ${CONFIG}
	sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=24/}" ${CONFIG}
	# Configure status LEDs
	sudo sed -i -e "0,/^rgb_red/{s/rgb_red.*/rgb_red=14/}" ${CONFIG}
	sudo sed -i -e "0,/^rgb_green/{s/rgb_green.*/rgb_green=15/}" ${CONFIG}
	sudo sed -i -e "0,/^rgb_blue/{s/rgb_blue.*/rgb_blue=16/}" ${CONFIG}
else
	echo "No changes to display and switch wiring configuration" 

fi

#####################
# Summarise changes #
#####################

echo "Changes written to ${CONFIG}"
if [[ ${USER_INTERFACE} != "0" ]]; then
	echo $(grep "^user_interface=" ${CONFIG} )
fi

if [[ $DISPLAY_TYPE != "" ]]; then
	echo $(grep "^display_type=" ${CONFIG} )
	echo $(grep "^display_lines=" ${CONFIG} )
	echo $(grep "^display_width=" ${CONFIG} )
fi

if [[ ${DISPLAY_TYPE} == "GRAPHICAL" ]]; then
	echo $(grep "^screen_size=" ${CONFIG} )
fi

if [[ ${WIRING_TYPE} != "0" ]]; then
	echo $(grep "^lcd_=" ${CONFIG} )
	wiring=$(grep "^[a-z]*_switch=" ${CONFIG} )
	for item in ${wiring}
	do
		echo $item
	done
fi

# Update the System V init script
DAEMON="radiod.py"
sudo sed -i "s/^NAME=.*/NAME=${DAEMON}/g" ${INIT}

# Update systemd script
echo
echo "Updating systemd script"
sudo sed -i "s/^ExecStart=.*/ExecStart=${BINDIR}${DAEMON} nodaemon/g" ${SERVICE}
sudo sed -i "s/^ExecStop=.*/ExecStop=${BINDIR}${DAEMON} stop/g" ${SERVICE}

echo
# Update system startup 
if [[ ${DISPLAY_TYPE} == "GRAPHICAL" ]]; then

	# Set up desktop radio execution icon
	sudo cp ${DIR}/Desktop/gradio.desktop /home/pi/Desktop/.
	sudo cp ${DIR}/Desktop/vgradio.desktop /home/pi/Desktop/.


	# Add [SCREEN] section to the configuration file
	grep "\[SCREEN\]" ${CONFIG} >/dev/null 2>&1
	if [[ $? != 0 ]]; then	# Don't seperate from above
		echo "Adding [SCREEN] section to ${CONFIG}"
		sudo cat ${DIR}/gradio.conf | sudo tee -a ${CONFIG}
	fi
	sudo systemctl daemon-reload
	cmd="sudo systemctl disable radiod.service"
	echo ${cmd}; ${cmd}  >/dev/null 2>&1

	# Set fullscreen option (Graphical radio version only)
	if [[ ${FULLSCREEN} != "" ]]; then
		sudo sed -i -e "0,/^fullscreen/{s/fullscreen.*/fullscreen=${FULLSCREEN}/}" ${CONFIG}
		echo "fullscreen=${FULLSCREEN}"
	fi

# Enable  radio daemon to start radiod
elif [[ ${DISPLAY_TYPE} =~ "LCD" ]]; then
	if [[ -x /bin/systemctl ]]; then
		sudo systemctl daemon-reload
		cmd="sudo systemctl enable radiod.service"
		echo ${cmd}; ${cmd} >/dev/null 2>&1
	else
		sudo update-rc.d radiod enable
	fi
fi

echo ${PROGRAM};echo

# Configure audio device
ans=0
ans=$(whiptail --title "Configure audio interface?" --menu "Choose your option" 15 75 9 \
"1" "Run audio configuration program (configure_audio.sh)" \
"2" "Do not change configuration" 3>&1 1>&2 2>&3) 

exitstatus=$?
if [[ $exitstatus != 0 ]]; then
	exit 0
fi

if [[ ${ans} == '1' ]]; then
	sudo ${DIR}/configure_audio.sh ${FLAGS}
else
	echo "Audio configuration unchanged"	
fi

echo "Reboot Raspberry Pi to enable changes"
exit 0

# End of configuration script

