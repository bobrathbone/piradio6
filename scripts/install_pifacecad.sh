#!/bin/bash
# $Id: install_pifacecad.sh,v 1.4 2025/01/26 09:25:18 bob Exp $
# Raspberry Pi Internet Radio - Install PiFace CAD
# This script installs and configures PiFace CAD display 
# See https://github.com/piface/pifacecad?tab=readme-ov-file
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.

FLAGS=$1
DIR=/usr/share/radio
# Test flag - change to current directory
if [[ ${FLAGS} == "-t" ]]; then
    DIR=$(pwd)
fi

LOGDIR=${DIR}/logs
SCRIPTS_DIR=${DIR}/scripts
LOG=${LOGDIR}/install_piface_cad.log
OS_RELEASE=/etc/os-release

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

# Install details
echo "$0 configuration log, $(date) " | tee ${LOG}

if [[ $(release_id) -ge 12 ]]; then
    echo "This installation only runs on Bullseye" | tee ${LOG}
    echo "This is $(codename) OS - Exiting" | tee ${LOG}
    exit 1
fi

echo "Using ${DIR}" | tee -a ${LOG}

echo "Installing dependencies " | tee -a ${LOG}
cd ${DIR}
pwd | tee -a ${LOG}
sudo apt-get install liblircclient-dev cython3 gcc python{,3}-setuptools python{,3}-dev | tee -a ${LOG}

# cython now called cython3
sudo ln -f -s /usr/bin/cython3 /usr/bin/cython

echo "Installing pythonlirc " | tee -a ${LOG}
cd ${DIR}
pwd | tee -a ${LOG}
git clone https://github.com/tompreston/python-lirc.git | tee -a ${LOG}
cd python-lirc/
pwd | tee -a ${LOG}
make py3 && sudo python3 setup.py install | tee -a ${LOG}
make py2 && sudo python setup.py install | tee -a ${LOG}

echo "Installing PiFace common" | tee -a ${LOG}
cd ${DIR}
pwd | tee -a ${LOG}
git clone https://github.com/piface/pifacecommon.git | tee -a ${LOG}
cd pifacecommon/ 
pwd | tee -a ${LOG}
sudo python setup.py install 2>&1 | tee -a ${LOG}
sudo python3 setup.py install 2>&1 | tee -a ${LOG}

echo "Installing PiFace CAD " | tee -a ${LOG}
cd ${DIR}
pwd | tee -a ${LOG}
git clone https://github.com/piface/pifacecad.git | tee -a ${LOG}
cd pifacecad/ 
pwd | tee -a ${LOG}
sudo python setup.py install  2>&1 | tee -a ${LOG}
sudo python3 setup.py install  2>&1 | tee -a ${LOG}

echo "Cleanup - Removing python-lirc, pifacecommon, pifacecad in ${DIR}" | tee -a ${LOG}
sudo rm -rf ${DIR}/python-lirc
sudo rm -rf ${DIR}/pifacecommon
sudo rm -rf ${DIR}/pifacecad

echo | tee -a ${LOG}
echo "PiFace CAD installation complete" | tee -a ${LOG}
echo "A log of this run will be found in ${LOG}"

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab

