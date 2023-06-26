#!/usr/bin/env python3
# Raspberry Pi Button Push Button Class
# $Id: test_mpc_events.py,v 1.2 2023/03/04 10:53:06 bob Exp $
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
import subprocess

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


# Execute a system command
def execCommand(cmd):
    p = os.popen(cmd)
    return  p.readline().rstrip('\n')
                
# Read events and return string
def readInputEvent(device):
    execCommand("sudo /usr/bin/ir-keytable -c -w /etc/rc_keymaps/myremote.toml")
    muted = False
    volume = 70

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

                # Issue MPC commands
                cmd = "mpc play "
                channel = None
                if(event.code == ecodes.KEY_1 and event.value==1):
                    channel = 1
                elif(event.code == ecodes.KEY_2 and event.value==1):
                    channel = 2
                elif(event.code == ecodes.KEY_3 and event.value==1):
                    channel = 3
                elif(event.code == ecodes.KEY_4 and event.value==1):
                    channel = 4
                elif(event.code == ecodes.KEY_5 and event.value==1):
                    channel = 5
                elif(event.code == ecodes.KEY_6 and event.value==1):
                    channel = 6
                elif(event.code == ecodes.KEY_7 and event.value==1):
                    channel = 7
                elif(event.code == ecodes.KEY_8 and event.value==1):
                    channel = 8
                elif(event.code == ecodes.KEY_9 and event.value==1):
                    channel = 9
                elif(event.code == ecodes.KEY_0 and event.value==1):
                    channel = 10
                if channel != None:
                    cmd = cmd + str(channel)
                    print(cmd)
                    execCommand(cmd)
                    continue

                # Control commands
                if(event.code == ecodes.KEY_CHANNELUP and event.value==1):
                    execCommand("mpc next")
                elif(event.code == ecodes.KEY_CHANNELDOWN and event.value==1):
                    execCommand("mpc prev")
                elif(event.code == ecodes.KEY_MUTE and event.value==1):
                    if muted:
                        execCommand("mpc play")
                        muted = False
                    else:
                        execCommand("mpc pause")
                        muted = True
                elif(event.code == ecodes.KEY_VOLUMEUP and (event.value==1 or event.value==2)):
                    volume += 10   
                    if volume  > 100:
                        volume = 100
                    execCommand("mpc volume " + str(volume))
                elif(event.code == ecodes.KEY_VOLUMEDOWN and (event.value==1 or event.value==2)):
                    volume -= 10   
                    if volume  < 1:
                        volume = 1
                    execCommand("mpc volume " + str(volume))
                    

while True:
    readInputEvent(irin)

# set tabstop=4 shiftwidth=4 expandtab
# retab
