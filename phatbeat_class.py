#!/usr/bin/env python
# Raspberry Pi pHAT Beat Class
# $Id: phatbeat_class.py,v 1.3 2018/12/04 07:59:51 bob Exp $
#
# Author: Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class usees the Pimoroni pHAT-BEAT libraries 
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
#

from __init__ import *
import sys,os
import time,pwd
import pdb

import phatbeat

class Phat:

        def __init__(self,callback,log):
                self.callback = callback
                self.log = log
		self.log.message("pHat beat initialised ", log.DEBUG)

# End of class

def interrupt(gpio):
        print "Button pressed on GPIO", gpio
        return

### Test routine ###
if __name__ == "__main__":
	from config_class import Configuration
	from log_class import Log
	config = Configuration()
        log = Log()
	log.init('radio')
	phat = Phat(interrupt,log)

	# pHAT callbacks
	@phatbeat.on(phatbeat.BTN_FASTFWD)
	def fast_forward(pin):
		log.message("pHat button " + str(phatbeat.BTN_FASTFWD), log.DEBUG)
		print "DEBUG pHat button " + str(phatbeat.BTN_FASTFWD)
		phat.callback(phatbeat.BTN_FASTFWD)

	@phatbeat.on(phatbeat.BTN_REWIND)
	def fast_forward(pin):
		phat.callback(phatbeat.BTN_REWIND)

	@phatbeat.on(phatbeat.BTN_PLAYPAUSE)
	def fast_forward(pin):
		phat.callback(phatbeat.BTN_PLAYPAUSE)

	@phatbeat.on(phatbeat.BTN_VOLUP)
	def fast_forward(pin):
		phat.callback(phatbeat.BTN_VOLUP)

	@phatbeat.on(phatbeat.BTN_VOLDN)
	def fast_forward(pin):
		phat.callback(phatbeat.BTN_VOLDN)

	@phatbeat.on(phatbeat.BTN_ONOFF)
	def fast_forward(pin):
		phat.callback(phatbeat.BTN_ONOFF)

        if pwd.getpwuid(os.geteuid()).pw_uid > 0:
                print "This program must be run with sudo or root permissions!"
                sys.exit(1)

	print "Test pHAT Beat interface board"
try:
	while True:
		#pdb.set_trace()
		#phatbeat.set_all(0,128,0,0.1,channel=0)
		#phatbeat.set_all(255,155,0,0.1,channel=1)
		#phatbeat.show()
		time.sleep(1)

except KeyboardInterrupt:
	sys.exit()
