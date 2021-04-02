#!/usr/bin/env python3
# Raspberry OLED test program 
#
# $Id: oled_hello.py,v 1.2 2020/10/13 06:59:53 bob Exp $
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#           The authors shall not be liable for any loss or damage however caused.
#
# Adapted from hello world program from Olimex Limited, www.olimex.com
# See https://github.com/SelfDestroyer/pyMOD-OLED.git
# 

from oled import OLED
from oled import Font
from oled import Graphics
import pdb,sys
import time,datetime
from time import strftime

#dis = OLED(0)  # Original Raspberry Pi only
# Connect to the display on /dev/i2c-1
dis = OLED(1)

# Start communication
#pdb.set_trace()
dis.begin()

# Start basic initialization
dis.initialize()

# Do additional configuration
dis.set_memory_addressing_mode(0)
dis.set_column_address(0, 127)
dis.set_page_address(0, 7)

# Clear display
dis.clear()

# Set font scale x2
f = Font(2)

# Print some large text
f.print_string(6, 0, "B.Rathbone")

sDate = strftime('%d, %b %Y %H:%M:%S')

# Change font to 5x7
f.scale = 1
f.print_string(0, 24, sDate)
f.print_string(0, 32, " www.bobrathbone.com")
f.print_string(0, 44, "abcdefghijklmnopqrstu")

# Send video buffer to display
dis.update()

# Make horizontal scroll
dis.horizontal_scroll_setup(dis.LEFT_SCROLL, 3, 3, 7)
dis.activate_scroll()

# Only the last scroll setup is active
dis.horizontal_scroll_setup(dis.LEFT_SCROLL, 4, 4, 6)
dis.activate_scroll()

# Draw line
Graphics.draw_pixel(0, 0)
Graphics.draw_line(0, 60, 125, 60)
dis.update()
