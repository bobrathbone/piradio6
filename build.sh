#!/bin/bash
# $Id: build.sh,v 1.18 2024/11/29 12:21:56 bob Exp $
# Build script for the Raspberry PI radio
# Run this script as user pi and not root

# Install the following packages before using this script
# sudo apt-get -y install equivs apt-file lintian

# Compatability rules
# Edit the compat file and change 9 to 10
# sudo vi /usr/share/equivs/template/debian/compat (Replace 9 with 10)

# Version 7.5 onwards allows any user with sudo permissions to install the software
USR=$(logname)
GRP=$(id -g -n ${USR})

PKGDEF=piradio
PKG=radiod
VERSION=$(grep ^Version: ${PKGDEF} | awk '{print $2}')
#ARCH=$(grep ^Architecture: ${PKGDEF} | awk '{print $2}')
BUILDLOG=build.log
OS_RELEASE=/etc/os-release
EQUIVS=/usr/bin/equivs-build
MPD=/usr/bin/mpd

# Colours
orange='\033[33m'
blue='\033[34m'
green='\033[32m'
default='\033[39m'

# Check we are not running as sudo
if [[ "$EUID" -eq 0 ]];then
    echo "Run this script as user ${USR} and not sudo/root"
    exit 1
fi

echo "Building radiod package $(date)"

# Check if this machine is 32 or 64-bit
BIT=$(getconf LONG_BIT)
if [[ ${BIT} == "64" ]]; then
    echo "64-bit system."
    ARCH="arm64"
elif [[ ${BIT} == "32" ]]; then
    echo "32-bit system."
    ARCH="armhf"
else
    echo "Cannot determine Architecture. Using 64-bit"
    ARCH="arm64"
fi

cp -f ${PKGDEF} ${PKGDEF}.save

DEBPKG=${PKG}_${VERSION}_${ARCH}.deb
echo "Buiding ${DEBPKG}"
sudo sed -i -e "0,/^Architecture:/{s/^Architecture:.*/Architecture: ${ARCH}/}" ${PKGDEF} 

# We need Rasbian Buster (Release 10) or later
VERSION_ID=$(grep VERSION_ID ${OS_RELEASE})
SAVEIFS=${IFS}; IFS='='
ID=$(echo ${VERSION_ID} | awk '{print $2}' | sed 's/"//g')
if [[ ${ID} -lt 10 ]]; then
	VERSION=$(grep VERSION= ${OS_RELEASE})
    echo "Raspbian Buster (Release 10) or later is required to run this build"
	RELEASE=$(echo ${VERSION} | awk '{print $2 $3}' | sed 's/"//g')
	echo "This is Raspbian ${RELEASE}"
    exit 1
fi
IFS=${SAVEIFS}

echo "Building package ${PKG} version ${VERSION}" | tee ${BUILDLOG}
echo "from input file ${PKGDEF}" | tee -a ${BUILDLOG}
echo "Update version and build number in constants.py as required"
sudo chown ${USR}:${GRP} *.py *.cmd *.sh
sudo chmod +x *.py *.cmd *.sh
sudo chmod -x language/* voice.dist

if [[ ! -f ${MPD} ]]; then
    sudo apt-get -y install python3-mpd mpd
fi

if [[ ! -f ${EQUIVS} ]];then
    sudo apt-get -y install equivs apt-file lintian
fi

# Build the package
equivs-build ${PKGDEF} | tee -a ${BUILDLOG}

echo -n "Check using Lintian y/n: "
read ans
if [[ ${ans} == 'y' ]]; then
	echo "Checking package ${DEBPKG} with lintian"  | tee -a ${BUILDLOG} 
	lintian ${DEBPKG} | tee -a ${BUILDLOG}
	if [[ $? = 0 ]]
	then
	    echo "Package ${DEBPKG} OK" | tee -a ${BUILDLOG}
	    echo "See ${BUILDLOG} for build details" 
	    echo "Package ${DEBPKG} file list" >> ${BUILDLOG}
	    dpkg -c ${DEBPKG} >> ${BUILDLOG}
	else
	    echo "Package ${DEBPKG} has errors" | tee -a ${BUILDLOG}
	fi
fi

# Prevent CVS from updating package file every time this is run
mv ${PKGDEF}.save ${PKGDEF}

echo
echo "Now install the ${DEBPKG} package with the following command:"
printf $orange
echo "sudo dpkg -i ${DEBPKG}"
printf $default
printf "To configure the radio software run ${green}radio-config\n\n"
printf $default

# End of build script
