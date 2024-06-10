#!/usr/bin/env python3
#       
# Raspberry Pi remote control daemon
# $Id: ireventd.py,v 1.24 2024/05/24 11:01:06 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#       The authors shall not be liable for any loss or damage however caused.
#
# The important configuration files are
#   /etc/rc_keymaps ir-keytable .toml configuration files
#   <myremote>.toml ir-keytable definition file
#
# This is the Python 3 version for use on Bullseye
#
# This class is calls the ir_daemon.py class to daemonize this process
# It is normally called from ireventd.service

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
from evdev import *
from threading import Timer

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

config = Configuration()
pidfile = '/var/run/ireventd.pid'
key_maps = '/etc/rc_keymaps'
sys_rc = '/sys/class/rc'
rc_device = ''


# Signal SIGTERM handler
def signalHandler(signal,frame):
    global log
    pid = os.getpid()
    log.message("Remote control stopped, PID " + str(pid), log.INFO)
    sys.exit(0)

# Daemon class
class RemoteDaemon(Daemon):

    keytable = 'myremote.toml'
    keymaps = '/etc/rc_keymaps'
    ir_device = 'rc0'	# Can be rc0, rc1, rc2, rc4 - Run ir-keytable 
    play_number = 0
    timer_running = False
    timer = None

    def run(self):
        global remote_led
        global udpport
        global udphost

        log.init('radio')
        progcall = str(sys.argv)
        log.message(progcall, log.DEBUG)
        log.message('Remote control running pid ' + str(os.getpid()), log.INFO)
        signal.signal(signal.SIGHUP,signalHandler)

        msg = "Using IR kernel events architecture"
        print(msg)
        log.message(msg, log.DEBUG)


        remote_led = config.remote_led
        if remote_led > 0:
            print("Flashing LED on GPIO", remote_led)
            GPIO.setwarnings(False)      # Disable warnings
            GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
            GPIO.setup(remote_led, GPIO.OUT)  # Output LED
            self.flash_led(remote_led)
        else:
            log.message("Remote control LED disabled", log.DEBUG)

        self.ir_device = self.get_ir_device('gpio_ir_recv')

        print("Using device /sys/class/rc/" + self.ir_device)

        udphost = config.remote_control_host
        udpport = config.remote_control_port
        log.message("UDP connect host " + udphost + " port " + str(udpport), log.DEBUG)

        devices = [InputDevice(path) for path in list_devices()]
        #print("DEBUG " + str(devices))

        self.keytable = config.keytable 
        self.loadKeyTable(self.keytable)

        # Define IR input as defined in /boot/config.txt
        irin = None
        for device in devices:
            print(device.path, device.name, device.phys)
            if(device.name=="gpio_ir_recv"):
                irin = device

        if(irin == None):
            print("Unable to find IR input device, exiting")
            exit(1)

        self.listener(irin)

    # Returns the device name for the "gpio_ir_recv" overlay (rc0...rc6)
    # Used to load ir_keytable
    def get_ir_device(self,sName):
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

    # Used by KEY_NUMERIC_x entries 
    def timerTask(self):
        msg = 'IR event PLAY_' + str(self.play_number)
        log.message(msg, log.DEBUG)
        if self.play_number > 0:
            print('PLAY_' + str(self.play_number))
            reply = self.udpSend('PLAY_' + str(self.play_number))
            print(reply)
        self.timer_running = False
        self.timer.cancel()
        self.play_number = 0

    # Load the specified key table into /etc/rc_keymaps/
    def loadKeyTable(self,keytable):
        log.message("Loading " + self.keytable, log.DEBUG)
        cmd = "sudo /usr/bin/ir-keytable -c -w " + self.keymaps + "/" + keytable + " -s " + self.ir_device
        print(cmd) 
        execCommand("sudo /usr/bin/ir-keytable -c -w " + self.keymaps + "/" + keytable
		    + " -s " + self.ir_device)

    # Handle the IR input event
    def readInputEvent(self,device):
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
                if remote_led > 0:
                    GPIO.output(remote_led, True)

                # Or use categorize. This is more useful if we want to write a function to
                # return a text representation of the button press on a key down
                data = categorize(event)
               
                if data.keystate > 0:
                    if len(data.keycode) == 2:
                        keycode = data.keycode[1]
                    else:
                        keycode = data.keycode

                    print(keycode,hex(data.scancode),data.keystate)
    
                    if 'KEY_NUMERIC_' in keycode :
                        playnum = int(keycode.split('_')[2])

                        if self.play_number > 0:
                            self.play_number *= 10

                        self.play_number += playnum
                        if not self.timer_running:
                            self.timer = Timer(2, self.timerTask, args=None)
                            self.timer.start()
                            self.timer_running = True
                    else:
                        print(keycode)
                        reply = self.udpSend(keycode)
                        print(reply)

                if remote_led > 0:
                    GPIO.output(remote_led, False)

    # Listener  routine
    def listener(self,irin):
        print("Listening for IR events:")
        while True:
            self.readInputEvent(irin)

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
        reply = self.udpSend(msg)
        return reply

    # Flash the IR activity LED
    def flash_led(self,led):
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
            
    # Test the LED
    def flash(self):
        log.init('radio')
        remote_led = config.remote_led
        if remote_led > 0:
            GPIO.setwarnings(False)      # Disable warnings
            GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
            GPIO.setup(remote_led, GPIO.OUT)  # Output LED
            self.flash_led(remote_led)
        return

    # Send button data to radio program
    def udpSend(self,button):
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

# get gpio-ir dtoverlay configuration and port configuration
def getBootConfig(str):
    file = "/boot/config.txt"
    if os.path.exists("/boot/firmware/config.txt"):      
        file = "/boot/firmware/config.txt"

    f = open(file, "r")
    msg = 'Warning: dtoverlay gpio-ir not configured in ' + file
    for line in f:
        if re.search(str, line):
            msg = line
    return msg

# Display configuration
def displayConfiguration():
    global rc_device
    print("Remote Control daemon configuration")
    print("-----------------------------------")
    config = Configuration()
    print("LED = GPIO " + str(config.remote_led))
    print("HOST = " + config.remote_control_host)
    print("PORT = " + str(config.remote_control_port))
    print("LISTEN = " + str(config.remote_control_port))
    line = getBootConfig("^dtoverlay=gpio-ir")
    if line != None:
        print(line.rstrip())

    mods = execCommand("lsmod | grep -i gpio_ir_recv")
    if len(mods) > 0:
        x = mods.split(' ')
        print ("Module %s loaded" % x[0])
    else:
        print ("ERROR: Module gpio_ir_recv not loaded, missing gpio-ir overlay")

    daemon.get_ir_device('gpio_ir_recv')
    print('Sysfs: ' + rc_device)
   
    protos = execCommand("cat " + rc_device + '/protocols')
    print('Protocols ' + protos) 

    for file in os.listdir(key_maps):
        if file.endswith(".toml"):
            print("Key map: " + os.path.join(key_maps, file))

### Main routine ###
if __name__ == "__main__":

    if pwd.getpwuid(os.geteuid()).pw_uid > 0:
        print("This program must be run with sudo or root permissions!")
        usage()

    daemon = RemoteDaemon(pidfile)
    if len(sys.argv) >= 2:
        if 'start' == sys.argv[1]:
            daemon.start()
            daemon.flash_led()
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
            displayConfiguration()
        else:
            print("Unknown command: " + sys.argv[1])
            usage()
        sys.exit(0)
    else:
        usage()

# set tabstop=4 shiftwidth=4 expandtab
# retab

# End of script

