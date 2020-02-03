#!/bin/bash
# $Id: build.sh,v 1.9 2019/12/10 15:33:47 bob Exp $
# Build script for the Raspberry PI radio
# Run this script as user pi and not root

# Install the following packages before using this script
# sudo apt-get -y install equivs apt-file lintian

# Compatability rules
# Edit the compat file and change 7 to 9
# sudo vi /usr/share/equivs/template/debian/compat (Replace 7 with 9)

PKGDEF=piradio
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

# Tar build files
BUILDFILES="piradio piradio.postinst piradio.postrm piradio.preinst"
BUILDTAR=piradio_build.tar.gz
tar -cvzf ${BUILDTAR} ${BUILDFILES} > /dev/null

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
