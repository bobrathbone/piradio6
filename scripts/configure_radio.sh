#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: configure_radio.sh,v 1.35 2025/07/09 09:15:26 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is used during installation to set up which
# radio daemon and peripherals are to be used. For 40-pin Raspberry Pi's only
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

BINDIR="\/usr\/share\/radio\/"  # Used for sed so \ needed
DIR=/usr/share/radio
SCRIPTS=${DIR}/scripts

# Display colours
orange='\033[33m'
blue='\033[34m'
green='\033[32m'
default='\033[39m'

# Development directory
if [[ ! -d ${DIR} ]];then
    echo "Fatal error: radiod package not installed!"
    exit 1
fi

# Version 7.5 onwards allows any user with sudo permissions to install the software
USER=$(logname)
GRP=$(id -g -n ${USER})

OS_RELEASE=/etc/os-release
LOGDIR=${DIR}/logs
CONFIG=/etc/radiod.conf
BOOTCONFIG=/boot/config.txt
BOOTCONFIG_2=/boot/firmware/config.txt
CMDLINE=/boot/cmdline.txt
CMDLINE_2=/boot/firmware/cmdline.txt
ETCMODULES=/etc/modules
MPDCONF=/etc/mpd.conf
WXCONFIG=/etc/weather.conf
LOG=${LOGDIR}/install.log
NODAEMON_LOG=${LOGDIR}/radiod_nodaemon.log
SPLASH="bitmaps\/raspberry-pi-logo.bmp" # Used for sed so \ needed
MANAGE_PIP=/usr/lib/python3.11/EXTERNALLY-MANAGED
FFMPEG=/usr/bin/ffmpeg
X_INSTALLED='no'   # 'yes' = X-Windows installed
WALLPAPER==/usr/share/rpd-wallpaper

# X-Window parameters
LXSESSION=""    # Start desktop radio at boot time
WAYFIRE_INI=/home/$USER/.config/wayfire.ini
LABWC_DIR=/home/$USER/.config/labwc
LABWC_AUTOSTART=${LABWC_DIR}/autostart
LABWC=/usr/bin/labwc
FULLSCREEN=""   # Start graphic radio fullscreen
SCREEN_SIZE="800x480"   # Screen size 800x480, 720x480 or 480x320

PROGRAM="Daemon radiod configured"
GPROG=""        # Which graphical radio (gradio or vgradio)
FONT_SIZE=11    # Font size for TFT displays 
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
DLINES=4        # Number of display lines
DWIDTH=20       # Display character width
FLIP=0          # OLED display can be flipped vertically

# Old wiring down switch
DOWN_SWITCH=10

# Volume sensitivity
VOLUME_RANGE=20

# Date format (Use default in radiod.conf)
DATE_FORMAT=""  

# Rotary encoder step size  
# Only used in the standard rotary encoder class and NOT the alternative rotary class
# ABC encoders seem to work best with 'full' step, KY040 encoders better with 'half' step
ROTARY_STEP_SIZE="full"

# KY040 rotary encoders can have resistor R1 (SW to VCC) omitted, 1 = R1 fitted
KY040_R1_FITTED=0

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

function no_install
{
    echo
    echo "WARNING!"
    echo "You cannot configure $1 during the initial installation" | tee -a ${LOG}
    printf "Run ${orange}radio-config${default} from the command line"
    printf " then select ${green}1 configure radio software${default}\n"
    echo "from the menu line and reconfigure the radio software"
    echo 
    echo -n "Press enter to continue: "
    read x
}

# Check if X-Windows installed
dpkg -l | grep xserver-xorg-core 2>&1 >/dev/null
if [[ $? == 0 ]]; then
    X_INSTALLED="yes"
fi

# Create log directory
sudo mkdir -p ${LOGDIR}
sudo chown ${USER}:${GRP} ${LOGDIR}

# In Bookworm (Release ID 12) the configuration has been moved to /boot/firmware/config.txt
if [[ $(release_id) -ge 12 ]]; then
    BOOTCONFIG=${BOOTCONFIG_2}
    CMDLINE=${CMDLINE_2}
fi

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
# Display top level menu 
DRIVERS=0
COMPONENTS=0
EDIT=0
DAEMONS=0

