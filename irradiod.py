#!/usr/bin/env python3
#       
# Raspberry Pi remote control daemon
# $Id: irradiod.py,v 1.5 2022/02/11 14:27:38 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program uses LIRC (Linux Infra Red Control) and python-lirc
#
# For Raspbian Bullseye and possibly later run:
#   apt install lirc python-lirc
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#       The authors shall not be liable for any loss or damage however caused.
#
# The important configuration files are
#   /etc/lirc/lircrc Program to event registration file
#   /etc/lircd.conf  User generated remote control configuration file
#
# This program  is the Python 3 version for Bullseye or later
# For the Python2 (Buster) version see remote_control.py and rc_daemon.py

import RPi.GPIO as GPIO
import configparser
import sys
import pwd
import os
import time
import signal
import socket
import errno
import re
import pdb
import pylirc

# Radio project imports
from config_class import Configuration
from ir_daemon import Daemon
from log_class import Log

log = Log()
IR_LED=11   # GPIO 11 pin 23
remote_led = IR_LED
muted = False
udphost = 'localhost'   # IR Listener UDP host default localhost
udpport = 5100      # IR Listener UDP port number default 5100
blocking = 1

config = Configuration()

pidfile = '/var/run/irradiod.pid'
lircrc = '/etc/lirc/lircrc'
lircd_service = '/lib/systemd/system/lircd.service'

# Signal SIGTERM handler
def signalHandler(signal,frame):
    global log
    pid = os.getpid()
    log.message("Remote control stopped, PID " + str(pid), log.INFO)
    sys.exit(0)

