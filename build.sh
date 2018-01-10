#!/bin/bash
# $Id: build.sh,v 1.4 2017/11/30 09:57:51 bob Exp $
# Build script for the Raspberry PI radio
# Run this script as user pi and not root
# sudo vi /usr/share/equivs/template/debian/compat (Replace 7 with 9)

PKGDEF=piradio
PKG=radiod
VERSION=$(grep ^Version: ${PKGDEF} | awk '{print $2}')
ARCH=$(grep ^Architecture: ${PKGDEF} | awk '{print $2}')
DEBPKG=${PKG}_${VERSION}_${ARCH}.deb
BUILDLOG=build.log

# Tar build files
BUILDFILES="piradio piradio.postinst piradio.postrm piradio.preinst"
BUILDTAR=piradio_build.tar.gz
tar -cvzf ${BUILDTAR} ${BUILDFILES} > /dev/null

echo "Building package ${PKG} version ${VERSION}" | tee ${BUILDLOG}
echo "from input file ${PKGDEF}" | tee -a ${BUILDLOG}
sudo chown pi:pi *.py
sudo chmod +x *.py
sudo chown pi:pi *.sh
sudo chmod +x *.sh
sudo chmod -x language/* voice.dist

# Create tar (optional)
#./create_tar.sh > /dev/null 2>&1 

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
