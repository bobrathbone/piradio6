#!/bin/bash
# $Id: buildweb.sh,v 1.1 2017/09/28 07:37:56 bob Exp $
# Build script for the Raspberry PI radio
# Run this script as user pi and not root

PKG=radiodweb
VERSION=$(grep ^Version: ${PKG} | awk '{print $2}')
ARCH=$(grep ^Architecture: ${PKG} | awk '{print $2}')
DEBPKG=${PKG}_${VERSION}_${ARCH}.deb

# Tar build files

WEBPAGES="/var/www/html/*  /usr/lib/cgi-bin/select_source.cgi"
BUILDFILES="radiodweb radioweb.postinst"
WEBTAR=pi_radio_web.tar.gz

# Create Web pages tar file
tar -cvzf ${WEBTAR} ${WEBPAGES} > /dev/null 2>&1

echo "Building package ${PKG} version ${VERSION}"
echo "from input file ${PKG}"
sudo chown pi:pi *.py
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
