#!/bin/bash
# $Id: build64.sh,v 1.1 2021/05/04 05:47:32 bob Exp $
# Build script for the Raspberry PI radio (64 bit)
# Run this script as user pi and not root

# Install the following packages before using this script
# sudo apt-get -y install equivs apt-file lintian

# Compatability rules
# Edit the compat file and change 9 to 10
# sudo vi /usr/share/equivs/template/debian/compat (Replace 9 with 10)

PKGDEF=piradio64
PKG=radiod
VERSION=$(grep ^Version: ${PKGDEF} | awk '{print $2}')
ARCH=$(grep ^Architecture: ${PKGDEF} | awk '{print $2}')
DEBPKG=${PKG}_${VERSION}_${ARCH}.deb
BUILDLOG=build.log
OS_RELEASE=/etc/os-release

# Check we are not running as sudo
if [[ "$EUID" -eq 0 ]];then
        echo "Run this script as user pi and not sudo/root"
        exit 1
fi

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
sudo chown pi:pi *.py *.cmd *.sh
sudo chmod +x *.py *.cmd *.sh
sudo chmod -x language/* voice.dist

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

# End of build script
