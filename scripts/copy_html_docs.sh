#!/bin/bash
# set -x
# Raspberry Pi Internet Radio
# $Id: copy_html_docs.sh,v 1.5 2025/01/07 12:14:18 bob Exp $
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
CMARK_BIN="/usr/bin/cmark"
CMARK="${CMARK_BIN} --hardbreaks"
APACHECTL=/usr/sbin/apachectl
HTML_HEADER="<!DOCTYPE html> <html> <head>"
CSS='<link rel="stylesheet" type="text/css" href="docs.css">'
HTML_BODY="</head> <body>"
HTML_FOOTER="</body> </html>"

# Install cmark if not yet installed
if [[ ! -f ${CMARK_BIN} ]]; then
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
    echo ${HTML_HEADER} > ${DOCS_DIR}/${file}.html
    echo ${CSS} >> ${DOCS_DIR}/${file}.html
    echo ${HTML_BODY} >> ${DOCS_DIR}/${file}.html
    echo "<button onclick=\"window.location.href='index.html';\">Back</button>" >> ${DOCS_DIR}/${file}.html
    ${CMARK} ${doc} >> ${DOCS_DIR}/${file}.html
    echo "<button onclick=\"window.location.href='index.html';\">Back</button>" >> ${DOCS_DIR}/${file}.html
    echo ${HTML_FOOTER} >> ${DOCS_DIR}/${file}.html
    echo "Converted ${file}.md to ${file}.html"
    sudo cp -f ${DOCS_DIR}/${file}.html ${WWW_DOCS}/.
done
# Copy CSS file
sudo cp -f ${DOCS_DIR}/docs.css ${WWW_DOCS}/.
sudo cp -f ${DOCS_DIR}/index.html ${WWW_DOCS}/.
echo "The above html documents have been copied to ${WWW_DOCS}"

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab

