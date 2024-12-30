#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: copy_html_docs.sh,v 1.1 2024/12/19 13:52:17 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program converts all <document>.md files to HTML and copies them to
# the /var/www/html/docs directory if Apache web server installed
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.

DIR=/usr/share/radio
DOCS_DIR=${DIR}/docs
WWW_DOCS=/var/www/html/docs
CMARK=/usr/bin/cmark
APACHECTL=/usr/sbin/apachectl


# Install cmark if not yet installed
if [[ ! -f ${CMARK} ]]; then
    sudo apt-get -y install cmark
fi

if [[ ! -x ${APACHECTL} ]]; then
    echo "Apache Web server not installed - Exiting" 
    exit 1
fi

for doc in ${DOCS_DIR}/*.md
do
    file=$(basename "$doc")
    file="${file%.*}"
    ${CMARK} ${doc} > ${DOCS_DIR}/${file}.html
    echo "Converted ${file}.md to ${file}.html"
    sudo cp -f ${DOCS_DIR}/${file}.html ${WWW_DOCS}/.
done

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