# Display full menu if not called from package install
if [[ ${FLAGS} != "-s" ]]; then
    if [[ -f ${CONFIG}.org ]]; then
        ans=0
        ans=$(whiptail --title "Upgrading, Re-configure radio?" --menu "Choose your option" 15 75 9 \
        "1" "Configure radio software" \
        "2" "Configure audio output devices" \
        "3" "Update radio stations playlist" \
        "4" "Create media playlists" \
        "5" "Diagnostics and Information" \
        "6" "Documents and Tutorials" \
        "7" "Edit configuration files" \
        "8" "Install/configure drivers and software components" \
        "9" "Start/Stop/Status radio daemons" 3>&1 1>&2 2>&3) 

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            exit 0

        elif [[ ${ans} == '2' ]]; then
            sudo ${SCRIPTS}/configure_audio.sh ${FLAGS}
            exit 0

        elif [[ ${ans} == '3' ]]; then
            sudo ${DIR}/create_stations.py 
            exit 0

        elif [[ ${ans} == '4' ]]; then
            sudo ${SCRIPTS}/create_playlist.sh ${FLAGS}
            exit 0

        elif [[ ${ans} == '5' ]]; then
            ${SCRIPTS}/diagnostics.sh ${FLAGS}
            exit 0

        elif [[ ${ans} == '6' ]]; then
            ${SCRIPTS}/display_docs.sh ${FLAGS}
            exit 0

        elif [[ ${ans} == '7' ]]; then
            EDIT=1

        elif [[ ${ans} == '8' ]]; then
            COMPONENTS=1

        elif [[ ${ans} == '9' ]]; then
            DAEMONS=1
        fi
    fi
fi

if [[ ${COMPONENTS} == 1 ]]; then
    run_components=1
    while [ $run_components == 1 ]
    do
        SCRIPT=""
        SUDO=""
        CMD=""
        ans=$(whiptail --title "Install software and driver components" --menu "Choose your option" 15 75 9 \
        "1" "Install/Configure IR remote control" \
        "2" "Install Web Interface" \
        "3" "Install Airplay (shairport-sync)" \
        "4" "Install Icecast" \
        "5" "Install Speech facility" \
        "6" "Install Luma OLED/TFT driver" \
        "7" "Install recording utility (liquidsoap)" \
        "8" "Install Alsa equalizer software" \
        "9" "Install Spotify (librespot)" \
        "10" "Install FLIRC IR remote control (X-Windows)" \
        "11" "Install PiFace CAD (Bullseye only)" \
        3>&1 1>&2 2>&3) 

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            exit 0

        elif [[ ${ans} == '1' ]]; then
            SCRIPT="configure_ir_remote.sh"
            DESC="Install IR remote control"

        elif [[ ${ans} == '2' ]]; then
            SCRIPT="install_web_interface.sh"
            DESC="Install Web Interface"

        elif [[ ${ans} == '3' ]]; then
            SCRIPT="install_airplay.sh"
            DESC="Install Airplay"

        elif [[ ${ans} == '4' ]]; then
            SCRIPT="install_streaming.sh"
            DESC="Install Icecast"
            SUDO="sudo"

        elif [[ ${ans} == '5' ]]; then
            SCRIPT="configure_speech.sh"
            DESC="Install Speech facility"

        elif [[ ${ans} == '6' ]]; then
            SCRIPT="install_luma.sh"
            DESC="Install Luma OLED/TFT driver"

        elif [[ ${ans} == '7' ]]; then
            SCRIPT="install_recording.sh"
            DESC="Install recording (liquidsoap)"

        elif [[ ${ans} == '8' ]]; then
            SCRIPT="install_equalizer.sh"
            DESC="Install Alsa equalizer"

        elif [[ ${ans} == '9' ]]; then
            SCRIPT="install_spotify.sh"
            DESC="Install Spotify (librespot)"

        elif [[ ${ans} == '10' ]]; then
            SCRIPT="install_flirc.sh"
            DESC="Install FLIRC (X-Windows)"

        elif [[ ${ans} == '11' ]]; then
            SCRIPT="install_pifacecad.sh"
            DESC="Install PiFace CAD (Bullseye only)"
        fi

        ## To do
        ## ${DIR}/install_ssd1306.sh ${FLAGS}
        #exit 0
        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60

        selection=$? 
        if [[ ${selection} == 0 ]]; then # Do not separate from above
            run_components=0
        fi
    done

    # Install component
    if [[ ${CMD} != "" ]]; then
        ${CMD} 
        exit 0
    elif [[ ${SCRIPT} != "" ]]; then
        ${SUDO} ${SCRIPTS}/${SCRIPT} ${FLAGS}
        exit 0
    fi
fi

