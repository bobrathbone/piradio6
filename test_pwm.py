#!/usr/bin/env python3
# test_pwm.py 
# Author: Fgmnts https://github.com/fgmnts
# Change the led GPIO number to the GPIO your led is connected to
# Copy this file to the next directory up
# cp test_pwm.py ../.
# cd ../
# ./test_pwm.py

from RPi import GPIO
import time

led = 16

GPIO.setmode(GPIO.BCM)

GPIO.setup(led, GPIO.OUT)
pwm_led1 = GPIO.PWM(led, 100)
pwm_led1.start(10)
try:
    while True:
        pwm_led1.ChangeDutyCycle(10)
        time.sleep(0.8)
        pwm_led1.ChangeDutyCycle(50)
        time.sleep(0.8)
        pwm_led1.ChangeDutyCycle(100)
        time.sleep(0.8)
        pwm_led1.ChangeDutyCycle(0)
        time.sleep(0.8)
except KeyboardInterrupt as e:
    print(e)
finally:
    pwm_led1.stop()
    GPIO.cleanup()
    print("script stop")

