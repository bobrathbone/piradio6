#!/bin/bash 
#
# Raspberry Pi Radiod display title and station/track name from MPD
#
# $Id: display_title.sh,v 1.1 2020/10/10 15:00:45 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
name=$(./display_current.py | grep name:)
if [[ $? -eq 0 ]]; then
	echo $name
fi

artist=$(./display_current.py | grep artist:)
if [[ $? -eq 0 ]]; then
	echo $artist
fi

title=$(./display_current.py | grep title:)
if [[ $? -eq 0 ]]; then
	echo $title
fi

