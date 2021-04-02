#!/usr/bin/env python3
"""
Test bitmap image
"""

import sys
from oled import OLED
from oled import Font
from PIL import Image
from oled import Graphics

# Image to be displayed
bitmap = 'bitmaps/clown.bmp'
bitmap = 'bitmaps/raspberry-pi-logo.bmp'

# Draw image location at x,y
def drawImage(bitmap,x,y):
    img = Image.open(bitmap)

    w = img.size[0]
    h = img.size[1]
    try:
        for i in range(0, w):
            for j in range(0, h):
                xy = (i, j)
                if img.getpixel(xy):
                    Graphics.draw_pixel(i+x, j+y, False)
                else:
                    Graphics.draw_pixel(i+x, j+y, True)
    except: pass

# Initialize library.
dis = OLED(1)
dis.begin()

# Clear display.
dis.clear()
drawImage(bitmap,35,0)
dis.update()
sys.exit(0)

