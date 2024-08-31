#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: configure_radio.sh,v 1.46 2024/08/23 14:26:18 bob Exp $
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
#        The authors shall not be liable for any loss or damage however caused.
#
# This program uses whiptail. Set putty terminal to use UTF-8 charachter set
# for best results
# Warning: whiptail overwrites the LINES variable previously used in this script. Use DLINES

# If -s flag specified (See piradio.postinst script)
FLAGS=$1

SERVICE=/lib/systemd/system/radiod.service
BINDIR="\/usr\/share\/radio\/"  # Used for sed so \ needed
DIR=/usr/share/radio

# Development directory
if [[ ! -d ${DIR} ]];then
    echo "Fatal error: radiod package not installed!"
    exit 1
fi

# Version 7.5 onwards allows any user with sudo permissions to install the software
USR=$(logname)
GRP=$(id -g -n ${USR})

OS_RELEASE=/etc/os-release
LOGDIR=${DIR}/logs
CONFIG=/etc/radiod.conf
BOOTCONFIG=/boot/config.txt
BOOTCONFIG_2=/boot/firmware/config.txt
ETCMODULES=/etc/modules
MPDCONF=/etc/mpd.conf
WXCONFIG=/etc/weather.conf
LOG=${LOGDIR}/install.log
SPLASH="bitmaps\/raspberry-pi-logo.bmp" # Used for sed so \ needed

LXSESSION=""    # Start desktop radio at boot time
FULLSCREEN=""   # Start graphic radio fullscreen
SCREEN_SIZE="800x480"   # Screen size 800x480, 720x480 or 480x320
PROGRAM="Daemon radiod configured"
GPROG=""    # Which graphical radio (gradio or vgradio)
FLIP_OLED_DISPLAY=0 # 1 = Flip OLED idisplay upside down

declare -i PI_MODEL=0  # 0=Undefined 5=Model 5 4=Model 4 or less

# Wiring type and schemes
BUTTON_WIRING=0 # 0 Not used or SPI/I2C, 1=Buttons, 2=Rotary encoders, 3=PHat BEAT
LCD_WIRING=0    # 0 not used, 1=standard LCD wiring, 
GPIO_PINS=0 # 0 Not configured, 1=40 pin wiring,2=26 pin,3=I2C Rotary
PULL_UP_DOWN=0  # Pull up/down resistors 1=Up, 0=Down
USER_INTERFACE=0    # 0 Not configured, 1=Buttons, 2=Rotary encoders, 3=HDMI/Touch-screen
            # 4=IQaudIO(I2C), 5=Pimoroni pHAT(SPI), 6=Adafruit RGB(I2C),
            # 7=PiFace CAD, 8=Pirate Audio, 9=pHat with 3 buttons and joystick 
# Display type
DISPLAY_TYPE=""
I2C_REQUIRED=0
I2C_ADDRESS="0x0"
SPI_REQUIRED=0
PIFACE_REQUIRED=0	
SCROLL_SPEED="0.2" 
ROTARY_CLASS="standard"    # Standard abc Rotary Encoders
ROTARY_HAS_RESISTORS=0	# Support for KY-040 or ABC Rotary encoders
ADAFRUIT_SSD1306=0	# Adafruit SSD1306 libraries required

# Display characteristics
I2C_ADDRESS=0x00        # I2C device address
I2C_RGB_ADDRESS=0x00    # I2C RGB device address
DLINES=4            # Number of display lines
DWIDTH=20       # Display character width

# Old wiring down switch
DOWN_SWITCH=10

# Volume sensitivity
VOLUME_RANGE=20

# Date format (Use default in radiod.conf)
DATE_FORMAT=""  

