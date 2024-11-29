#!/usr/bin/env python3
# Raspberry Pi RGB I2C Rotary Encoder Class
# $Id: rotary_class_rgb_i2c.py,v 1.17 2024/11/25 10:17:30 bob Exp $
#
# Author : Bob Rathbone and Lubos Ruckl (Czech republic)
# Site   : http://www.bobrathbone.com
#
# This class is the driver for the Pimoroni I2C RGB Rotary Encoder 
# See: See https://shop.pimoroni.com/products/rgb-encoder-breakout  
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#
#Change the I2C_ADDR to:
# - 0x1F to use with the Rotary Encoder breakout.
# - 0x18 to use with IO Expander.

import threading
import time,sys
import colorsys
import ioexpander as io
import threading
import pdb
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
I2C_ADDR = 0x1F  # 0x18 for IO Expander, 0x1F for the encoder breakout

PIN_RED = 1
PIN_GREEN = 7
PIN_BLUE = 2

POT_ENC_A = 12
POT_ENC_B = 3
POT_ENC_C = 11

BRIGHTNESS = 0.5                # Fraction of the period that the LED will be on
PERIOD = int(255 / BRIGHTNESS)  # The desired brightness determined by PERIOD

# Event definitions
NO_CHANGE=0
CLOCKWISE=1
ANTICLOCKWISE=2
BUTTONDOWN=3
BUTTONUP=4

Debug = False


class RGB_I2C_RotaryEncoder:
    count = 0
    direction = 0
    xcount = 0
    callback = None
    sEvents = ['NO_CHANGE', 'CLOCKWISE', 'ANTICLOCKWISE', 'BUTTONDOWN']
    i2c_address = 0xF0
    button = 0
    interrupt_pin = 4
    ioe = None

    def __init__(self,i2c_address=0xF0,button=button,callback=callback,interrupt_pin=22):
        self.interrupt_pin = interrupt_pin
        self.callback = callback
        self.button = button
        self.i2c_address = i2c_address
        self.ioe = io.IOE(i2c_address,interrupt_pin)
        t = threading.Thread(target=self._setup,args=(i2c_address,callback,interrupt_pin))
        t.daemon = True
        t.start()

    def _setup(self,i2c_address,callback,interrupt_pin):

        # Swap the interrupt pin for the Rotary Encoder breakout
        self.ioe.enable_interrupt_out(pin_swap=True)

        self.ioe.setup_rotary_encoder(1, POT_ENC_A, POT_ENC_B, pin_c=POT_ENC_C)

        self.ioe.set_pwm_period(PERIOD)
        self.ioe.set_pwm_control(divider=2)  # PWM as fast as we can to avoid LED flicker

        self.ioe.set_mode(PIN_RED, io.PWM, invert=True)
        self.ioe.set_mode(PIN_GREEN, io.PWM, invert=True)
        self.ioe.set_mode(PIN_BLUE, io.PWM, invert=True)
        self.setColor((0,255,0))
        self.setupButton(self.button)
        
    # Setup button interface
    def setupButton(self,button):
        try:
            if button > 0:
                GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                # Add event detection to the GPIO input
                GPIO.add_event_detect(self.button, GPIO.FALLING, callback=self.button_event,
                        bouncetime=150)
        except Exception as e:
            print("Rotary Encoder initialise error " + str(e))
            sys.exit(1)
        
    # Set the RGB shaft colour
    def setColor(self,color):
        r = color[0]
        g = color[1]
        b = color[2]
        self.ioe.output(PIN_RED, r)
        self.ioe.output(PIN_GREEN, g)
        self.ioe.output(PIN_BLUE, b)

    # Need to put run into a thread as it blocks
    def run(self,cycle):
        t = threading.Thread(target=self._run,args=(cycle,))
        t.daemon = True
        t.start()

    # Run routine runs in a thread
    def _run(self,cycle):
        direction = NO_CHANGE
        while True:
            try:
                if self.ioe.get_interrupt():
                    count = self.ioe.read_rotary_encoder(1)
                    if self.xcount == 0:
                        direction = NO_CHANGE
                    elif count > self.xcount:
                        direction = CLOCKWISE
                    elif count < self.xcount:
                        direction = ANTICLOCKWISE
                    else:
                        direction = NO_CHANGE
                    self.xcount = count

                if direction != NO_CHANGE:
                    if cycle:
                        self.cycle(count,direction)
                    self.rotary_event(direction)
                    self.direction = direction
                    self.count = count
                time.sleep(0.05)
                # Don't clear interrupt here. Clear it in the event handler
            except Exception as e:
                print( str(e))

    # Cycle the LEDS
    def cycle(self,count,direction):
        h = (count % 360) / 360.0
        r,g,b = [int(c * PERIOD * BRIGHTNESS) for c in colorsys.hsv_to_rgb(h, 1.0, 1.0)]
        if Debug:
            msg = (self.sEvents[direction],count, r, g, b)
            print(msg)
        self.setColor((r,g,b))

    # Call back routine called by rotary encoder events
    def rotary_event(self, direction):
        if self.ioe.get_interrupt():
            self.callback(direction)
            self.ioe.clear_interrupt()
        

    # Push button up event
    def button_event(self,button):
        # Ignore Button Up events
        if not GPIO.input(button):
            event = BUTTONDOWN
            self.callback(event)
        return

    # Get a button state - returns 1 or 0
    def getButtonState(self, button):
        return  GPIO.input(button)

    def buttonPressed(self,button):
        state = self.getButtonState(button)
        if state == 1:
            pressed = False
        else:
            pressed = True
        return pressed

    # Set the IOE i2c address (Caution - understand before using)
    def set_i2c_addr(self, i2c_addr):
        print("Setting IOE I2C address to %s" % hex(i2c_addr))
        #self.ioe.set_i2c_addr(i2c_addr)
        sys.exit(0)

