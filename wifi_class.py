#!/usr/bin/env python3
#
# Raspberry Pi Internet Radio Wifi Class
# $Id: wifi_class.py,v 1.6 2026/01/24 10:35:50 bob Exp $
#
# This program allows selection of a specific Wi-Fi network from 
# a list of available SSIDs. It adds a wpa-suplicant entry to
# /etc/wpa-supplicant/wpa-suplicant.conf
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class sets up the wifi interface
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#
import os,sys
import subprocess
import pdb

from country_codes import CountryCodes

countryCodes = CountryCodes()

wpa_supplicant = '/etc/wpa_supplicant/wpa_supplicant.conf'

# wpa_supplicant.conf file contents
header1 = 'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev'
header2 = 'update_config=1'
header3 = 'country='

class WiFi:

    ssid = ''
    psk = '' 
    countryCode = ''

    def __init__(self):
        return

    # Get list of SSIDs
    def list(self):
        SSIDs = []
        command = ['sudo', 'iwlist', 'wlan0', 'scanning']
        iwList = self.execCommand(command)
        for line in iwList:
            line = str(line.lstrip())
            line = line.rstrip()
            if 'ESSID' in line:
                x,ssid = line.split(':')
                ssid = ssid.strip("'")
                ssid = ssid.strip('\"')
                if len(ssid) > 0 and ssid not in SSIDs:
                    SSIDs.append(ssid)
        return SSIDs

    # Execute a system command
    def execCommand(self,command):
        result = []
        ps = subprocess.Popen(command, stdout=subprocess.PIPE)
        output = ps.communicate()[0]
        for line in output.splitlines():
            result.append(line)
        return result

    # Get country from code
    def getCountry(self,code):
        return countryCodes.getCountry(code)

    # Get country from code
    def setCountryCode(self,code):
        self.countryCode = code.upper()

    # Set the ssid
    def setSSID(self,ssid):
        self.ssid = ssid

    # Set the psk
    def setPSK(self,psk):
        self.psk = psk

    # Create a header
    def createHeader(self,countryCode):
        header = []
        if len(countryCode) < 1:
            countryCode = 'gb'
        self.countryCode = countryCode.upper()
        header.append(header1)
        header.append(header2)
        header.append(header3 + self.countryCode)
        return header

    def createEntry(self,ssid,psk):
        entry = []
        self.ssid = ssid
        self.psk = psk
        
        # Build entry
        entry.append('')
        entry.append('network={')
        entry.append('\tssid="' + self.ssid + '"')
        entry.append('\tpsk="' + self.psk + '"')
        entry.append('}')
        return entry

    # Write the header (removes all entries)
    def writeHeader(self,header):
        f = open(wpa_supplicant, 'w')
        for line in header:
            f.write(line + '\n')    
        f.close()

    # Append a WiFi entry
    def appendEntry(self,entry):
        f = open(wpa_supplicant, 'a')
        for line in entry:
            f.write(line + '\n')    
        f.close()

# End of WiFi class

if __name__ == '__main__':
    import pwd
    from wifi_class import WiFi

    if pwd.getpwuid(os.geteuid()).pw_uid > 0:
        print("This program must be run with sudo or root permissions!")
        sys.exit(1)

    wifi =  WiFi()

    # Get a list of SSIDs
    SSIDs = wifi.list()
    idx = 1
    for ssid in SSIDs:
        print (idx,ssid)
        idx += 1

    # Select SSID
    idx = input("Select SSID number: ")
    try:
        idx = int(idx)
        ssid = SSIDs[idx-1]
        print(ssid, "selected")
    except:
        print("Invalid selection!")
        sys.exit(1)

    passkey = input("Enter password: ")
    if len(passkey) < 1:
        sys.exit(0)

    print("Adding %s to %s" % (ssid,wpa_supplicant))

    header = wifi.createHeader('gb')
    wifi.writeHeader(header)

    entry = wifi.createEntry(ssid,passkey)
    wifi.appendEntry(entry)

    sys.exit(0)

# End of __main__
# :set tabstop=4 shiftwidth=4 expandtab
# :retab
