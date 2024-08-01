#!/usr/bin/env python3
# Raspberry Pi RGB I2C Rotary Encoder Class
# $Id: rgb_set_i2c_address.py,v 1.5 2024/06/13 16:05:41 bob Exp $
#
# Author : Bob Rathbone and Lubos Ruckl (Czech republic)
# Site   : http://www.bobrathbone.com
#
# This program is used to set programable I2C addresses of the Pimoroni I2C RGB Rotary Encoder 
# See https://shop.pimoroni.com/products/rgb-encoder-breakout
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#
#Change the I2C_ADDR to:
# - 0x1F to use with the Rotary Encoder breakout.
# - 0x18 to use with IO Expander.

import sys
import ioexpander as io
import string
import pdb

I2C_ADDR = 0x1F  # 0x18 for IO Expander, 0x1F for the encoder breakout

ioe = None

class RGB_I2C_RotaryEncoder:

    i2c_address = 0xF0

    def __init__(self,i2c_address=0xF0):
        global ioe
        self.i2c_address = i2c_address
        ioe = io.IOE(i2c_addr=self.i2c_address, interrupt_pin=4)

        ioe.enable_interrupt_out(pin_swap=True)
        
    # Set the IOE i2c address
    def set_i2c_addr(self, i2c_addr):
        print("Setting IOE I2C address to %s" % hex(i2c_addr))
        ioe.set_i2c_addr(i2c_addr)
        sys.exit(0)

# End of i2c RGB Rotary Encoder class

if __name__ == "__main__":

    def usage():
        print('')
        print("Usage: sudo %s --help " % sys.argv[0])
        print("               --i2c_address=<i2c_address>")
        print("               --new_i2c_address=<new_i2c_address>")
        print('')
        print("Recommended values for current and new adresses are 0x0F and 0x1F")
        print("Run \"i2cdetect -y 1\" to check I2C address before and after")
        print('')
        sys.exit(0)

    def get_value(param):
        x,value = param.split('=')
        return value

    def hexValue(x):
        try:
            int(x,16)
            isHex = True
        except:
            isHex = False
        return isHex 

    i2c_address = 0x0F
    new_i2c_address = 0x1F

    print("RGB I2C Rotary Encoder set new I2C address %s" % hex(i2c_address))

    if len(sys.argv) < 2 or sys.argv[1] == "--help":
        usage()

    # Get command line parameters
    for i in range(1,len(sys.argv)):
        param = sys.argv[i]
        if param == "--help":
            usage()

        elif "--i2c_address" in param:
            value = get_value(param)
            if hexValue(value):
                i2c_address = int(value,16)
            else:
                print("Invalid new hex value %s specified" % value)
                exit(1)

        elif "--new_i2c_address" in param:
            value = get_value(param)
            if hexValue(value):
                new_i2c_address = int(value,16)
            else:
                print("Invalid new hex value %s specified" % value)
                exit(1)
        else:
            print("Invalid parameter %s" % param)
            usage()
            
    print("Change device hex address from %s to %s" % (hex(i2c_address),hex(new_i2c_address)))
    answer = input("Do you wish to change the I2C address y/n: ")
    if answer == 'y':
        encoder = RGB_I2C_RotaryEncoder(i2c_address)
        encoder.set_i2c_addr(new_i2c_address)
    else:
        print("I2C address unchanged")

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
