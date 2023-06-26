#!/usr/bin/env python3
# -*- coding: latin-1 -*-
#
# $Id: ssid_class.py,v 1.11 2023/06/20 07:40:36 bob Exp $
# Raspberry Pi SSID class
# Allows listing/selection of Wi-Fi access point by SSID
# Requires wifi package
# sudo pip3 install wifi
# Documentation: https://wifi.readthedocs.io/en/latest/scanning.html
# It writes Wi-Fi configurations to /etc/network/interfaces
# Also see: /usr/local/bin/wifi (Python3)
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#
#!/usr/bin/env python3

import sys,os
import pwd
import pdb

from wifi import Cell, Scheme
from wifi.utils import print_table, match as fuzzy_match
from wifi.exceptions import ConnectionError, InterfaceError
from subprocess import check_output

class Wireless:

    def __init__(self):
        return

    # Get list of all SSIDs
    def getSSIDS(self):
        ssids = []
        cells = Cell.all('wlan0')
        for cell in cells:
            ssid = cell.ssid
            if ssid not in ssids:
                ssids.append(ssid)
        return ssids

    # Get cell by SSID
    def getCell(self,ssid,passkey):
        #pdb.set_trace()
        cell = Cell.from_string(ssid)
        scheme = Scheme.for_cell('wlan0', ssid, cell, passkey)
        try: 
            scheme.save()
        except:
            pass    # Ignore if already present
        
        return cell

    def connect(self,ssid):
        try:
            scheme = Scheme.find('wlan0', ssid)
            scheme.activate()
            return True
        except Exception as e:
            print(str(e))
            return False

# End of Wireless class

# Class test routine
# Print usage
def usage():
    print(("Usage: sudo %s" % sys.argv[0]))
    sys.exit(2)

# Wireless class
if __name__ == "__main__":

    if pwd.getpwuid(os.geteuid()).pw_uid > 0:
        print("This program must be run with sudo or root permissions!")
        usage()
        sys.exit(1)

    # Get the list of available SSIDs
    w = Wireless()
    ssids = w.getSSIDS()
    idx = 1
    for ssid in ssids:
        print(idx,ssid)
        idx += 1
    
    # Select SSID
    idx = input("Select SSID number: ") 
    try:
        idx = int(idx)
        ssid = ssids[idx-1]
        print(ssid, "selected")
    except:
        print("Invalid selection!")
        sys.exit(1)

    passkey = input("Enter password: ") 

    cell = w.getCell(ssid,passkey)
    print("Frequency", cell.frequency)

    print("Connecting", ssid)

    if w.connect(ssid):
        print(ssid,"Connected")
    else:
        print(ssid,"Connection failed")
        sys.exit(1)

# End of test routine
    
# :set tabstop=4 shiftwidth=4 expandtab
# :retab