# Get OS release ID
function release_id
{
    VERSION_ID=$(grep VERSION_ID $OS_RELEASE)
    arr=(${VERSION_ID//=/ })
    ID=$(echo "${arr[1]}" | tr -d '"')
    ID=$(expr ${ID} + 0)
    echo ${ID}
}

# Get OS release name
function codename
{
    VERSION_CODENAME=$(grep VERSION_CODENAME $OS_RELEASE)
    arr=(${VERSION_CODENAME//=/ })
    CODENAME=$(echo "${arr[1]}" | tr -d '"')
    echo ${CODENAME}
}

# Create log directory
sudo mkdir -p ${LOGDIR}
sudo chown ${USR}:${GRP} ${LOGDIR}

sudo rm -f ${LOG}
echo "$0 configuration log, $(date) " | tee ${LOG}

# In Bookworm (Release ID 12) the configuration has been moved to /boot/firmware/config.txt
if [[ $(release_id) -ge 12 ]]; then
    BOOTCONFIG=${BOOTCONFIG_2}
fi

echo "Boot configuration in ${BOOTCONFIG}" | tee -a ${LOG}

# Copy weather configuration file to /etc
if [[ ! -f   ${WXCONFIG} ]]; then
    sudo cp -f ${DIR}/weather.conf ${WXCONFIG}
fi

# Replace /etc/mpd.conf if corrupt
grep ^audio_out /etc/mpd.conf >/dev/null 2>&1
if [[ $? != 0 ]]; then
    echo "Replacing corrupt ${MPDCONF} with ${DIR}/mpd.conf"
    sudo cp ${DIR}/mpd.conf ${MPDCONF}
fi

# Replace /etc/mpd.conf.orig if corrupt
grep ^audio_out /etc/mpd.conf.orig >/dev/null 2>&1
if [[ $? != 0 ]]; then
    echo "Replacing corrupt ${MPDCONF}.orig with ${DIR}/mpd.conf"
    sudo cp ${DIR}/mpd.conf ${MPDCONF}.orig
fi

# Check if user wants to configure radio if upgrading
if [[ -f ${CONFIG}.org ]]; then
    ans=0
    ans=$(whiptail --title "Upgrading, Re-configure radio?" --menu "Choose your option" 15 75 9 \
    "1" "Run radio configuration?" \
    "2" "Do not change configuration?" 3>&1 1>&2 2>&3) 

    exitstatus=$?
    if [[ $exitstatus != 0 ]] || [[ ${ans} == '2' ]]; then
        echo "Current configuration in ${CONFIG} unchanged" | tee -a ${LOG}
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
    echo "Existing configuration  copied to ${CONFIG}.save" | tee -a ${LOG}
    sudo cp ${DIR}/radiod.conf ${CONFIG}
    echo "Current configuration ${CONFIG} replaced with distribution" | tee -a ${LOG}
fi

# Select Raspberry Pi model  
ans=0
selection=1 
while [ $selection != 0 ]
do
    ans=$(whiptail --title "Select Raspberry Pi Model" --menu "Choose your option" 15 75 9 \
    "1" "Raspberry Pi Model 5" \
    "2" "Raspberry Pi Model 4 or earlier" \
    "3" "Do not change configuration" 3>&1 1>&2 2>&3) 

    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
        exit 0
    fi

    if [[ ${ans} == '1' ]]; then
        DESC="Raspberry Pi Model 5 selected"
        PI_MODEL=5

    elif [[ ${ans} == '2' ]]; then
        DESC="Raspberry Pi Model 4 or earlier"
        PI_MODEL=4

    else
        DESC="Raspberry Pi model unchanged"  
        echo ${DESC} | tee -a ${LOG}
    fi

    whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
    selection=$?
done
echo ${DESC} | tee -a ${LOG}


# Select the user interface (Buttons or Rotary encoders)
ans=0
selection=1 
while [ $selection != 0 ]
do
    ans=$(whiptail --title "Select user interface" --menu "Choose your option" 15 75 9 \
    "1" "Push button directly connected to GPIO pins" \
    "2" "Radio with Rotary Encoders" \
    "3" "Mouse or touch screen only" \
    "4" "IQAudio Cosmic Controller" \
    "5" "Pimoroni pHat BEAT with own push buttons" \
    "6" "Adafruit RGB plate with own push buttons" \
    "7" "PiFace CAD with own push buttons" \
    "8" "Pimoroni Audio with four push buttons" \
    "9" "Hat with 1.3\" OLED 3 x push buttons and joystick" \
    "10" "Do not change configuration" 3>&1 1>&2 2>&3) 

    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
        exit 0
    fi

    if [[ ${ans} == '1' ]]; then
        DESC="Push buttons selected"
        USER_INTERFACE=1
        BUTTON_WIRING=1

    elif [[ ${ans} == '2' ]]; then
        DESC="Rotary encoders selected"
        USER_INTERFACE=2
        BUTTON_WIRING=2
        PULL_UP_DOWN=1

    elif [[ ${ans} == '3' ]]; then
        DESC="HDMI or touch screen only"
        USER_INTERFACE=3

    elif [[ ${ans} == '4' ]]; then
        DESC="IQAudio Cosmic Controller"
        USER_INTERFACE=4
        BUTTON_WIRING=3
        PULL_UP_DOWN=1

    elif [[ ${ans} == '5' ]]; then
        DESC="Pimoroni pHat BEAT with buttons"
        USER_INTERFACE=5
        BUTTON_WIRING=4
        PULL_UP_DOWN=1

    elif [[ ${ans} == '6' ]]; then
        DESC="Adafruit RGB plate with buttons"
        USER_INTERFACE=6
        I2C_REQUIRED=1
        I2C_ADDRESS="0x20"

    elif [[ ${ans} == '7' ]]; then
        DESC="PiFace CAD with buttons"
        USER_INTERFACE=7
        SPI_REQUIRED=1
        PIFACE_REQUIRED=1
        GPIO_PINS=1

    elif [[ ${ans} == '8' ]]; then
        DESC="Pimoroni Audio with four push buttons"
        USER_INTERFACE=8
        GPIO_PINS=1
        BUTTON_WIRING=5
        PULL_UP_DOWN=1

    elif [[ ${ans} == '9' ]]; then
        DESC="1.3\" OLED with joystick and 3 buttons"
        USER_INTERFACE=9
        GPIO_PINS=1
        BUTTON_WIRING=6
        PULL_UP_DOWN=1
    else
        DESC="User interface in ${CONFIG} unchanged"    
        echo ${DESC} | tee -a ${LOG}
    fi

    whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
    selection=$?
done

# Check how push-buttons are wired
if [[ ${USER_INTERFACE} == "1" ]]; then
    ans=0
    selection=1 
    while [ $selection != 0 ]
    do
        ans=$(whiptail --title "How are the push buttons wired?" --menu "Choose your option" 15 75 9 \
        "1" "GPIO --> Button --> +3.3V - Original wiring scheme" \
        "2" "GPIO --> Button --> GND(0V) - Alternative wiring scheme" \
        "3" "Do not change configuration" 3>&1 1>&2 2>&3) 

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            exit 0
        fi

        if [[ ${ans} == '1' ]]; then
            DESC="Buttons wired to +3.3V (GPIO low to high)"
            PULL_UP_DOWN=0

        elif [[ ${ans} == '2' ]]; then
            DESC="Buttons wired to GND(0V) (GPIO high to low)"
            PULL_UP_DOWN=1

        else
            DESC="Wiring configuration in ${CONFIG} unchanged"  
            echo ${DESC} | tee -a ${LOG}
        fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
    done
    echo ${DESC} | tee -a ${LOG}
fi

# Configure pull-up resistors for type of rotary encoder
if [[ ${USER_INTERFACE} == "2" ]]; then
    ans=0
    selection=1 
    while [ $selection != 0 ]
    do
        ROTARY_CLASS="standard"

        ans=$(whiptail --title "Select type of rotary encoder" --menu "Choose your option" 15 75 9 \
        "1" "Standard rotary encoders with A, B and C inputs only" \
        "2" "Rotary encoders encoders (eg KY-040) with own pull-up resistors" \
        "3" "Rotary encoders with RGB LEDs" \
        "4" "I2C Rotary encoders with RGB LEDs" \
        "5" "Standard A,B,C rotary encoders alternative driver" \
        "6" "Not sure" 3>&1 1>&2 2>&3) 

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            exit 0
        fi

        if [[ ${ans} == '1' ]]; then
            DESC="Configuring standard rotary encoders"

        elif [[ ${ans} == '2' ]]; then
            DESC="Configuring rotary encoders (eg. KY-040) with own pull-up resistors"
            ROTARY_HAS_RESISTORS=1

        elif [[ ${ans} == '3' ]]; then
            DESC="Configuring rotary encoders with RGB LEDs"
            ROTARY_HAS_RESISTORS=1
            ROTARY_CLASS="rgb_rotary"

        elif [[ ${ans} == '4' ]]; then
            DESC="Configuring I2C rotary encoders with RGB LEDs"
            ROTARY_CLASS="rgb_i2c_rotary"
            GPIO_PINS=3

        elif [[ ${ans} == '5' ]]; then
            DESC="Standard rotary encoders alternative driver"
            ROTARY_HAS_RESISTORS=1
            ROTARY_CLASS="alternative"

        else
            DESC="Standard rotary encoders"  
            echo ${DESC} | tee -a ${LOG}
        fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
    done
    echo ${DESC} | tee -a ${LOG}
fi
# Select the wiring type (40 or 26 pin) if not already specified
if [[ ${GPIO_PINS} == "0" ]]; then
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
            GPIO_PINS=1

        elif [[ ${ans} == '2' ]]; then
            DESC="26 pin version selected"
            GPIO_PINS=2

        else
            DESC="Wiring configuration in ${CONFIG} unchanged"  
            echo ${DESC} | tee -a ${LOG}
        fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
    done
    echo ${DESC} | tee -a ${LOG}
fi


# Configure the down switch (24 pin wiring)
if [[ ${GPIO_PINS} == "2" ]]; then
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
            echo ${DESC} | tee -a ${LOG}
        fi

        whiptail --title "${DESC} " --yesno "Is this correct?" 10 60
        selection=$?
    done
fi 


# Select the display type
ans=0
selection=1 
while [ $selection != 0 ]
do
    ans=$(whiptail --title "Select display type" --menu "Choose your option" 15 75 9 \
    "1" "LCD wired directly to GPIO pins" \
    "2" "LCD with Arduino (PCF8574) backpack" \
    "3" "LCD with Adafruit (MCP23017) backpack" \
    "4" "Adafruit RGB LCD plate with 5 push buttons" \
    "5" "HDMI or touch screen display" \
    "6" "Olimex 128x64 pixel OLED display" \
    "7" "PiFace CAD display" \
    "8" "Pimoroni Audio ST7789 TFT" \
    "9" "Sitronix SSD1306 128x64 monochrome OLED" \
    "10" "OLEDs using LUMA driver (SSD1306,SH1106 etc)" \
    "11" "Grove LCD RGB JHD1313 (AIP31068L controller)" \
    "12" "Grove LCD RGB JHD1313 (SGM31323 controller)" \
    "13" "OLEDs using SH1106 SPI interface, buttons & joystick" \
    "14" "No display used/Pimoroni Pirate radio" \
    "15" "Do not change display type" 3>&1 1>&2 2>&3) 

    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
        exit 0
    fi

    if [[ ${ans} == '1' ]]; then
        DISPLAY_TYPE="LCD"
        LCD_WIRING=1
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
        DLINES=0
        DWIDTH=0

    elif [[ ${ans} == '6' ]]; then
        DISPLAY_TYPE="OLED_128x64"
        I2C_ADDRESS="0x3C"
        I2C_REQUIRED=1
        DESC="Olimex 128x64 pixel OLED display"
        VOLUME_RANGE=10
        DATE_FORMAT="%H:%M %d%m"
        DLINES=5
        DWIDTH=20

    elif [[ ${ans} == '7' ]]; then
        DISPLAY_TYPE="PIFACE_CAD"
        DESC="PiFace CAD display"
        VOLUME_RANGE=10
        DLINES=2
        DWIDTH=16
        SPI_REQUIRED=1
        PIFACE_REQUIRED=1

    elif [[ ${ans} == '8' ]]; then
        DISPLAY_TYPE="ST7789TFT"
        DESC="Pimoroni Audio ST7789 TFT"
        VOLUME_RANGE=10
        DLINES=6
        DWIDTH=16
        SPLASH="images\/raspberrypi.png"
        SPI_REQUIRED=1

    elif [[ ${ans} == '9' ]]; then
        DISPLAY_TYPE="SSD1306"
        DESC="128x64 OLED with SSD1306 SPI interface"
        DLINES=4
        DWIDTH=16
        VOLUME_RANGE=10
        SPI_REQUIRED=1
        SPLASH="images\/raspberrypi.png"

    elif [[ ${ans} == '10' ]]; then
        DISPLAY_TYPE="LUMA"
        DESC="OLEDs using LUMA driver"
        DLINES=4
        DWIDTH=16
        VOLUME_RANGE=10
        I2C_REQUIRED=1
        I2C_ADDRESS="0x3C"
        SPLASH="images\/raspberrypi.png"

    elif [[ ${ans} == '11' ]]; then
        DISPLAY_TYPE="LCD_I2C_JHD1313"
        I2C_ADDRESS="0x3e"
        I2C_RGB_ADDRESS="0x30"
        I2C_REQUIRED=1
        DLINES=2
        DWIDTH=16
        DESC="Grove JHD1313LCD RGB LCD"

    elif [[ ${ans} == '12' ]]; then
        DISPLAY_TYPE="LCD_I2C_JHD1313_SGM31323"
        I2C_ADDRESS="0x3e"
        I2C_RGB_ADDRESS="0x30"
        I2C_REQUIRED=1
        DLINES=2
        DWIDTH=16
        DESC="Grove JHD1313 SGM31323 RGB LCD"

    elif [[ ${ans} == '13' ]]; then
        DISPLAY_TYPE="SH1106_SPI"
        DESC="OLED using SH1106 SPI interface"
        DLINES=4
        DWIDTH=16
        VOLUME_RANGE=20
        SPI_REQUIRED=1
        SPLASH="bitmaps\/raspberry-pi-logo.bmp" 

    elif [[ ${ans} == '14' ]]; then
        DISPLAY_TYPE="NO_DISPLAY"
        DLINES=0
        DWIDTH=0
        DESC="No display used"

    else
        DESC="Display type unchanged"
        echo ${DESC} | tee -a ${LOG}

    fi

    whiptail --title "$DESC" --yesno "Is this correct?" 10 60
    selection=$?
done 

if [[ ${DISPLAY_TYPE} == "LUMA" ]]; then
    ans=0
    selection=1 
    while [ $selection != 0 ]
    do
        ans=$(whiptail --title "Select LUMA OLED device" --menu "Choose your option" 15 75 9 \
        "1" "SH1106 128x64 monochrome OLED" \
        "2" "SH1106 128x32 monochrome OLED" \
        "3" "SSD1306 128x64 monochrome OLED " \
        "4" "SSD1309 monochrome OLED " \
        "5" "SSD1325 monochrome OLED " \
        "6" "SSD1331 monochrome OLED " \
        "7" "WS0010 monochrome OLED " 3>&1 1>&2 2>&3) 

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            exit 0
        fi

        if [[ ${ans} == '1' ]]; then
            DESC="SH1106 128x64 monochrome OLED"
            DISPLAY_TYPE="${DISPLAY_TYPE}.SH1106"

        elif [[ ${ans} == '2' ]]; then
            DESC="SH1106 128x32 monochrome OLED"
            DISPLAY_TYPE="${DISPLAY_TYPE}.SH1106_128x32"

        elif [[ ${ans} == '3' ]]; then
            DESC="SSD1306 128x64 monochrome OLED"
            DISPLAY_TYPE="${DISPLAY_TYPE}.SSD1306"

        elif [[ ${ans} == '4' ]]; then
            DESC="SSD1309 monochrome OLED"
            DISPLAY_TYPE="${DISPLAY_TYPE}.SSD1309"

        elif [[ ${ans} == '5' ]]; then
            DESC="SSD1325 monochrome OLED"
            DISPLAY_TYPE="${DISPLAY_TYPE}.SSD1325"

        elif [[ ${ans} == '6' ]]; then
            DESC="SSD1331 monochrome OLED"
            DISPLAY_TYPE="${DISPLAY_TYPE}.SSD1331"

        elif [[ ${ans} == '7' ]]; then
            DESC="WS0010 monochrome OLED"
            DISPLAY_TYPE="${DISPLAY_TYPE}.WS0010"
        fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
    done
    echo ${DESC} | tee -a ${LOG}
fi

# Flip display upside down option
if [[ ${DISPLAY_TYPE} == "OLED_128x64" || ${DISPLAY_TYPE} =~ "LUMA" ]]; then
    ans=0
    selection=1 
    while [ $selection != 0 ]
    do
        ans=$(whiptail --title "Flip OLED display upside down " --menu "Choose your option" 15 75 9 \
        "1" "Flip OLED display upside down" \
        "2" "Do not flip OLED display upside down" 3>&1 1>&2 2>&3) 

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            exit 0
        fi

        if [[ ${ans} == '1' ]]; then
            DESC="OLED display flipped upside down"
            FLIP_OLED_DISPLAY=1 # Flip OLED display upside down
        else
            DESC="OLED display NOT flipped upside down"
        fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
    done
    echo ${DESC} | tee -a ${LOG}
fi

if [[ ${SPI_REQUIRED} != 0 ]]; then
        echo | tee -a ${LOG}
        echo "The chosen display (${DESC}) requires the" | tee -a ${LOG}
        echo "SPI kernel module to be loaded at boot time." | tee -a ${LOG}
        echo "The program will call the raspi-config program" | tee -a ${LOG}
        echo "Select the following options on the next screens:" | tee -a ${LOG}
        echo "   5 Interfacing options" | tee -a ${LOG}
        echo "   P4 Enable/Disable automatic loading of SPI kernel module" | tee -a ${LOG}
        echo; echo -n "Press enter to continue: "
        read ans

    exitstatus=$?
    if [[ $exitstatus != 0 ]]; then
        exit 0
    fi

    # Enable the SPI kernel interface 
    ans=0
    ans=$(whiptail --title "Enable SPI interface" --menu "Choose your option" 15 75 9 \
    "1" "Enable SPI Kernel Interface " \
    "2" "Do not change configuration" 3>&1 1>&2 2>&3) 

    # Configure SPI interface for PiFace CAD or ST7889 TFT
    if [[ ${ans} == '1' ]]; then
        sudo raspi-config
    else
        echo "SPI configuration unchanged"   | tee -a ${LOG}
    fi

    if [[ ${PIFACE_REQUIRED} == '1' ]]; then
        echo "The selected interface requires the PiFace CAD Python library" | tee -a ${LOG}
        echo "It is necessary to install the python-pifacecad library" | tee -a ${LOG}
        echo "After this program finishes carry out the following command:" | tee -a ${LOG}
        echo "   sudo apt-get install python-pifacecad" | tee -a ${LOG}
        echo "and reboot the system." | tee -a ${LOG}
        echo; echo -n "Press enter to continue: "
        read ans
    fi
fi


if [[ ${SPI_REQUIRED} != 0 ]]; then
    echo "$DESC requires the SPI interface"
    echo "Use sudo raspi-config to enable SPI"
fi

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
        "4" "Hex 0x3F (PCF8574 devices 2nd alternative address)" \
        "5" "Hex 0x3C (Cosmic controller/Sitronix SSD1306/LUMA devices)" \
        "6" "Hex 0x3e (Grove JHD1313 LCD with RGB AIP31068L/SGM31323 controller)" \
        "7" "Manually configure i2c_address in ${CONFIG}" \
        "8" "Do not change configuration" 3>&1 1>&2 2>&3) 

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
            DESC="Hex 0x3F selected"
            I2C_ADDRESS="0x3F"

        elif [[ ${ans} == '5' ]]; then
            DESC="Hex 0x3C selected"
            I2C_ADDRESS="0x3C"

        elif [[ ${ans} == '6' ]]; then
            DESC="Hex 0x3E selected"
            I2C_ADDRESS="0x3E"

        elif [[ ${ans} == '7' ]]; then
            DESC="Manually configure i2c_address in ${CONFIG} "
            echo ${DESC} | tee -a ${LOG}

        else
            echo "Wiring configuration in ${CONFIG} unchanged"   | tee -a ${LOG}
        fi

        whiptail --title "$DESC" --yesno "Is this correct?" 10 60
        selection=$?
    done

        # Update boot config
        echo "Enabling I2C interface in ${BOOTCONFIG}" | tee -a ${LOG}
        sudo sed -i -e "0,/^\#dtparam=i2c_arm/{s/\#dtparam=i2c_arm.*/dtparam=i2c_arm=yes/}" ${BOOTCONFIG}
        grep -q ^i2c-dev ${ETCMODULES}
        if [[ $? -ne 0 ]]; then
            param=i2c-dev
            echo "Adding ${param} to  ${ETCMODULES}"
            echo $param | sudo tee -a ${ETCMODULES} > /dev/null
        fi
fi

# Select the display type (Lines and Width)
if [[ ${DISPLAY_TYPE} =~ "LCD" ]]; then
    ans=0
    selection=1 
    while [ $selection != 0 ]
    do
        ans=$(whiptail --title "Select display type" --menu "Choose your option" 15 75 9 \
        "1" "Four line 20 character LCD" \
        "2" "Four line 16 character LCD" \
        "3" "Two line 16 character LCD/PiFace CAD" \
        "4" "Two line 8 character LCD" \
        "5" "Do not change display type" 3>&1 1>&2 2>&3) 

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            exit 0
        fi

        if [[ ${ans} == '1' ]]; then
            DESC="Four line 20 character LCD" 
            DLINES=4;DWIDTH=20

        elif [[ ${ans} == '2' ]]; then
            DESC="Four line 16 character LCD" 
            DLINES=4;DWIDTH=16

        elif [[ ${ans} == '3' ]]; then
            DESC="Two line 16 character LCD" 
            DLINES=2;DWIDTH=16

        elif [[ ${ans} == '4' ]]; then
            DESC="Two line 8 character LCD" 
            DLINES=2;DWIDTH=8

        else
            echo "Wiring configuration in ${CONFIG} unchanged"   | tee -a ${LOG}
        fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
    done

elif [[ ${DISPLAY_TYPE} == "GRAPHICAL" ]]; then
    # Configure graphical display
    ans=0
    selection=1 
    while [ $selection != 0 ]
    do
        ans=$(whiptail --title "Select graphical display type?" --menu "Choose your option" 15 75 9 \
        "1" "Raspberry Pi 7-inch touch-screen (800x480)" \
        "2" "Medium 3.5 inch TFT touch-screen (720x480)" \
        "3" "Small 2.8 inch TFT touch-screen (480x320)" \
        "4" "7-inch TFT touch-screen (1024x600)" \
        "5" "HDMI television or monitor (800x480)" \
        "6" "Do not change configuration" 3>&1 1>&2 2>&3) 

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            exit 0
        fi

        if [[ ${ans} == '1' ]]; then
            DESC="Raspberry Pi 7 inch touch-screen"
            SCREEN_SIZE="800x480"

        elif [[ ${ans} == '2' ]]; then
            DESC="Medium 3.5 inch TFT touch-screen"
            SCREEN_SIZE="720x480"

        elif [[ ${ans} == '3' ]]; then
            DESC="Small 3.5 inch TFT touch-screen"
            SCREEN_SIZE="480x320"

        elif [[ ${ans} == '4' ]]; then
            DESC="7-inch TFT touch-screen (1024x600)"
            SCREEN_SIZE="1024x600"

        elif [[ ${ans} == '4' ]]; then
            DESC="HDMI television or monitor"
            SCREEN_SIZE="800x480"

        else
            DESC="Graphical display type unchanged"    
            echo ${DESC} | tee -a ${LOG}
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
            echo ${DESC} | tee -a ${LOG}
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
            echo "Boot configuration unchanged"  | tee -a ${LOG}
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
            echo "Desktop configuration unchanged"   | tee -a ${LOG}
        fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
    done

    echo "Desktop program ${GPROG}.py configured" | tee -a ${LOG}
fi

echo "Configuring radio for $(codename) OS " 

# Correct missing autostart file
if [[ $(release_id) -ge 12 ]]; then
    LXDE="LXDE"
else 
    LXDE="LXDE-pi"
fi

LXDE_DIR=/home/${USR}/.config/lxsession/${LXDE}
AUTOSTART="${LXDE_DIR}/autostart"
if [[ ! -d ${LXDE_DIR} ]]; then
    mkdir -p ${LXDE_DIR}
    cp ${DIR}/lxsession/${LXDE}.autostart ${AUTOSTART} 
    chown -R ${USR}:${GRP} /home/${USR}/.config/lxsession
fi

# Configure desktop autostart if X-Windows installed
if [[ -f ${AUTOSTART} ]]; then
    if [[ ${LXSESSION} == "yes" ]]; then
        # Delete old entry if it exists
        sudo sed -i -e "/radio/d" ${AUTOSTART}
        echo "Configuring ${AUTOSTART} for automatic start" | tee -a ${LOG}
	cmd="@sudo /usr/share/radio/${GPROG}.py"
        sudo echo ${cmd} | sudo tee -a  ${AUTOSTART}
    else
        sudo sed -i -e "/radio/d" ${AUTOSTART}
    fi
fi

# Install Adafruit SSD1306 package if required
if [[ ${ADAFRUIT_SSD1306} > 0  ]]; then
    ${DIR}/install_ssd1306.sh | tee -a ${LOG}
fi

#######################################
# Commit changes to radio config file #
#######################################

# Enable GPIO converter module if model is a Raspberry Pi 5 or later or Bookworm OS or later
echo "VERSION_ID"  $(release_id)
if [[ ${PI_MODEL} -ge 5 || $(release_id) -ge 12 ]]; then
    # Enable GPIO converter in ${DIR}/RPi
    touch ${DIR}/RPi/__init__.py | tee -a ${LOG}
    echo "GPIO conversion enabled" | tee -a ${LOG}
else
    # Disable GPIO converter
    rm -f  ${DIR}/RPi/__init__.py | tee -a ${LOG}
    echo "GPIO conversion disabled" | tee -a ${LOG}
fi 

# Save original configuration file
if [[ ! -f ${CONFIG}.org ]]; then
    sudo cp ${CONFIG} ${CONFIG}.org
    echo "Original ${CONFIG} copied to ${CONFIG}.org" | tee -a ${LOG}
fi

# Configure display width and lines
if [[ ${DISPLAY_TYPE} != "" ]]; then
    sudo sed -i -e "0,/^display_type/{s/display_type.*/display_type=${DISPLAY_TYPE}/}" ${CONFIG}
    sudo sed -i -e "0,/^display_lines/{s/display_lines.*/display_lines=${DLINES}/}" ${CONFIG}
    sudo sed -i -e "0,/^display_width/{s/display_width.*/display_width=${DWIDTH}/}" ${CONFIG}
    sudo sed -i -e "0,/^volume_range/{s/volume_range.*/volume_range=${VOLUME_RANGE}/}" ${CONFIG}
    sudo sed -i -e "0,/^scroll_speed/{s/scroll_speed.*/scroll_speed=${SCROLL_SPEED}/}" ${CONFIG}
fi

if [[ $DATE_FORMAT != "" ]]; then
    sudo sed -i -e "0,/^dateformat/{s/dateformat.*/dateformat=${DATE_FORMAT}/}" ${CONFIG}
fi


# Set up graphical screen size
if [[ ${DISPLAY_TYPE} == "GRAPHICAL" ]]; then
    sudo sed -i -e "0,/^screen_size/{s/screen_size.*/screen_size=${SCREEN_SIZE}/}" ${CONFIG}
fi

# Configure user interface
if [[ ${USER_INTERFACE} == "1" || ${USER_INTERFACE} == "8" || ${USER_INTERFACE} == "9" ]]; then
    sudo sed -i -e "0,/^user_interface/{s/user_interface.*/user_interface=buttons/}" ${CONFIG}

elif [[ ${USER_INTERFACE} == "2" ]]; then
    sudo sed -i -e "0,/^user_interface/{s/user_interface.*/user_interface=rotary_encoder/}" ${CONFIG}
    sudo sed -i -e "0,/^rotary_class/{s/rotary_class.*/rotary_class=${ROTARY_CLASS}/}" ${CONFIG}
    if [[ ${ROTARY_HAS_RESISTORS} == 1 ]]; then
        sudo sed -i -e "0,/^rotary_gpio_pullup/{s/rotary_gpio_pullup.*/rotary_gpio_pullup=none/}" ${CONFIG}
    fi

elif [[ ${USER_INTERFACE} == "3" ]]; then
    sudo sed -i -e "0,/^user_interface/{s/user_interface.*/user_interface=graphical/}" ${CONFIG}

elif [[ ${USER_INTERFACE} == "4" ]]; then
    sudo sed -i -e "0,/^user_interface/{s/user_interface.*/user_interface=cosmic_controller/}" ${CONFIG}

elif [[ ${USER_INTERFACE} == "5" ]]; then
    sudo sed -i -e "0,/^user_interface/{s/user_interface.*/user_interface=phatbeat/}" ${CONFIG}

elif [[ ${USER_INTERFACE} == "7" ]]; then
    sudo sed -i -e "0,/^user_interface/{s/user_interface.*/user_interface=pifacecad/}" ${CONFIG}
fi

# Configure I2C address
if [[ ${I2C_ADDRESS} != "0x00" ]]; then
    echo "Configuring I2C address to ${I2C_ADDRESS} (i2c_address)" 
    sudo sed -i -e "0,/^i2c_address/{s/i2c_address.*/i2c_address=${I2C_ADDRESS}/}" ${CONFIG}
fi

# Configure I2C address for RGB LEDs with coulor backlight
if [[ ${I2C_RGB_ADDRESS} != "0x00" ]]; then
    echo "Configuring I2C RGB address to ${I2C_RGB_ADDRESS} (i2c_rgb_address)" 
    sudo sed -i -e "0,/^i2c_rgb_address/{s/i2c_rbb_address.*/i2c_address=${I2C_RGB_ADDRESS}/}" ${CONFIG}
fi

# Configure wiring for directly connected LCD displays
if [[ ${DISPLAY_TYPE} == "LCD" ]]; then
    if [[ ${GPIO_PINS} == "1" ]]; then
        echo "LCD pinouts configured for 40 pin wiring" | tee -a ${LOG}
        sudo sed -i -e "0,/^lcd_select/{s/lcd_select.*/lcd_select=7/}" ${CONFIG}
        sudo sed -i -e "0,/^lcd_enable/{s/lcd_enable.*/lcd_enable=8/}" ${CONFIG}
        sudo sed -i -e "0,/^lcd_data4/{s/lcd_data4.*/lcd_data4=5/}" ${CONFIG}
        sudo sed -i -e "0,/^lcd_data5/{s/lcd_data5.*/lcd_data5=6/}" ${CONFIG}
        sudo sed -i -e "0,/^lcd_data6/{s/lcd_data6.*/lcd_data6=12/}" ${CONFIG}
        sudo sed -i -e "0,/^lcd_data7/{s/lcd_data7.*/lcd_data7=13/}" ${CONFIG}
    else
        echo "LCD pinouts configured for 26 pin wiring" | tee -a ${LOG}
        sudo sed -i -e "0,/^lcd_select/{s/lcd_select.*/lcd_select=7/}" ${CONFIG}
        sudo sed -i -e "0,/^lcd_enable/{s/lcd_enable.*/lcd_enable=8/}" ${CONFIG}
        sudo sed -i -e "0,/^lcd_data4/{s/lcd_data4.*/lcd_data4=27/}" ${CONFIG}
        sudo sed -i -e "0,/^lcd_data5/{s/lcd_data5.*/lcd_data5=22/}" ${CONFIG}
        sudo sed -i -e "0,/^lcd_data6/{s/lcd_data6.*/lcd_data6=23/}" ${CONFIG}
        sudo sed -i -e "0,/^lcd_data7/{s/lcd_data7.*/lcd_data7=24/}" ${CONFIG}
    fi

else
    # LCD not connected 
    echo "LCD pinouts disabled" | tee -a ${LOG}
    sudo sed -i -e "0,/^lcd_select/{s/lcd_select.*/lcd_select=0/}" ${CONFIG}
    sudo sed -i -e "0,/^lcd_enable/{s/lcd_enable.*/lcd_enable=0/}" ${CONFIG}
    sudo sed -i -e "0,/^lcd_data4/{s/lcd_data4.*/lcd_data4=0/}" ${CONFIG}
    sudo sed -i -e "0,/^lcd_data5/{s/lcd_data5.*/lcd_data5=0/}" ${CONFIG}
    sudo sed -i -e "0,/^lcd_data6/{s/lcd_data6.*/lcd_data6=0/}" ${CONFIG}
    sudo sed -i -e "0,/^lcd_data7/{s/lcd_data7.*/lcd_data7=0/}" ${CONFIG}
fi

# Configure buttons and rotary encoders
if [[ ${BUTTON_WIRING} == "1" || ${BUTTON_WIRING} == "2" ]]; then

    if [[ ${GPIO_PINS} == "1" ]]; then
        echo "Configuring 40 Pin wiring"  | tee -a ${LOG}
        sudo sed -i -e "0,/^menu_switch=/{s/menu_switch=.*/menu_switch=17/}" ${CONFIG}
        sudo sed -i -e "0,/^mute_switch/{s/mute_switch.*/mute_switch=4/}" ${CONFIG}
        sudo sed -i -e "0,/^up_switch/{s/up_switch.*/up_switch=24/}" ${CONFIG}
        sudo sed -i -e "0,/^down_switch/{s/down_switch.*/down_switch=23/}" ${CONFIG}
        sudo sed -i -e "0,/^left_switch/{s/left_switch.*/left_switch=14/}" ${CONFIG}
        sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=15/}" ${CONFIG}

    elif [[ ${GPIO_PINS} == "3" ]]; then
        echo "Configuring RGB I2C encoder Pin wiring"  | tee -a ${LOG}
        sudo sed -i -e "0,/^menu_switch=/{s/menu_switch=.*/menu_switch=17/}" ${CONFIG}
        sudo sed -i -e "0,/^mute_switch/{s/mute_switch.*/mute_switch=4/}" ${CONFIG}
        sudo sed -i -e "0,/^up_switch/{s/up_switch.*/up_switch=0/}" ${CONFIG}
        sudo sed -i -e "0,/^down_switch/{s/down_switch.*/down_switch=0/}" ${CONFIG}
        sudo sed -i -e "0,/^left_switch/{s/left_switch.*/left_switch=0/}" ${CONFIG}
        sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=0/}" ${CONFIG}
    else
        echo "Configuring 26 Pin wiring"  | tee -a ${LOG}
        sudo sed -i -e "0,/^menu_switch=/{s/menu_switch=.*/menu_switch=25/}" ${CONFIG}
        sudo sed -i -e "0,/^mute_switch/{s/mute_switch.*/mute_switch=4/}" ${CONFIG}
        sudo sed -i -e "0,/^up_switch/{s/up_switch.*/up_switch=17/}" ${CONFIG}
        sudo sed -i -e "0,/^down_switch/{s/down_switch.*/down_switch=${DOWN_SWITCH}/}" ${CONFIG}
        sudo sed -i -e "0,/^left_switch/{s/left_switch.*/left_switch=14/}" ${CONFIG}
        sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=15/}" ${CONFIG}
    fi