if [[ ${DAEMONS} == 1 ]]; then
    run_daemons=1
    while [ $run_daemons == 1 ]
    do
        CTL_C=0
        SERVICE=""
        ACTION="status"

        ans=$(whiptail --title "Select operation" --menu "Choose your option" 16 75 10 \
        "1" "Start radio daemon " \
        "2" "Stop radio daemon " \
        "3" "Enable radio daemon " \
        "4" "Disable radio daemon " \
        "5" "Start IR remote control daemon" \
        "6" "Stop IR remote control daemon" \
        "7" "Enable IR remote control daemon" \
        "8" "Disable IR remote control daemon" \
        "9" "Radio service status" \
        "10" "IR remote control daemon status" 3>&1 1>&2 2>&3) 

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            exit 0

        elif [[ ${ans} == '1' ]]; then
            SERVICE=radiod.service 
            ACTION=restart

        elif [[ ${ans} == '2' ]]; then
            SERVICE=radiod.service 
            ACTION=stop

        elif [[ ${ans} == '3' ]]; then
            SERVICE=radiod.service 
            ACTION=enable

        elif [[ ${ans} == '4' ]]; then
            SERVICE=radiod.service 
            ACTION=disable

        elif [[ ${ans} == '5' ]]; then
            SERVICE=ireventd.service 
            ACTION=restart

        elif [[ ${ans} == '6' ]]; then
            SERVICE=ireventd.service 
            ACTION=stop

        elif [[ ${ans} == '7' ]]; then
            SERVICE=ireventd.service 
            ACTION=enable

        elif [[ ${ans} == '8' ]]; then
            SERVICE=ireventd.service 
            ACTION=disable

        elif [[ ${ans} == '9' ]]; then
            SERVICE=radiod.service 
            ACTION=status

        elif [[ ${ans} == '10' ]]; then
            SERVICE=ireventd.service 
            ACTION=status
            CTL_C=1
        fi

        # If SERVICE defined carry out the required action
        if [[ ${SERVICE} != "" ]]; then 
            clear
            if [[ ${CTL_C} == 1 ]]; then
                echo "Enter Ctrl-C to continue"
                echo "========================"
                echo
            fi
            cmd="sudo systemctl ${ACTION} ${SERVICE}" 
            echo ${cmd}
            ${cmd} 
            if [[ $? == 0 ]]; then
                echo "Command executed OK"
            fi
            echo
            if [[ ${CTL_C} == 0 ]]; then
                echo -n "Press enter to continue: "
                read key
            fi
        fi
    done
    exit 0
fi

if [[ ${EDIT} == 1 ]]; then
    ${SCRIPTS}/edit_files.sh
    exit 0
fi

# Normal cofiguration start
sudo rm -f ${LOG}
# Make log file writeable
sudo touch ${LOG}
sudo chown ${USER}:${GRP} ${LOG}

echo "$0 configuration log, $(date) " | tee ${LOG}
echo "Using ${DIR}" | tee -a ${LOG}
echo "Configuring radio for $(codename) OS " | tee -a ${LOG}
echo "Boot configuration in ${BOOTCONFIG}" | tee -a ${LOG}
echo "X-Windows installed ${X_INSTALLED}"  | tee -a ${LOG}

# Copy the distribution configuration
ans=$(whiptail --title "Replace your configuration file ?" --menu "Choose your option" 15 75 9 \
"1" "Replace configuration file" \
"2" "Amend existing configuration file" \
"3" "Only update software" \
3>&1 1>&2 2>&3) 

exitstatus=$?
if [[ $exitstatus != 0 ]]; then
    exit 0

elif [[ ${ans} == '1' ]]; then
    pwd 
    sudo mv ${CONFIG} ${CONFIG}.save    
    echo "Existing configuration  copied to ${CONFIG}.save" | tee -a ${LOG}
    sudo cp ${DIR}/radiod.conf ${CONFIG}
    echo "Current configuration ${CONFIG} replaced with distribution" | tee -a ${LOG}

elif [[ ${ans} == '2' ]]; then
    echo "Amend existing configuration"  | tee -a ${LOG}

elif [[ ${ans} == '3' ]]; then
    echo "Software only update"  | tee -a ${LOG}
    exit 0
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
        BUTTON_WIRING=1
        GPIO_PINS=1
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

PULL_UP_DOWN=1
# Check how push-buttons are wired

