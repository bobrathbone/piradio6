#!/bin/bash
# Raspberry Pi display  OS configuration for analysis
# $Id: display_os.sh,v 1.4 2025/05/10 08:43:31 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program is diagnostic to display the OS and user details 
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#

# This script requires an English locale(C)
export LC_ALL=C

DIR=/usr/share/radio
LOGDIR=${DIR}/logs
SCRIPTS_DIR=${DIR}/scripts
LOG=${LOGDIR}/os_config.log
USR=$(logname)
GRP=$(id -g -n ${USR})
OS_RELEASE=/etc/os-release
DEBIAN_VERSION=/etc/debian_version
BOOTCONFIG=/boot/firmware/config.txt
BOOTCONFIG_2=/boot/config.txt
# The LXDE sub directory can be plain LXDE or LXDE-${USR}
LXSESSION=/home/${USR}/.config/lxsession
AUTOSTART="${LXSESSION}/LXDE*/autostart"
RADIOD=/usr/share/radio/radiod.py
WAYFIRE_INI=~/.config/wayfire.ini
EMAIL="bob@bobrathbone.com"
RADIO_CONFIG=/etc/radiod.conf

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

# Return X protocol (X11 or Wayland)
function X-protocol
{
    type=$(loginctl show-session $(loginctl | grep "$USER" | awk '{print $1}') -p Type | grep -i wayland)
    if [[ $? == 0 ]]; then  # Do not seperate from above
        X=Wayland
    else
        X=X11
    fi
    echo ${X}
}

echo "OS configuration log for host $(hostname) $(date)" | tee ${LOG}
# Create run log directory
mkdir -p ${LOGDIR}
sudo chown ${USR}:${GRP} ${LOGDIR}

# Display OS
echo | tee -a ${LOG}
echo "OS Configuration" | tee -a ${LOG}
echo "----------------" | tee -a ${LOG}
cat ${OS_RELEASE} | tee -a ${LOG}
echo "Debian version $(cat ${DEBIAN_VERSION})" | tee -a ${LOG}

echo | tee -a ${LOG}
if [[ -f ${BOOTCONFIG} ]]; then
    BOOTCFG=${BOOTCONFIG}
else
    BOOTCFG=${BOOTCONFIG_2}
fi
echo "Boot configuration"  | tee -a ${LOG}
echo "------------------" | tee -a ${LOG}
echo "${BOOTCFG}"  | tee -a ${LOG}
grep "^arm_64bit" ${BOOTCFG} | tee -a ${LOG}
grep "^dtoverlay=" ${BOOTCFG} | tee -a ${LOG}
grep "^dtparam=" ${BOOTCFG} | tee -a ${LOG}

echo | tee -a ${LOG}

echo "Kernel version " | tee -a ${LOG}
echo "--------------" | tee -a ${LOG}
uname -a  | tee -a ${LOG}
echo "OS $(codename) Architecture $(getconf LONG_BIT)-bit" | tee -a ${LOG}
echo | tee -a ${LOG}

# Display nework details
echo "Network configuration" | tee -a ${LOG}
echo "---------------------" | tee -a ${LOG}
ip4=$(hostname -I | awk '{print $1;}')
echo "IP address: ${ip4}"  | tee -a ${LOG}
ip route | tee -a ${LOG}

${SCRIPTS_DIR}/display_wifi.sh | tee -a ${LOG}
echo | tee -a ${LOG}

# Display user details
echo "User details" | tee -a ${LOG}
echo "------------" | tee -a ${LOG}
echo "User ${USER}, Group: ${GRP}" | tee -a ${LOG}
echo "Home directory: ${HOME}" | tee -a ${LOG}
id ${USR} | tee -a ${LOG}
echo | tee -a ${LOG}

# Check for X-Windows graphic radio installation
echo "Desktop installation" | tee -a ${LOG}
echo "--------------------" | tee -a ${LOG}
if [[ -f /usr/bin/startx ]]; then
    X=$(X-protocol)
    echo "X-Windows appears to be installed and is using the ${X} protocol" | tee -a ${LOG}
    if [[ ${X} == "X11" ]]; then
        entry=$(grep -i 'radio' ${AUTOSTART})
        if [[ $? == 0 ]]; then
            if [[ ${entry:0:1} == "#" ]]; then
                echo "Graphic version of the radio is disabled in ${AUTOSTART}" | tee -a ${LOG}
            else
                echo "Graphic version of the radio configured in ${AUTOSTART}" | tee -a ${LOG}
            fi
            echo ${entry} | tee -a ${LOG}
        else
            echo "Graphic versions of the radio not configured in ${AUTOSTART}" | tee -a ${LOG}
        fi

    elif [[ ${X} == "Wayland" ]]; then
        echo "X-Windows autostart configuration in file ${WAYFIRE_INI}" | tee -a ${LOG}
        grep "\[autostart\]" ${WAYFIRE_INI} | tee -a ${LOG}
        sed -e '1,/\[autostart\]/d' ${WAYFIRE_INI} | tee -a ${LOG}
        if [[ $? != 0 ]]; then
            echo "[autostart] not configured in ${WAYFIRE_INI}" | tee -a ${LOG}
        fi
    else
        echo "No X-Window configuration foe wayland or X11 found" | tee -a ${LOG}
    fi
else
    echo "X-Windows is not installed" | tee -a ${LOG}
    echo "Probaly Raspbian-Lite installed" | tee -a ${LOG}
fi


# Display radio version and alsa configuration
echo | tee -a ${LOG}
if [[ -f ${RADIOD} ]]; then 
    echo "Radio version"  | tee -a ${LOG}
    echo "-------------"  | tee -a ${LOG}
    ${RADIOD} version | tee -a ${LOG}
    ${RADIOD} build | tee -a ${LOG}
    echo | tee -a ${LOG}
    echo "Audio Configuration" | tee -a ${LOG}
    echo "-------------------" | tee -a ${LOG}
    AUDIO_OUT=$(grep "audio_out=" ${RADIO_CONFIG}) | tee -a ${LOG}
    if [[ ${AUDIO_OUT} =~ bluetooth  ]]; then
        echo ${AUDIO_OUT}  | tee -a ${LOG}
    else
        /usr/bin/aplay -l | tee -a ${LOG}
    fi
    aplay -L | grep -i pulse | tee -a ${LOG}
fi

echo | tee -a ${LOG}

# Create tar file
tar -zcf ${LOG}.tar.gz ${LOG} >/dev/null 2>&1
echo "A log of this run will be found in ${LOG}" 
echo "A compressed tar file has been saved in ${LOG}.tar.gz" | tee -a ${LOG}
echo "Send ${LOG}.tar.gz to ${EMAIL} if required" | tee -a ${LOG}
echo | tee -a ${LOG}

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