# Configure the cosmic controller (40 pin only)
elif [[ ${BUTTON_WIRING} == "3" ]]; then
    echo "Configuring Cosmic Controller Pin wiring"  | tee -a ${LOG}
    # Switches
    sudo sed -i -e "0,/^menu_switch=/{s/menu_switch=.*/menu_switch=5/}" ${CONFIG}
    sudo sed -i -e "0,/^mute_switch/{s/mute_switch.*/mute_switch=27/}" ${CONFIG}
    sudo sed -i -e "0,/^up_switch/{s/up_switch.*/up_switch=6/}" ${CONFIG}
    sudo sed -i -e "0,/^down_switch/{s/down_switch.*/down_switch=4/}" ${CONFIG}
    sudo sed -i -e "0,/^left_switch/{s/left_switch.*/left_switch=23/}" ${CONFIG}
    sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=24/}" ${CONFIG}

    # Configure status LEDs
    sudo sed -i -e "0,/^rgb_red/{s/rgb_red.*/rgb_red=14/}" ${CONFIG}
    sudo sed -i -e "0,/^rgb_green/{s/rgb_green.*/rgb_green=15/}" ${CONFIG}
    sudo sed -i -e "0,/^rgb_blue/{s/rgb_blue.*/rgb_blue=16/}" ${CONFIG}