# Configure pull-up resistors for type of rotary encoder
if [[ ${USER_INTERFACE} == "2" ]]; then
    ans=0
    selection=1 
    while [ $selection != 0 ]
    do
        ROTARY_CLASS="standard"

        ans=$(whiptail --title "Select type of rotary encoder" --menu "Choose your option" 15 75 9 \
        "1" "Standard rotary encoders with A, B and C inputs only" \
        "2" "Rotary encoders (eg KY-040) with no resistor R1 (default)" \
        "3" "Rotary encoders (eg KY-040) with resistor R1 fitted (3 resistors)" \
        "4" "Rotary encoders with RGB LEDs" \
        "5" "I2C Rotary encoders with RGB LEDs" \
        "6" "Standard A,B,C rotary encoders alternative driver" \
        "7" "Not sure" 3>&1 1>&2 2>&3) 

        exitstatus=$?
        if [[ $exitstatus != 0 ]]; then
            exit 0
        fi

        if [[ ${ans} == '1' ]]; then
            DESC="Configuring standard rotary encoders"
            ROTARY_STEP_SIZE="half"
            ROTARY_HAS_RESISTORS=0

        elif [[ ${ans} == '2' ]]; then
            DESC="Configuring rotary encoders (eg. KY-040) with resistor R1 omitted"
            ROTARY_HAS_RESISTORS=1
            ROTARY_STEP_SIZE="half"

        elif [[ ${ans} == '3' ]]; then
            DESC="Configuring rotary encoders (eg. KY-040) with resistor R1 fitted"
            ROTARY_HAS_RESISTORS=1
            ROTARY_STEP_SIZE="half"
            KY040_R1_FITTED=1

        elif [[ ${ans} == '4' ]]; then
            DESC="Configuring rotary encoders with RGB LEDs"
            ROTARY_HAS_RESISTORS=1
            ROTARY_CLASS="rgb_rotary"

        elif [[ ${ans} == '5' ]]; then
            DESC="Configuring I2C rotary encoders with RGB LEDs"
            ROTARY_CLASS="rgb_i2c_rotary"
            GPIO_PINS=2

        elif [[ ${ans} == '6' ]]; then
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

# Install ioe-python
if [[ ${ROTARY_CLASS} == "rgb_i2c_rotary" ]]; then 
    if [[ ${FLAGS} != "-s" ]]; then
        if [[ ! -x /usr/bin/git ]]; then
            sudo apt-get install git
        fi
        echo "Answer Y to questions about creating a virtual environment for this script if asked"
        echo "Answer N to questions about installing documentation and examples"
        echo -n "Enter to continue "
        read y
        echo "Installing Pimoroni ioe-python" | tee -a ${LOG}
        git clone https://github.com/pimoroni/ioe-python        
        cd ioe-python/
        ./install.sh
        cd -
    else
        no_install "I2C rotary encoders with RGB LEDs"
        exit 0
    fi
    
    # Link ioexpander to site-packages 
    if [[ $(release_id) -ge 12 ]]; then
        sudo ln -s ~/.virtualenvs/pimoroni/lib/python3.11/site-packages/ioexpander \
                   /usr/lib/python3.11/dist-packages/ioexpander fi
    else
        sudo ln -s ~/.virtualenvs/pimoroni/lib/python3.9/site-packages/ioexpander \
                   /usr/lib/python3.9/dist-packages/ioexpander
    fi
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
    "14" "Waveshare 2.42\" OLED with SPI interface" \
    "15" "Waveshare 1.5\" OLED with SPI interface" \
    "16" "No display used/Pimoroni Pirate radio" \
    "17" "Waveshare I2C 40-character 2-line LCD (PCF8574)" \
    "18" "Do not change display type" 3>&1 1>&2 2>&3) 

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
        FLIP=1

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
        SCROLL_SPEED="0.1" 
        VOLUME_RANGE=10
        SPI_REQUIRED=1
        SPLASH="images\/raspberrypi.png"

    elif [[ ${ans} == '10' ]]; then
        DISPLAY_TYPE="LUMA"
        DESC="OLEDs using LUMA driver"
        DLINES=4
        DWIDTH=16
        SCROLL_SPEED="0.1" 
        VOLUME_RANGE=10
        I2C_REQUIRED=1
        I2C_ADDRESS="0x3C"
        SPLASH="images\/raspberrypi.png"
        FLIP=1

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
        SCROLL_SPEED="0.1" 
        VOLUME_RANGE=20
        SPI_REQUIRED=1
        SPLASH="bitmaps\/raspberry-pi-logo.bmp" 

    elif [[ ${ans} == '14' ]]; then
        DISPLAY_TYPE="WS_SPI_SSD1309.2in42"
        DESC="Waveshare 2.42\" OLED with SPI interface"
        DLINES=5
        DWIDTH=25
        SCROLL_SPEED="0.07" 
        VOLUME_RANGE=20
        SPI_REQUIRED=1
        FLIP=1

    elif [[ ${ans} == '15' ]]; then
        DISPLAY_TYPE="WS_SPI_SSD1309.1in5_b"
        DESC="Waveshare 1.5\" OLED with SPI interface"
        DLINES=5
        DWIDTH=25
        SCROLL_SPEED="0.007" 
        VOLUME_RANGE=20
        SPI_REQUIRED=1
        FLIP=1

    elif [[ ${ans} == '16' ]]; then
        DISPLAY_TYPE="NO_DISPLAY"
        DLINES=0
        DWIDTH=0
        DESC="No display used"

    elif [[ ${ans} == '17' ]]; then
        DISPLAY_TYPE="LCD_I2C_PCF8574"
        DESC="Waveshare 40-character 2-line LCD"
        DLINES=2
        DWIDTH=40
        SCROLL_SPEED="0.1" 
        I2C_REQUIRED=1

    else
        DESC="Display type unchanged"
        echo ${DESC} | tee -a ${LOG}

    fi

    whiptail --title "$DESC" --yesno "Is this correct?" 10 60
    selection=$?