# End of i2c RGB Rotary Encoder class

if __name__ == "__main__":

    from config_class import Configuration
    config = Configuration()

    volume_i2c = 0x0F
    channel_i2c = 0x1F

    volume_interrupt = 22
    channel_interrupt = 23

    test_volume = False
    test_channel = False

    # Define callbacks
    def volume_callback(event):
        print("Volume rotary encoder event", RGB_I2C_RotaryEncoder.sEvents[event])
        handleEvent(event)

    def channel_callback(event):
        print("Channel rotary encoder event", RGB_I2C_RotaryEncoder.sEvents[event])
        handleEvent(event)

    def mute_event(event):
        print("Mute switch pressed (GPIO %s)" % event)

    def menu_event(event):
        print("Menu switch pressed (GPIO %s)" % event)

    # Handle event if other actions required
    def handleEvent(event):
        return

    def usage():
        print('')
        print("Usage: sudo %s --help " % sys.argv[0])
        print("               --test_volume")
        print("               --test_channel")
        print("               --test_both")
        print("               --volume_i2c=<volume_i2c_address>")
        print("               --channel_i2c=<channel_i2c_address>")
        print('')
        print("Recommended values for volume and channel I2C adresses are 0x0F and 0x1F (defaults)")
        print("Run \"i2cdetect -y 1\" to check I2C address")
        print('')
        sys.exit(0)

    # Text for hex value
    def hexValue(x):
        try:
            int(x,16)
            isHex = True
        except:
            isHex = False
        return isHex

    def get_value(param):
        x,value = param.split('=')
        return value

    volume_i2c = config.volume_rgb_i2c
    channel_i2c = config.channel_rgb_i2c

    # Get command line parameters
    for i in range(1,len(sys.argv)):
        param = sys.argv[i]
        if param == "--help":
            usage()

        elif "--test_volume" in param:
            test_volume = True

        elif "--test_channel" in param:
            test_channel = True

        elif "--test_both" in param:
            test_volume = True
            test_channel = True

        elif "--volume_i2c" in param:
            value = get_value(param)
            if hexValue(value):
                volume_i2c = int(value,16)
            else:
                print("Invalid volume encoder hex value %s specified" % value)
                exit(1)

        elif "--channel_i2c" in param:
            value = get_value(param)
            if hexValue(value):
                channel_i2c = int(value,16)
            else:
                print("Invalid channel encoder hex value %s specified" % value)
                exit(1)
        else:
            print("Invalid parameter %s" % param)
            usage()

    # Check that at least one encoder is being tested
    if not test_volume and not test_channel:
        print ("\nYou must specify at least one encoder to be tested!")
        usage()

    # Start of test
    print("RGB I2C Dual Rotary Encoder Test")

    cycle=True # Cycle colours when encoder knob turned

    if test_volume:
        print("Volume rotary encoder I2C address=%s Interrupt pin %d" % (hex(volume_i2c),volume_interrupt))
        mute_switch = config.getSwitchGpio("mute_switch")
        print("Mute switch GPIO", mute_switch)
        try:
            volume_encoder = RGB_I2C_RotaryEncoder(volume_i2c,mute_switch,
                            volume_callback,volume_interrupt)
            volume_encoder.run(cycle)
        except Exception as e:
            print(str(e))
            print("Check volume rotary encoder I2C address %s matches device" % hex(volume_i2c))
            sys.exit(1)

    if test_channel:
        print("Channel rotary encoder I2C address=%s Interrupt pin %d" % (hex(channel_i2c),channel_interrupt))
        menu_switch = config.getSwitchGpio("menu_switch")
        print("Menu switch GPIO", menu_switch)
        try:
            channel_encoder = RGB_I2C_RotaryEncoder(channel_i2c,menu_switch,
                            channel_callback,channel_interrupt)
            channel_encoder.run(cycle)
        except Exception as e:
            print(str(e))
            print("Check channel rotary encoder I2C address %s matches device" % hex(channel_i2c))
            sys.exit(1)

    colors = [(255,0,0),(255,255,0),(255,255,255),(0,255,0),(0,255,255),
              (255,0,255),(0,0,255),(255,64,64),(64,64,255),(255,0,0)]

    try:
        print("Started")
        while True:
            for color in colors:
                time.sleep(5)
                if test_volume:
                    volume_encoder.setColor(color)
                if test_channel:
                    channel_encoder.setColor(color)

    except KeyboardInterrupt:
        print(" Stopped")
        sys.exit(0)

# End of script

# set tabstop=4 shiftwidth=4 expandtab
# retab