# Configure Pimoroni pHat BEAT
elif [[ ${BUTTON_WIRING} == "4" ]]; then
    echo "Configuring Pimoroni pHat BEAT"  | tee -a ${LOG}
    # Switches
    sudo sed -i -e "0,/^menu_switch=/{s/menu_switch=.*/menu_switch=12/}" ${CONFIG}
    sudo sed -i -e "0,/^mute_switch/{s/mute_switch.*/mute_switch=6/}" ${CONFIG}
    sudo sed -i -e "0,/^up_switch/{s/up_switch.*/up_switch=5/}" ${CONFIG}
    sudo sed -i -e "0,/^down_switch/{s/down_switch.*/down_switch=13/}" ${CONFIG}
    sudo sed -i -e "0,/^left_switch/{s/left_switch.*/left_switch=26/}" ${CONFIG}
    sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=16/}" ${CONFIG}

# Configure Pimoroni Audio with ST7789 controller (40 pin only)
elif [[ ${BUTTON_WIRING} == "5" ]]; then
    echo "Configuring Pimoroni Audio with ST7789 controller"  | tee -a ${LOG}
    # Switches
    sudo sed -i -e "0,/^menu_switch=/{s/menu_switch=.*/menu_switch=0/}" ${CONFIG}
    sudo sed -i -e "0,/^mute_switch/{s/mute_switch.*/mute_switch=0/}" ${CONFIG}
    sudo sed -i -e "0,/^up_switch/{s/up_switch.*/up_switch=16/}" ${CONFIG}
    sudo sed -i -e "0,/^down_switch/{s/down_switch.*/down_switch=5/}" ${CONFIG}
    sudo sed -i -e "0,/^left_switch/{s/left_switch.*/left_switch=6/}" ${CONFIG}

    # Some versions of the Pimoroni Audio use GPIO 20 for the right switch
    sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=24/}" ${CONFIG}
    #sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=20/}" ${CONFIG}