done 

# Create "/tmp/check_luma.py"
cat >/tmp/check_luma.py << EOF
import luma.core
EOF

if [[ ${DISPLAY_TYPE} == "LUMA" ]]; then

    python check_luma.py >/dev/null 2>&1
    if [[ $? == 0 ]]; then
        echo "Luma core already installed" | tee -a ${LOG}
    else
        echo "Installing Luma core" | tee -a ${LOG}
        ${SCRIPTS}/install_luma.sh        
    fi

    # Configure LUMA.driver
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
            FONT_SIZE=12

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
if [[ ${FLIP} == 1 ]]; then
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
    echo "Enabling the SPI kernel module" | tee -a ${LOG}
    sudo dtparam spi=on

    # Enable the SPI kernel interface 
    sudo sed -i 's/^#dtparam=spi=.*$/dtparam=spi=on/'  ${BOOTCONFIG}
    sudo sed -i 's/^dtparam=spi=.*$/dtparam=spi=on/'  ${BOOTCONFIG}
else
    echo "Disabling the SPI kernel module" | tee -a ${LOG}
    sudo dtparam spi=off
    sudo sed -i 's/^dtparam=spi=.*$/dtparam=spi=off/'  ${BOOTCONFIG}
fi

if [[ ${I2C_REQUIRED} != 0 ]]; then
    # Select the I2C address
    ans=0
    selection=1 
    while [ $selection != 0 ]
    do
        ans=$(whiptail --title "Select I2C hex address" --menu "Choose your option" 15 75 9 \
        "1" "Hex 0x20 (Adafruit devices)" \
        "2" "Hex 0x27 (PCF8574 devices) including 40-character LCD" \
        "3" "Hex 0x37 (PCF8574 devices alternative address)" \
        "4" "Hex 0x3F (PCF8574 devices 2nd alternative address)" \
        "5" "Hex 0x3C (Olimex OLED/Cosmic controller/Sitronix SSD1306/LUMA devices)" \
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
    dtparam=i2c_arm=on
    sudo sed -i -e "0,/^\#dtparam=i2c_arm/{s/\#dtparam=i2c_arm.*/dtparam=i2c_arm=yes/}" ${BOOTCONFIG}
    sudo sed -i -e "0,/^\dtparam=i2c_arm/{s/\dtparam=i2c_arm.*/dtparam=i2c_arm=yes/}" ${BOOTCONFIG}
    grep -q ^i2c-dev ${ETCMODULES}
    if [[ $? -ne 0 ]]; then
        param=i2c-dev
        echo "Adding ${param} to  ${ETCMODULES}"
        echo $param | sudo tee -a ${ETCMODULES} > /dev/null
    fi
fi

# Select the display type (Lines and Width)
echo "Configuring display type ${DISPLAY_TYPE}" | tee -a ${LOG}
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
        "5" "Two line 40 character LCD" \
        "6" "Do not change display type" 3>&1 1>&2 2>&3) 

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

        elif [[ ${ans} == '5' ]]; then
            DESC="Two line 40 character LCD" 
            DLINES=2;DWIDTH=40

        else
            echo "Wiring configuration in ${CONFIG} unchanged"   | tee -a ${LOG}
        fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
    done

