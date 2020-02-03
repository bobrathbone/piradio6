#!/usr/bin/env python
import RPi.GPIO as GPIO
import time 

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pins = (2,3,4,5,6,7,8,9,10,11,12,13,14,15,17,18,19,20,21,22,23,24,25,26,27)

def event():
        return False

for pin in range (0,len(pins)):
        gpio_pin = pins[pin]
	print "GPIO",gpio_pin
	try:
		GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		print ('GPIO: '+ str(gpio_pin), GPIO.input(gpio_pin))

		# Add event detection to the GPIO inputs
		GPIO.add_event_detect(gpio_pin, GPIO.FALLING,
					callback=event, bouncetime=200)
	except Exception as e:
		print "Error: GPIO",gpio_pin, e     