# Configure 1.3" OLED with 5-button joystick and 3 push buttons
elif [[ ${BUTTON_WIRING} == "6" ]]; then
    echo "Configuring Pimoroni Audio with ST7789 controller"  | tee -a ${LOG}
    # Switches
    sudo sed -i -e "0,/^menu_switch=/{s/menu_switch=.*/menu_switch=13/}" ${CONFIG}
    sudo sed -i -e "0,/^mute_switch/{s/mute_switch.*/mute_switch=21/}" ${CONFIG}
    sudo sed -i -e "0,/^up_switch/{s/up_switch.*/up_switch=6/}" ${CONFIG}
    sudo sed -i -e "0,/^down_switch/{s/down_switch.*/down_switch=19/}" ${CONFIG}
    sudo sed -i -e "0,/^left_switch/{s/left_switch.*/left_switch=5/}" ${CONFIG}
    sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=26/}" ${CONFIG}

# Disable switch GPIOs if using SPI or I2C interface
else 
    sudo sed -i -e "0,/^menu_switch=/{s/menu_switch=.*/menu_switch=0/}" ${CONFIG}
    sudo sed -i -e "0,/^mute_switch/{s/mute_switch.*/mute_switch=0/}" ${CONFIG}
    sudo sed -i -e "0,/^up_switch/{s/up_switch.*/up_switch=0/}" ${CONFIG}
    sudo sed -i -e "0,/^down_switch/{s/down_switch.*/down_switch=0/}" ${CONFIG}
    sudo sed -i -e "0,/^left_switch/{s/left_switch.*/left_switch=0/}" ${CONFIG}
    sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=0/}" ${CONFIG}
