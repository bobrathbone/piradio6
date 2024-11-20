#!/usr/bin/env python3
# Raspberry Pi Button Push Button Class
# $Id: test_events.py,v 1.3 2002/02/19 16:23:27 bob Exp $
#
# IR remote tester
# Assumes device already configured with ir-keytable
#
# Author: Dave Hartburn 
# Website: https://samndave.org.uk
#
# Modified: Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
#

from evdev import *
import pdb 
import sys 
import os 

devices = [InputDevice(path) for path in list_devices()]
# Define IR input as defined in /boot/config.txt
irin = None
for device in devices:
    print(device.path, device.name, device.phys)
    if(device.name=="gpio_ir_recv"):
        irin = device

if(irin == None):
    print("Unable to find IR input device, exiting")
    exit(1)

print("IR input device found at", irin.path)

config1_txt = "/boot/firmware/config.txt"
config2_txt = "/boot/config.txt"

if os.path.exists(config1_txt):
    config_txt = config1_txt
else:
    config_txt = config2_txt

print("Boot configuration in", config_txt)
with open(config_txt, 'r') as f:
    for line in f.readlines():
        if 'gpio-ir' in line:
            line = line.rstrip()
            print(line)

# Read events and return string
def readInputEvent(device):
    try:
        print("Press Ctl-C to end events test")
        print("Waiting for IR events")
        for event in device.read_loop():
            # Event returns sec, usec (combined with .), type, code, value
            # Type 01 or ecodes.EV_KEY is a keypress event
            # A value of  0 is key up, 1 is key down, 2 is repeat key
            # the code is the value of the keypress
            # Full details at https://python-evdev.readthedocs.io/en/latest/apidoc.html

            # However we can use the categorize structure to simplify things
            # data.keycode - Text respresentation of the key
            # data.keystate - State of the key, may match .key_down or .key_up
            # data.scancode - Key code
            # See https://python-evdev.readthedocs.io/en/latest/apidoc.html#evdev.events.InputEvent
            if event.type == ecodes.EV_KEY:
                if(event.code == ecodes.KEY_8 and event.value==1):
                    print("Detected keydown event on the 8")

                # Or use categorize. This is more useful if we want to write a function to
                # return a text representation of the button press on a key down
                data = categorize(event)
                #print(dir(data))
                if data.keystate > 0:
                    #pdb.set_trace()
                    if len(data.keycode) == 2:
                        keycode = data.keycode[1]
                    else:
                        keycode = data.keycode
                    print(keycode,hex(data.scancode),data.keystate)

    except KeyboardInterrupt:
        print("")
        print("End of IR events test")
        sys.exit(0)

while True:
    readInputEvent(irin)

# set tabstop=4 shiftwidth=4 expandtab
# retab