elif [[ ${DISPLAY_TYPE} =~ "WS_SPI_SSD1309" ]]; then
    set -x
    if [[ ${FLAGS} != "-s" ]]; then
        if [[ $(release_id) -ge 12 ]]; then
            sudo mv ${MANAGE_PIP} ${MANAGE_PIP}.orig
        fi
        sudo apt-get install python3-pip
        sudo pip3 install RPi.GPIO
        sudo apt-get install python3-smbus
        sudo pip3 install spidev

        if [[ $(release_id) -ge 12 ]]; then
            sudo mv ${MANAGE_PIP}.orig ${MANAGE_PIP}
        fi

        sudo sed -i 's/^#dtparam=spi=.*$/dtparam=spi=on/'  ${BOOTCONFIG}
        sudo sed -i 's/^dtparam=spi=.*$/dtparam=spi=on/'  ${BOOTCONFIG}
    else
        no_install "Waveshare SPI SSD1309 display"
        exit 0
    fi

elif [[ ${DISPLAY_TYPE} == "OLED_128x64" ]]; then
    if [[ ${FLAGS} != "-s" ]]; then
        PKGS="libffi-dev build-essential libi2c-dev i2c-tools python3-dev"
        echo "Installing ${PKGS} " | tee -a ${LOG} 
        sudo apt-get -y install ${PKGS} 
    else
        no_install "Olimex OLED 128x64"
        exit 0
    fi

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
        "4" "7-inch TFT touch-screen (800x480)" \
        "5" "HDMI television or monitor (1024x600)" \
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
            DESC="7-inch TFT touch-screen (800x480)"
            SCREEN_SIZE="800x480"

        elif [[ ${ans} == '5' ]]; then
            DESC="HDMI television or monitor"
            SCREEN_SIZE="1024x600"

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
            DESC="Start radio in a desktop window" 
            FULLSCREEN="no"

        else
            echo "Desktop configuration unchanged"   | tee -a ${LOG}
        fi

        whiptail --title "${DESC}" --yesno "Is this correct?" 10 60
        selection=$?
    done

    echo "Desktop program ${GPROG}.py configured" | tee -a ${LOG}
fi


# X-Windows radio desktop program (gradio or vgradio) installation 
# Install for both X11 and Wayland protocols as user can switch between them
LXDE="LXDE-${USER}"
LXDE_DIR=/home/${USER}/.config/lxsession/${LXDE}
X11_AUTOSTART="${LXDE_DIR}/autostart"

if [[ ${DISPLAY_TYPE} == "GRAPHICAL" ]]; then

    echo "Configuring X-Windows configuration for automatic start" | tee -a ${LOG}
    if [[ ! -d ${LXDE_DIR} ]]; then
        mkdir -p ${LXDE_DIR}
        cp ${DIR}/lxsession/${LXDE}.autostart ${X11_AUTOSTART} 
        chown -R ${USER}:${GRP} /home/${USER}/.config/lxsession
    fi

    # Configure desktop X11 autostart if X-Windows installed
    if [[ -f ${X11_AUTOSTART} ]]; then
        echo "${X11_AUTOSTART}" | tee -a ${LOG}
        if [[ ${LXSESSION} == "yes" ]]; then
            # Delete old entry if it exists
            sudo sed -i -e "/radio/d" ${X11_AUTOSTART}
            cmd="@sudo /usr/share/radio/${GPROG}.py"
            sudo echo ${cmd} | tee -a ${LOG}
            echo ${cmd} >>  ${X11_AUTOSTART}
        fi
        echo | tee -a ${LOG}
    fi

    # Configure desktop wayfire.ini if Wayland installed 
    if [[ -f ${WAYFIRE_INI} ]]; then
        echo "${WAYFIRE_INI}" | tee -a ${LOG}
        if [[ ${LXSESSION} == "yes" ]]; then
            grep "^\[autostart\]"  ${WAYFIRE_INI} > /dev/null 2>&1
            if [[ $? != 0 ]]; then
                echo >> ${WAYFIRE_INI}
                cmd="[autostart]"
                echo ${cmd} | tee -a ${LOG}
                echo ${cmd} >> ${WAYFIRE_INI}
            fi 
            # Delete old entry if it exists
            sudo sed -i "/^radiod = sudo/d" ${WAYFIRE_INI}
            sudo sed -i "/^#radiod = sudo/d" ${WAYFIRE_INI}
            cmd="radiod = sudo /usr/share/radio/${GPROG}.py"
            echo ${cmd} | tee -a ${LOG}
            echo ${cmd} >> ${WAYFIRE_INI} 
        fi
        echo | tee -a ${LOG}
    fi 

    if [[ -f ${LABWC} ]]; then
        echo "${LABWC_AUTOSTART}" | tee -a ${LOG}
        if [[ ${LXSESSION} == "yes" ]]; then
            if [[ ! -d ${LABWC_DIR} ]]; then
                mkdir -p ${LABWC_DIR}
            fi
            if [[ ! -d ${LABWC_AUTOSTART} ]]; then
                touch ${LABWC_AUTOSTART}
            fi
            sed -i '/gradio/d' ${LABWC_AUTOSTART} >/dev/null 2>&1
            cmd="sudo /usr/share/radio/${GPROG}.py &"
            echo ${cmd} | tee -a ${LOG}
            echo ${cmd} >> ${LABWC_AUTOSTART} 
            chown -R pi:pi ${LABWC_DIR}
        fi
    fi