fi

# Configure splash screen
echo "Configuring splash screen as ${SPLASH[index]//\\/}"
sudo sed -i -e "0,/^splash/{s/splash.*/splash=${SPLASH}/}" ${CONFIG}

# Configure the pull up/down resistors
if [[ ${PULL_UP_DOWN} == "1" ]]; then
    sudo sed -i -e "0,/^pull_up_down/{s/pull_up_down.*/pull_up_down=up/}" ${CONFIG}

else
    sudo sed -i -e "0,/^pull_up_down/{s/pull_up_down.*/pull_up_down=down/}" ${CONFIG}
fi

# Flip OLED display
if [[ ${FLIP_OLED_DISPLAY} == "1" ]]; then
    sudo sed -i -e "0,/^flip_display_vertically/{s/flip_display_vertically.*/flip_display_vertically=yes/}" ${CONFIG}

else
    sudo sed -i -e "0,/^flip_display_vertically/{s/flip_display_vertically.*/flip_display_vertically=no/}" ${CONFIG}
fi

#####################
# Summarise changes #
#####################

echo | tee -a ${LOG}
echo "Changes written to ${CONFIG}" | tee -a ${LOG}
echo "-----------------------------------" | tee -a ${LOG}
if [[ ${USER_INTERFACE} != "0" ]]; then
    echo $(grep "^user_interface=" ${CONFIG} ) | tee -a ${LOG}
