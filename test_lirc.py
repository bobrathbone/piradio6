#!/usr/bin/env python3
#
# Raspberry Pi Radio Remote Control Test for lircd
#
# $Id: test_lirc.py,v 1.2 2023/02/28 10:40:37 bob Exp $
#
# Author : AutoDesk Instructables
# Site   : https://www.instructables.com
#
# Publisher: Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#       The authors shall not be liable for any loss or damage however caused.
#

from lirc import RawConnection
def ProcessIRRemote():
       
    #get IR command
    #keypress format = (hexcode, repeat_num, command_key, remote_id)
    try:
        keypress = conn.readline(.0001)
    except:
        keypress=""
              
    if (keypress != "" and keypress != None):
                
        data = keypress.split()
        sequence = data[1]
        command = data[2]
        
        #ignore command repeats
        if (sequence != "00"):
           return
        
        print(command)        
            
#define Global
conn = RawConnection()
print("Waiting for IR events ...")
while True:         
      ProcessIRRemote()
