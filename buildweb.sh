#!/bin/bash
# $Id: buildweb.sh,v 1.4 2023/06/05 22:10:04 bob Exp $
# Build script for the Raspberry PI radio
# Run this script as user pi and not root

PKG=radiodweb
VERSION=$(grep ^Version: ${PKG} | awk '{print $2}')
ARCH=$(grep ^Architecture: ${PKG} | awk '{print $2}')
DEBPKG=${PKG}_${VERSION}_${ARCH}.deb
OS_RELEASE=/etc/os-release

# Version 7.5 onwards allows any user with sudo permissions to install the software
USR=$(logname)
GRP=$(id -g -n ${USR})

# Check we are not running as sudo
if [[ "$EUID" -eq 0 ]];then
        echo "Run this script as user pi and not sudo/root"
        exit 1
fi

# Tar build for Rasbian Buster (Release 10) or later
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

WEBPAGES="/var/www/html/*  /usr/lib/cgi-bin/*.cgi"
BUILDFILES="radiodweb radioweb.postinst"
WEBTAR=piradio_web.tar.gz

# Create Web pages tar file
echo "Create web pages tar file ${WEBTAR}"
tar -cvzf ${WEBTAR} ${WEBPAGES} > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
        echo "Missing input files ${WEBPAGES}"
        exit 1
fi

echo "Building package ${PKG} version ${VERSION}"
echo "from input file ${PKG}"
sudo chown ${USR}:${GRP} *.py
sudo chmod +x *.py
equivs-build ${PKG}

echo -n "Check using Lintian y/n: "
read ans
if [[ ${ans} == 'y' ]]; then
    echo "Checking package ${DEBPKG} with lintian"
    lintian ${DEBPKG}
    if [[ $? = 0 ]]
    then
        dpkg -c ${DEBPKG}
        echo "Package ${DEBPKG} OK"
    else
        echo "Package ${DEBPKG} has errors"
    fi
fi

# End of build script