fi

if [[ ${USER_INTERFACE} == "2" ]]; then
    echo $(grep "^rotary_class=" ${CONFIG} ) | tee -a ${LOG}
fi

if [[ $DISPLAY_TYPE != "" ]]; then
    echo $(grep "^display_type=" ${CONFIG} ) | tee -a ${LOG}
    echo $(grep "^display_lines=" ${CONFIG} ) | tee -a ${LOG}
    echo $(grep "^display_width=" ${CONFIG} ) | tee -a ${LOG}
    echo | tee -a ${LOG}
fi

if [[ ${DISPLAY_TYPE} == "GRAPHICAL" ]]; then
    echo $(grep "^screen_size=" ${CONFIG} ) | tee -a ${LOG}
    echo | tee -a ${LOG}
fi

# LCD wiring
wiring=$(grep "^lcd_" ${CONFIG} )
for item in ${wiring}
do
    echo ${item} | tee -a ${LOG}
done
echo | tee -a ${LOG}

# Button / Rotary encoder wiring
wiring=$(grep "^[a-z]*_switch=" ${CONFIG} )
for item in ${wiring}
do
    echo ${item} | tee -a ${LOG}
done
echo | tee -a ${LOG}

echo $(grep "^pull_up_down=" ${CONFIG} ) | tee -a ${LOG}
echo $(grep "^flip_display_vertically=" ${CONFIG} ) | tee -a ${LOG}
echo $(grep "^splash=" ${CONFIG} ) | tee -a ${LOG}

