#!/usr/bin/env python
#       
# Raspberry Pi remote control daemon
# $Id: remote_control.py,v 1.18 2019/08/29 09:48:16 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program uses LIRC (Linux Infra Red Control) and python-pylirc
# For Raspbian Buster run:
# 	apt-get install lirc python-pylirc
#
# For Raspbian Jessie run:
# 	apt-get install lirc python-lirc
# and amend all statements containing pylirc to lirc
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	    The authors shall not be liable for any loss or damage however caused.
#
# The important configuration files are
# 	/etc/lirc/lircrc Program to event registration file
#	/etc/lircd.conf	 User generated remote control configuration file
#

import RPi.GPIO as GPIO
import ConfigParser
# import lirc # For Raspbian Jessie only
#import pylirc
import sys
import pwd
import os
import time
import signal
import socket
import errno
import pdb

# Radio project imports
from config_class import Configuration
from rc_daemon import Daemon
from log_class import Log

log = Log()
IR_LED=11	# GPIO 11 pin 23
remote_led = IR_LED
muted = False
udphost = 'localhost'	# IR Listener UDP host default localhost
udpport = 5100		# IR Listener UDP port number default 5100
blocking = 1
use_pylirc = False	# For Buster use pylirc module instead of lirc 

config = Configuration()

pidfile = '/var/run/irradiod.pid'
lircrc = '/etc/lirc/lircrc'
lircd_service = '/lib/systemd/system/lircd.service'
pylirc_module='/usr/lib/python2.7/dist-packages/pylircmodule.so'

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
		global use_pylirc

		log.init('radio')
		progcall = str(sys.argv)
		log.message(progcall, log.DEBUG)
		log.message('Remote control running pid ' + str(os.getpid()), log.INFO)
		signal.signal(signal.SIGHUP,signalHandler)

		#pdb.set_trace()
		# In Buster the lirc module has been renamed to pylirc
		if os.path.exists(pylirc_module):
			msg = "Using pylirc module"
			print msg
			log.message(msg, log.DEBUG)
			import pylirc
			global pylirc
			use_pylirc = True
		else:
			msg = "Using lirc module"
			print msg
			log.message(msg, log.DEBUG)
			import lirc
			global lirc
			
		# Start lirc service
		if os.path.exists(lircd_service):
			log.message("Starting lircd daemon", log.DEBUG)
			execCommand('sudo systemctl start lircd')	# For Stretch		
			time.sleep(1)
			# Load all IR protocols if ir-keytable installed
			if os.path.exists("/usr/bin/ir-keytable"):
				execCommand('sudo ir-keytable -p all')
			
		else:
			# Earlier Jessie and Stretch OS
			log.message("Starting lirc daemon", log.DEBUG)
			execCommand('sudo service lirc start')	# For Jessie

		remote_led = config.getRemoteLed()
		if remote_led > 0:
			print "Flashing LED on GPIO", remote_led
			GPIO.setwarnings(False)      # Disable warnings
			GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
			GPIO.setup(remote_led, GPIO.OUT)  # Output LED
			flash_led(remote_led)
		else:
			log.message("Remote control LED disabled", log.DEBUG)
		udpport = config.getRemoteUdpPort()
		udphost = config.getRemoteUdpHost()
		log.message("UDP connect host " + udphost + " port " + str(udpport), log.DEBUG)
		listener()

	# Status enquiry
	def status(self):
		# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None

		if not pid:
			message = "Remote control status: not running"
			log.message(message, log.INFO)
			print message
		else:
			message = "Remote control running pid " + str(pid)
			log.message(message, log.INFO)
			print message
		return

	# Test udp send
	def send(self,msg):
		udpSend(msg)
		return
		
	# Test the LED
	def flash(self):
		log.init('radio')
		remote_led = config.getRemoteLed()
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
		if use_pylirc:
			sockid = pylirc.init("piradio", lircrc, blocking)
		else:
			# The following line is for Jessie  and Stretch only
			sockid = lirc.init("piradio", lircrc, blocking)

		log.message("Listener on socket " + str(socket) + " established", log.DEBUG)

		# Main Listen loop
		print "Listening for input on IR sensor"
		while True:
			#pdb.set_trace()

			if use_pylirc:
				nextcode =  pylirc.nextcode()
			else:
				nextcode =  lirc.nextcode()

			# For Jessie amend pylirc.nextcode to lirc.nextcode

			if nextcode != None and len(nextcode) > 0:
				if remote_led > 0:
					GPIO.output(remote_led, True)
				button = nextcode[0]
				log.message(button, log.DEBUG)
				print button
				udpSend(button)	# Send to radiod program
				if remote_led > 0:
					GPIO.output(remote_led, False)
			else:
				time.sleep(0.2)

	except Exception as e:
		log.message(str(e), log.ERROR)
		print str(e)
		mesg = "Possible configuration error, check /etc/lirc/lircd.conf"
		log.message(mesg, log.ERROR)
		print mesg
		mesg = "Activation IR Remote Control failed - Exiting"
		log.message(mesg, log.ERROR)
		print mesg
		sys.exit(1)

# The main Remote control listen routine

# Send button data to radio program
def udpSend(button):
	global udpport
	global udphost
	data = ''
	log.message("Remote control daemon udpSend " + button, log.DEBUG)
	
	try:
		clientsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		clientsocket.settimeout(3)
		clientsocket.sendto(button, (udphost, udpport))
		data = clientsocket.recv(100).strip()
		clientsocket.close()

	except socket.error, e:
		err = e.args[0]
		if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
			msg = "IR remote udpSend no data: " + str(e)
			print msg
			log.message(msg, log.ERROR)
		else:
			# Errors such as timeout
			msg = "IR remote udpSend: " + str(e)
			print msg
			log.message(msg , log.ERROR)

	if len(data) > 0:
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
	print "usage: %s start|stop|status|nodaemon|version|flash|send|config" % sys.argv[0]
	sys.exit(2)

### Main routine ###
if __name__ == "__main__":

	if pwd.getpwuid(os.geteuid()).pw_uid > 0:
		print "This program must be run with sudo or root permissions!"
		sys.exit(1)

	daemon = RemoteDaemon('/var/run/remote.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'nodaemon' == sys.argv[1]:
			daemon.nodaemon()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'flash' == sys.argv[1]:
			daemon.flash()
		elif 'status' == sys.argv[1]:
			daemon.status()
		elif 'version' == sys.argv[1]:
			print "Version 0.1"
		elif 'send' == sys.argv[1]:
			daemon.send('IR_REMOTE')
		elif 'config' == sys.argv[1]:
			config = Configuration()
			print "LED = GPIO", config.getRemoteLed()
			print "HOST =", config.getRemoteUdpHost()
			print "PORT =", config.getRemoteUdpPort()
			print "LISTEN =", config.getRemoteListenHost()
		else:
			print "Unknown command: " + sys.argv[1]
			usage()
		sys.exit(0)
	else:
		usage()

# End of script