# Daemon class
class RemoteDaemon(Daemon):

    def run(self):
        global remote_led
        global udpport
        global udphost

        log.init('radio')
        progcall = str(sys.argv)
        log.message(progcall, log.DEBUG)
        log.message('Remote control running pid ' + str(os.getpid()), log.INFO)
        signal.signal(signal.SIGHUP,signalHandler)

        # Start lirc service
        if os.path.exists(lircd_service):
            log.message("Starting lircd daemon", log.DEBUG)
            execCommand('sudo systemctl start lircd')   # For Stretch       
            time.sleep(1)
            # Load all IR protocols if ir-keytable installed
            if os.path.exists("/usr/bin/ir-keytable"):
                execCommand('sudo ir-keytable -p all')
            
        else:
            # Earlier Jessie and Stretch OS
            log.message("Starting lirc daemon", log.DEBUG)
            execCommand('sudo service lirc start')  # For Jessie

        remote_led = config.remote_led
        if remote_led > 0:
            print("Flashing LED on GPIO", remote_led)
            GPIO.setwarnings(False)      # Disable warnings
            GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
            GPIO.setup(remote_led, GPIO.OUT)  # Output LED
            flash_led(remote_led)
        else:
            log.message("Remote control LED disabled", log.DEBUG)
        udphost = config.remote_control_host
        udpport = config.remote_control_port
        log.message("UDP connect host " + udphost + " port " + str(udpport), log.DEBUG)
        listener()

    # Status enquiry
    def status(self):
        # Get the pid from the pidfile
        try:
            pf = open(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "Remote control status: not running"
            log.message(message, log.INFO)
            print(message)
        else:
            message = "Remote control running pid " + str(pid)
            log.message(message, log.INFO)
            print(message)
        return

    # Test udp send
    def send(self,msg):
        reply = udpSend(msg)
        return reply
        
    # Test the LED
    def flash(self):
        log.init('radio')
        remote_led = config.remote_led
        if remote_led > 0:
            GPIO.setwarnings(False)      # Disable warnings
            GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
            GPIO.setup(remote_led, GPIO.OUT)  # Output LED
            flash_led(remote_led)
        return

# End of class overrides

# The main Remote control listen routine
def listener():
    try:
        sockid = pylirc.init("piradio", lircrc, blocking)

        log.message("Listener on socket " + str(socket) + " established", log.DEBUG)

        # Main Listen loop
        print("Listening for input on IR sensor")
        while True:
            #pdb.set_trace()

            nextcode =  pylirc.nextcode()

            # For Jessie amend pylirc.nextcode to lirc.nextcode

            if nextcode != None and len(nextcode) > 0:
                if remote_led > 0:
                    GPIO.output(remote_led, True)
                button = nextcode[0]
                log.message(button, log.DEBUG)
                print(button)
                udpSend(button) # Send to radiod program
                if remote_led > 0:
                    GPIO.output(remote_led, False)
            else:
                time.sleep(0.2)

    except Exception as e:
        log.message(str(e), log.ERROR)
        print(str(e))
        mesg = "Possible configuration error, check /etc/lirc/lircd.conf"
        log.message(mesg, log.ERROR)
        print(mesg)
        mesg = "Activation IR Remote Control failed - Exiting"
        log.message(mesg, log.ERROR)
        print(mesg)
        sys.exit(1)

# The main Remote control listen routine

# Send button data to radio program
def udpSend(button):
    global udpport
    data = ''
    log.message("Remote control daemon udpSend " + button, log.DEBUG)
    
    # The host to send to is either local host or the IP address of the remote server
    udphost = config.remote_listen_host
    try:
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        clientsocket.settimeout(3)
        button = button.encode('utf-8')
        clientsocket.sendto(button, (udphost, udpport))
        data = clientsocket.recv(100).strip()
        clientsocket.close()

    except socket.error as e:
        err = e.args[0]
        if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
            msg = "IR remote udpSend no data: " + str(e)
            print(msg)
            log.message(msg, log.ERROR)
        else:
            # Errors such as timeout
            msg = "IR remote udpSend: " + str(e)
            print(msg)
            log.message(msg , log.ERROR)

    if len(data) > 0:
        data = data.decode('utf-8')
        log.message("IR daemon server sent: " + data, log.DEBUG)
    return data

# Flash the IR activity LED
def flash_led(led):
    count = 6
    delay = 0.3
    log.message("Flash LED on GPIO " + str(led), log.DEBUG)

    while count > 0:
        GPIO.output(led, True)
        time.sleep(delay)
        GPIO.output(led, False)
        time.sleep(delay)
        count -= 1
    return

# Execute system command
def execCommand(cmd):
    p = os.popen(cmd)
    return  p.readline().rstrip('\n')

# Print usage
def usage():
    print(("Usage: sudo %s start|stop|status|nodaemon|flash|config|send <KEY>" % sys.argv[0]))
    sys.exit(2)

def usageSend():
    print(("Usage: %s send <KEY>" % sys.argv[0]))
    print ("Where <KEY> is a valid IR_KEY")
    print ("   KEY_VOLUMEUP,KEY_VOLUMEDOWN,KEY_CHANNELUP,KEY_CHANNELDOWN,")
    print ("   KEY_UP,KEY_DOWN,KEY_LEFT,KEY_RIGHT,KEY_OK,KEY_INFO,KEY_MUTE")
    sys.exit(2)

def getBootConfig(str):
    f = open("/boot/config.txt", "r")
    for line in f:
        if re.search(str, line):
            return line

### Main routine ###
if __name__ == "__main__":

    if pwd.getpwuid(os.geteuid()).pw_uid > 0:
        print("This program must be run with sudo or root permissions!")
        usage()
        sys.exit(1)

    daemon = RemoteDaemon('/var/run/remote.pid')
    if len(sys.argv) >= 2:
        if 'start' == sys.argv[1]:
            daemon.start()
            daemon.flash()
        elif 'nodaemon' == sys.argv[1]:
            daemon.nodaemon()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'flash' == sys.argv[1]:
            daemon.flash()
        elif 'status' == sys.argv[1]:
            daemon.status()
        elif 'send' == sys.argv[1]:
            msg = 'IR_REMOTE'
            if len(sys.argv) > 2:   
                msg = sys.argv[2]
                reply = daemon.send(msg)
                print(reply)
            else:
                usageSend()
        elif 'config' == sys.argv[1]:
            config = Configuration()
            print("LED = GPIO " + str(config.remote_led))
            print("HOST = " + config.remote_control_host)
            print("PORT = " + str(config.remote_control_port))
            print("LISTEN = " + str(config.remote_control_port))
            line = getBootConfig("^dtoverlay=lirc-rpi") 
            if line != None:
                print(line)
            line = getBootConfig("^dtoverlay=gpio-ir")  
            if line != None:
                print(line)
        else:
            print("Unknown command: " + sys.argv[1])
            usage()
        sys.exit(0)
    else:
        usage()

# End of script

# set tabstop=4 shiftwidth=4 expandtab
# retab