echo $(grep "^volume_range=" ${CONFIG} ) | tee -a ${LOG}
if [[ $DATE_FORMAT != "" ]]; then
    echo $(grep -m 1 "^dateformat=" ${CONFIG} ) | tee -a ${LOG}
fi
echo "-----------------------------------" | tee -a ${LOG}

echo | tee -a ${LOG}
# Update system startup 
if [[ ${DISPLAY_TYPE} == "GRAPHICAL" ]]; then

    # Set up desktop radio execution icon
    sudo cp ${DIR}/Desktop/gradio.desktop /home/${USR}/Desktop/.
    sudo cp ${DIR}/Desktop/vgradio.desktop /home/${USR}/Desktop/.
    sudo chmod +x /home/${USR}/Desktop/gradio.desktop
    sudo chmod +x /home/${USR}/Desktop/vgradio.desktop

    # Add [SCREEN] section to the configuration file
    grep "\[SCREEN\]" ${CONFIG} >/dev/null 2>&1
    if [[ $? != 0 ]]; then  # Don't seperate from above
        echo "Adding [SCREEN] section to ${CONFIG}" | tee -a ${LOG}
        sudo cat ${DIR}/gradio.conf | sudo tee -a ${CONFIG}
    fi
    sudo systemctl daemon-reload
    cmd="sudo systemctl disable radiod.service"
    echo ${cmd}; ${cmd}  >/dev/null 2>&1

    # Set fullscreen option (Graphical radio version only)
    if [[ ${FULLSCREEN} != "" ]]; then
        sudo sed -i -e "0,/^fullscreen/{s/fullscreen.*/fullscreen=${FULLSCREEN}/}" ${CONFIG}
        echo "fullscreen=${FULLSCREEN}" | tee -a ${LOG}
    fi

# Enable  radio daemon to start radiod
elif [[ ${DISPLAY_TYPE} =~ "LCD" ]]; then
    if [[ -x /bin/systemctl ]]; then
        sudo systemctl daemon-reload
        cmd="sudo systemctl enable radiod.service"
        echo ${cmd}; ${cmd} >/dev/null 2>&1
    else
        sudo systemctl enable radiod 
    fi
fi

# Enable mpd socket service
cmd="sudo systemctl disable mpd.service"
echo ${cmd}; ${cmd} >/dev/null 2>&1
cmd="sudo systemctl enable mpd.socket"
echo ${cmd}; ${cmd} >/dev/null 2>&1

echo ${PROGRAM};echo | tee -a ${LOG}

# Install anacron if not already installed
PKG="anacron"
if [[ ! -f /usr/sbin/anacron && ${FLAGS} != "-s" ]]; then
        echo "Installing ${PKG} package" | tee -a ${LOG}
        sudo apt-get --yes install ${PKG}
fi


# Configure audio device
ans=0
ans=$(whiptail --title "Configure audio interface?" --menu "Choose your option" 15 75 9 \
"1" "Run audio configuration program (configure_audio.sh)" \
"2" "Do not change audio configuration" 3>&1 1>&2 2>&3) 

if [[ ${ans} == '1' ]]; then
    sudo ${DIR}/configure_audio.sh ${FLAGS}
else
    echo "Audio configuration unchanged."    | tee -a ${LOG}
fi

# Integrity check of /boot/config.txt
declare -i lines=$(wc -l ${BOOTCONFIG} | awk '{print $1}')
if [[ ${lines} -lt 10 ]]; then
    echo "ERROR: ${BOOTCONFIG} failed integrity check"
    echo "Restoring ${BOOTCONFIG} from ${BOOTCONFIG}.orig"
    sudo cp ${BOOTCONFIG}.orig ${BOOTCONFIG}
    echo "Re-run sudo ${0} "
    exit 1
else 
    echo
    echo "${BOOTCONFIG} has ${lines} lines"
    echo
fi

# Sync changes to disk
sync;sync

echo "Reboot Raspberry Pi to enable changes." | tee -a ${LOG}
echo "A log of these changes has been written to ${LOG}"
exit 0

# End of configuration script