else
    # Delete auto-run entries from all X-Windows configurations
    echo "Deleting any X-Windows application start commands" | tee -a ${LOG}
    if [[ -f ${X11_AUTOSTART} ]]; then
        echo "   ${X11_AUTOSTART}" | tee -a ${LOG}
        sudo sed -i "/gradio/d" ${X11_AUTOSTART}
        sudo sed -i "/vgradio/d" ${X11_AUTOSTART}
    fi

    if [[ -f ${WAYFIRE_INI} ]]; then
        echo "   ${WAYFIRE_INI}" | tee -a ${LOG}
        sed -i '/radiod = sudo/d' ${WAYFIRE_INI}
    fi

    if [[ -f ${LABWC_AUTOSTART} ]]; then
        echo "   ${LABWC_AUTOSTART}" | tee -a ${LOG}
        sed -i '/gradio/d' ${LABWC_AUTOSTART}
        sed -i '/vgradio/d' ${LABWC_AUTOSTART}
    fi

fi  # End of ${DISPLAY_TYPE} == "GRAPHICAL" 

# Install Adafruit SSD1306 package if required
if [[ ${ADAFRUIT_SSD1306} > 0  ]]; then
    ${SCRIPTS}/install_ssd1306.sh | tee -a ${LOG}
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
    sudo sed -i -e "0,/^font_size/{s/font_size.*/font_size=${FONT_SIZE}/}" ${CONFIG}
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
    sudo sed -i -e "0,/^rotary_step_size/{s/rotary_step_size.*/rotary_step_size=${ROTARY_STEP_SIZE}/}" ${CONFIG}

    if [[ ${ROTARY_HAS_RESISTORS} == 1 ]]; then
        sudo sed -i -e "0,/^rotary_gpio_pullup/{s/rotary_gpio_pullup.*/rotary_gpio_pullup=none/}" ${CONFIG}
    fi

    if [[ ${KY040_R1_FITTED} == 1 ]]; then 
        r1fitted=yes
    else
        r1fitted=no
    fi
    sudo sed -i -e "0,/^ky040_r1_fitted/{s/ky040_r1_fitted.*/ky040_r1_fitted=${r1fitted}/}" ${CONFIG}

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
    if [[ ! -x /usr/sbin/i2cdetect ]]; then
        sudo apt -y install i2c-tools
    fi
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

echo "BUTTON_WIRING  ${BUTTON_WIRING}"

# Configure buttons and rotary encoders
if [[ ${BUTTON_WIRING} == "1" || ${BUTTON_WIRING} == "3" ]]; then

    if [[ ${GPIO_PINS} == "1" ]]; then
        echo "Configuring 40 Pin wiring"  | tee -a ${LOG}
        sudo sed -i -e "0,/^menu_switch=/{s/menu_switch=.*/menu_switch=17/}" ${CONFIG}
        sudo sed -i -e "0,/^mute_switch/{s/mute_switch.*/mute_switch=4/}" ${CONFIG}
        sudo sed -i -e "0,/^up_switch/{s/up_switch.*/up_switch=24/}" ${CONFIG}
        sudo sed -i -e "0,/^down_switch/{s/down_switch.*/down_switch=23/}" ${CONFIG}
        sudo sed -i -e "0,/^left_switch/{s/left_switch.*/left_switch=14/}" ${CONFIG}
        sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=15/}" ${CONFIG}

    elif [[ ${GPIO_PINS} == "2" ]]; then
        echo "Configuring RGB I2C encoder Pin wiring"  | tee -a ${LOG}
        sudo sed -i -e "0,/^menu_switch=/{s/menu_switch=.*/menu_switch=17/}" ${CONFIG}
        sudo sed -i -e "0,/^mute_switch/{s/mute_switch.*/mute_switch=4/}" ${CONFIG}
        sudo sed -i -e "0,/^up_switch/{s/up_switch.*/up_switch=0/}" ${CONFIG}
        sudo sed -i -e "0,/^down_switch/{s/down_switch.*/down_switch=0/}" ${CONFIG}
        sudo sed -i -e "0,/^left_switch/{s/left_switch.*/left_switch=0/}" ${CONFIG}
        sudo sed -i -e "0,/^right_switch/{s/right_switch.*/right_switch=0/}" ${CONFIG}
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

    # Install ST7789
    if [[ ${FLAGS} != "-s" ]]; then
        sudo apt-get install python3-pip
        if [[ -f  ${MANAGE_PIP} ]]; then
            sudo mv ${MANAGE_PIP} ${MANAGE_PIP}.orig
        fi
        echo "Installing ST7789 module" | tee -a ${LOG}
        sudo apt-get -y install libopenblas-dev
        sudo pip3 install st7789 
        sudo mv ${MANAGE_PIP}.orig ${MANAGE_PIP}
    else
        no_install "Devices with ST7789 controller"
        exit 0
    fi

