#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Raspberry Pi Internet Radio Class
# $Id: constants.py,v 1.71 2026/01/14 14:15:05 bob Exp $
#
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class provides constants for the radiod package
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#

# Amend version and 
__build_no__ = 12
__version__ = "8.2" 
build = __version__ + '.' + str(__build_no__)

# Up/Down constants (switch levels)
UP = 1 
DOWN = 0

# MPD mute actions
PAUSE = 0
STOP = 1
