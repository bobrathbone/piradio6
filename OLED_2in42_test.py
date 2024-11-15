#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import pdb
dir = os.getcwd()
libdir = os.path.join(dir,'waveshare_OLED/lib')
picdir = os.path.join(dir,'waveshare_OLED/pic')
fontdir = os.path.join(dir,'waveshare_OLED/fonts')
print(libdir)
print(picdir)
print(fontdir)

if os.path.exists(libdir):
    sys.path.append(libdir)

import logging    
import time
import traceback
from waveshare_OLED.lib import OLED_2in42
from PIL import Image,ImageDraw,ImageFont
logging.basicConfig(level=logging.DEBUG)

try:
    #pdb.set_trace()
    disp = OLED_2in42.OLED_2in42(spi_freq = 1000000)

    logging.info("\r2.42inch OLED ")
    # Initialize library.
    disp.Init()
    # Clear display.
    logging.info("clear display")
    disp.clear()

    # Create blank image for drawing.
    image1 = Image.new('1', (disp.width, disp.height), "WHITE")
    draw = ImageDraw.Draw(image1)
    font1 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 18)
    font2 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 24)
    logging.info ("***draw line")
    draw.line([(0,0),(127,0)], fill = 0)
    draw.line([(0,0),(0,63)], fill = 0)
    draw.line([(0,63),(127,63)], fill = 0)
    draw.line([(127,0),(127,63)], fill = 0)
    logging.info ("***draw text")
    draw.text((20,0), 'Waveshare ', font = font1, fill = 0)
    draw.text((20,24), u'微雪电子 ', font = font2, fill = 0)
    image1 = image1.rotate(180) 
    disp.ShowImage(disp.getbuffer(image1))
    time.sleep(3)
    
    logging.info ("***draw image")
    Himage2 = Image.new('1', (disp.width, disp.height), 255)  # 255: clear the frame
    #bmp = Image.open(os.path.join(picdir, 'waveshare.bmp'))
    bmp = Image.open(os.path.join(picdir, 'raspberry-pi-logo.bmp'))
    Himage2.paste(bmp, (0,0))
    Himage2=Himage2.rotate(180) 	
    disp.ShowImage(disp.getbuffer(Himage2)) 
    time.sleep(3)    
    disp.clear()

except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    disp.module_exit()
    exit()
