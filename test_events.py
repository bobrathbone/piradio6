#!/usr/bin/env python3
# Raspberry Pi test remote control kernel events
# $Id: test_events.py,v 1.6 2024/12/20 14:23:58 bob Exp $
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

raw = False
info = False
sys_rc = '/sys/class/rc'
rc_device = ''

def usage():
    print("Usage: %s <--help> <--raw>|<--config>" % (sys.argv[0]))
    print("Where --help    This help text")
    print("      --raw     Display raw codes")
    print("      --config  Display configuration only")
    sys.exit(0)

if len(sys.argv) >= 2:
    if '--help' == sys.argv[1] or '-h' == sys.argv[1]:
        usage()
    elif '--config' == sys.argv[1] or '-c' == sys.argv[1]:
        info = True
    elif '--raw' == sys.argv[1] or '-r' == sys.argv[1]:
        raw = True
    else:
        usage()

# Returns the device name for the "gpio_ir_recv" overlay (rc0...rc6)
# Used to load ir_keytable
def get_ir_device(sName):
    global rc_device
    found = False
    for x in range(7):
        name = ''
        device = ''
        for y in range(7):
            file = sys_rc + '/rc' + str(x) + '/input' + str(y) + '/name'
            if os.path.isfile (file):
                try:
                    f = open(file, "r")
                    name = f.read()
                    name = name.strip()
                    if (sName == name):
                        device = 'rc' + str(x)
                        rc_device = sys_rc + '/rc' + str(x)
                        found = True
                        break
                    f.close()
                except Exception as e:
                    print(str(e))
        if found:
            break

    return device

devices = [InputDevice(path) for path in list_devices()]
# Define IR input as defined in /boot/config.txt
irin = None
for device in devices:
    if(device.name=="gpio_ir_recv"):
        print(device.path, device.name, device.phys)
        irin = device

if(irin == None):
    print("Unable to find IR input device, exiting")
    exit(1)

rc_device = get_ir_device('gpio_ir_recv')
print("Kernel event device " +  rc_device)
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

# Configuration information only
if info:
    sys.exit(0)

# Read events and return string
def readInputEvent(device):
    try:
        print("Press Ctl-C to end events test")
        print("Waiting for IR events")
        if raw:
            print("Listening in raw mode")

        for event in device.read_loop():
            if raw:
                print(event)
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