# Configure 1.3" OLED with 5-button joystick and 3 push buttons
elif [[ ${BUTTON_WIRING} == "6" ]]; then
    echo "Configuring Pimoroni Audio with ST7789 controller" | tee -a ${LOG}
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

# Disable dtoverlay=i2s-mmap (now automatically loaded)
echo "Disable dtoverlay=i2s-mmap in ${BOOTCONFIG}" 
sudo sed -i -e "0,/^dtoverlay=i2s-mmap/{s/^dtoverlay=i2s-mmap.*/#dtoverlay=i2s-mmap/}" ${BOOTCONFIG}


# Force fsck file system check
grep -q "fsck.mode=force" ${CMDLINE}
if [[ $? -ne 0 ]]; then
    sudo cp -f ${CMDLINE} ${CMDLINE}.save
    sudo sed -i -e "0,/fsck.repair=yes/{s/fsck.repair=yes/fsck.repair=yes fsck.mode=force/}" ${CMDLINE}
    echo "Added fsck.mode=force to ${CMDLINE}"
fi

#####################
# Summarise changes #
#####################
echo | tee -a ${LOG}
echo "Boot configuration ${BOOTCONFIG} settings" | tee -a ${LOG}
echo "----------------------------------------------" | tee -a ${LOG}
grep "^dtoverlay" ${BOOTCONFIG} | tee -a ${LOG}

echo | tee -a ${LOG}
echo "Changes written to ${CONFIG}" | tee -a ${LOG}
echo "-----------------------------------" | tee -a ${LOG}
if [[ ${USER_INTERFACE} != "0" ]]; then
    echo $(grep "^user_interface=" ${CONFIG} ) | tee -a ${LOG}
fi

if [[ ${USER_INTERFACE} == "2" ]]; then
    echo $(grep "^rotary_class=" ${CONFIG} ) | tee -a ${LOG}
    echo $(grep "^rotary_gpio_pullup=" ${CONFIG} ) | tee -a ${LOG}
    echo $(grep "^rotary_step_size=" ${CONFIG} ) | tee -a ${LOG}
    echo $(grep "^ky040_r1_fitted=" ${CONFIG} ) | tee -a ${LOG}
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
    sudo cp ${DIR}/Desktop/gradio.desktop /home/${USER}/Desktop/.
    sudo cp ${DIR}/Desktop/vgradio.desktop /home/${USER}/Desktop/.
    sudo chmod +x /home/${USER}/Desktop/gradio.desktop
    sudo chmod +x /home/${USER}/Desktop/vgradio.desktop

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

# Install config-parser if running Bullseye
PKG="python-configparser"
if [[ $(release_id) -le 11 ]]; then
        echo "Installing ${PKG} package" | tee -a ${LOG}
        sudo apt-get -y install ${PKG}
fi

# Install X-windows components
if [[ ${X_INSTALLED} == 'yes' ]]; then

    # Install ffmpeg (Used for X-Windows programs)
    if [[ ! -x ${FFMPEG} ]]; then
        sudo apt-get -y install ffmpeg
    fi

    if [[ ! -x ${WALLPAPER} ]]; then
        sudo apt-get -y install rpd-wallpaper
    fi

fi

# Configure audio device
ans=0
ans=$(whiptail --title "Configure audio interface?" --menu "Choose your option" 15 75 9 \
"1" "Run audio configuration program (configure_audio.sh)" \
"2" "Do not change audio configuration" 3>&1 1>&2 2>&3) 

if [[ ${ans} == '1' ]]; then
    sudo ${SCRIPTS}/configure_audio.sh ${FLAGS}
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

# set tabstop=4 shiftwidth=4 expandtab
# retab
