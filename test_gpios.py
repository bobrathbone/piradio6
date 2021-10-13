#!/usr/bin/env python3
# Raspberry Pi test all available GPIOs
#
# $Id: test_gpios.py,v 1.11 2021/10/03 09:52:24 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#

import RPi.GPIO as GPIO
import sys,time 

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#pins = (4,)
pins = (2,3,4,5,6,7,8,9,10,11,12,13,14,15,17,18,19,20,21,22,23,24,25,26,27)

def gpio_event(gpio):
    state = GPIO.input(gpio)
    if state == 1:
        sState = "rising"
    else: 
        sState = "falling"
    print("GPIO %s %s " % (gpio,sState))

def usage():
    print("Usage: %s <--help> <--pull_up> <--pull_down> <--none>" % (sys.argv[0]))
    print("Where --help this help text")
    print("      --pull_up Set pull-up-down internal resistors high (+3.3V)")
    print("      --pull_down Set pull-up-down internal resistors low (0V GND)")
    print("      --pull_off No pull-up-down internal resistors (Use external resistors)")
    sys.exit(0)

# Main program
pull_up_down = GPIO.PUD_UP

if len(sys.argv) >= 2:
    if '--help' == sys.argv[1]:
        usage()
    elif '--pull_down' == sys.argv[1]:
        pull_up_down = GPIO.PUD_DOWN
    elif '--pull_up' == sys.argv[1]:
        pull_up_down = GPIO.PUD_UP
    elif '--pull_off' == sys.argv[1]:
        pull_up_down = GPIO.PUD_OFF
else:
    usage()

for pin in range (0,len(pins)):
    gpio_pin = pins[pin]
    try:
        GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        time.sleep(0.1)
        if  GPIO.input(gpio_pin) > 0:
            sState = 'High'
        else:
            sState = 'Low'
        #print('GPIO: %s State:%s' % (str(gpio_pin), GPIO.input(gpio_pin)))
        print('GPIO: %s State:%s' % (str(gpio_pin),sState))
        # Add event detection to the GPIO inputs
        GPIO.add_event_detect(gpio_pin, GPIO.BOTH,callback=gpio_event, bouncetime=100)
    except Exception as e:
        print("Error: GPIO",gpio_pin, e)     
        print("Check conflict with GPIO %s in other programs or in /boot/config.txt" % gpio_pin)
        with open('/boot/config.txt', 'r') as f:
            x = '=' + str(gpio_pin)
            for line in f.readlines():
                if x in line:
                    line = line.rstrip()
                    print(line)

print("Waiting for input events:")

try:
    while True:
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nEnd of GPIOs test")
    GPIO.cleanup()
    sys.exit(0)

# set tabstop=4 shiftwidth=4 expandtab
# retab
