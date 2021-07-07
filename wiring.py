#!/usr/bin/env python3
#
# Raspberry Pi Internet Radio
# This program produces a wiring diagram based on the 
#      configuration in the /etc/radiod.conf file

# $Id: wiring.py,v 1.6 2021/05/25 05:41:04 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#       The authors shall not be liable for any loss or damage however caused.
#

import os,sys
import pwd
import subprocess

from config_class import Configuration

config = Configuration()
bootconfig = "/boot/config.txt"

switch_labels = [ "left_switch",
          "right_switch",
          "GND_0V",
          "mute_switch",
          "down_switch",
          "up_switch",
          "GND_0V",
          "menu_switch",
        ]

switch_details = { "left_switch": 'A',
           "right_switch": 'B',
           "GND_0V": 'C',
           "mute_switch": '< GND 0V',
           "down_switch": 'A',
           "up_switch": 'B',
           "menu_switch": '< GND 0V',
         }

lcd_labels = [  'lcd_data4',
        'lcd_data5',
        'lcd_data6',
        'lcd_data7',
        'lcd_enable',
        'lcd_select',
         ]

lcd_pins = {    'lcd_data4': 11,
        'lcd_data5': 12,
        'lcd_data6': 13,
        'lcd_data7': 14,
        'lcd_enable': 6,
        'lcd_select': 4,
         }

other_labels = ['remote_led',
        'I2C_Data',
        'I2C_Clock',
        'IR_Remote',
         ]

pullupdown = ['DOWN', 'UP']
voltages   = ['+3.3V', 'GND(0V)']


# GPIO to Physical pins translation Format: <gpio>:<pysical pin>
pins = { 0:6, 2:3, 3:5, 4:7, 5:29, 6:31, 7:26, 8:24, 9:21, 10:19, 
    11:23, 12:32, 13:33, 14:8, 15:10, 16:36, 17:11, 18:12, 19:35, 
    20:38, 21:40, 22:15, 23:16, 24:18, 25:22, 26:37, 27:13,  }

# Display the Switch wiring
def displaySwitch(config,params):
    print('--------------- SWITCHES ----------------')
    print("GPIO","\tPin\t    Switch\t   Rotary")
    print("====","\t===\t    ======\t   ======")
    for label in switch_labels:
        pin = 0
        gpio = 0
        if label is not 'GND_0V':
            gpio = config.getSwitchGpio(label)
        rotary = switch_details[label]
        try:
            pin = pins[gpio]
            if not params:
                label = label.replace('_', ' ')
                label = label.capitalize()
            print(" %2.d\t%2.d <------> %-12s   %s" % (gpio, pin, label, rotary))
        except:
            print("Invalid GPIO", label + '=' + str(gpio))
    print()
    print("Pull Up/Down resistors", pullupdown[config.pull_up_down])
    print()
    print("Push button switches must be wired to " + voltages[config.pull_up_down])
    print("Rotary push switches must always be wired to GND 0V")
    print()
    return

# Display the LCD wiring
def displayLCD(config,params):
    print('----------------- LCD ------------------')
    print("GPIO","\tPin\t    Function\tLCD pin")
    print("====","\t===\t    ========\t=======")
    for label in lcd_labels:
        pin = 0
        gpio = 0
        #if label is not 'GND_0V' or label is not 'LCD Contrast':
        gpio = config.getLcdGpio(label)
        lcd_pin = lcd_pins[label]
        try:
            pin = pins[gpio]
            if not params:
                label = label.replace('_', ' ')
                label = label.capitalize()
            print(" %2.d\t%2.d <------> %-12s %2d" % (gpio, pin, label, lcd_pin))
        except:
            print("Invalid GPIO", label + '=' + str(gpio))
        
    pin = 2
    label = 'VCC +5V'   
    print(" \t%2.d <------> %-12s  %s" % (pin, label, '2,15'))
    pin = 6
    label = 'GND 0V'    
    print(" \t%2.d <------> %-12s  %s" % (pin, label, '1,16'))
    label = 'Contrast'  
    print(" 10K Pot   <------> %-12s  %d" % (label, 3))
    print()
    return

# Get lirc configuration from boot.txt
def getLircGpio():
    cmd = "grep lirc " + bootconfig + " | grep gpio | awk -F ',' '{print $2}'"
    x = subprocess.getstatusoutput(cmd)
    x = x[1]
    x = x.replace('gpio_in_pin=', '' )
    try:
        gpio = int(x)
    except:
        gpio = -1
    return gpio


def displayOther(config,params):
    print('----------- OTHER ------------')
    print("GPIO","\tPin\t    Function")
    print("====","\t===\t    ========")
    for label in other_labels:
        pin = 0
        gpio = 0
        comment = ''
        if label is 'remote_led':
            gpio = config.remote_led
            if not params:
                label = label.capitalize()
        elif label is 'I2C_Clock':
            gpio = 2 
        elif label is 'I2C_Data':
            gpio = 3 
        elif label is 'IR_Remote':
            gpio = getLircGpio()
            comment = "(See " + bootconfig + ")"

        try:
            if gpio > 0:
                pin = pins[gpio]
                if not params:
                    label = label.replace('_', ' ')
                print(" %2.d\t%2.d <------> %-12s %s" % (gpio, pin, label, comment))
        except:
            print("Invalid GPIO", label + '=' + str(gpio))
    print()
    return

def usage():
    print("Usage: %s -p -h" % (sys.argv[0]))
    print("Where -p print parameters, -h this help text")
    sys.exit(0)

# Main program

params = False 
if len(sys.argv) > 1:
    if  '-p'== sys.argv[1] :
        params = True
    elif '-h' == sys.argv[1]:
        usage()
    else:
        usage()

print("Radio wiring scheme based upon configuration in /etc/radiod.conf")
print("================================================================")
print()

displaySwitch(config,params)
displayLCD(config,params)
displayOther(config,params)


# End of program
