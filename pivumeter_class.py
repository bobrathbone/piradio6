#!/usr/bin/env python3
# Raspberry Pi VuMeter (Pimoroni PHat beat) Class
# $Id: pivumeter_class.py,v 1.6 2023/01/24 12:23:27 bob Exp $
#
# Display volume setting on the Pimoroni PiVumeter (PHat beat)
#
# Author: Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
#
import phatbeat
import sys,time
import threading
import pdb

try:
    import alsaaudio
except Exception as e:
    print(e)
    print("Run: sudo apt install python3-alsaaudio")
    sys.exit(1)
    
# phatbeat.set_pixel(pixel, r, g, b, brightness=None, channel=None)


class PiVumeter:
    _bright = 128 	# 1 to 255
    _r=_bright
    _g=0
    _b=0
    _pixel=0
    _vol = -1

    def __init__(self):
        pass

    def getVolume(self):
        vol = alsaaudio.Mixer('PCM')
        volume = vol.getvolume() # Get the current Volume
        return volume


    # Display volume if it changed
    def display(self,volume): 
        r = 0
        g = self._bright
        b = 0
        if volume != self._vol:
            phatbeat.clear()
            leftVol = volume[0]
            rightVol = volume[1]
            leftRange = 7-int(leftVol/float(12.5))
            rightRange = 7-int(rightVol/float(12.5))

            for pixel in range(leftRange,8):
                if pixel < 0:
                    pixel = 0
                
                if leftVol <= 0:
                    r = self._bright
                    g = 0
                    b = 0
                elif pixel < 2:
                    r = self._bright
                    g = 0
                    b = 0
                elif pixel == 7:
                    r = 0
                    g = 0
                    b = self._bright
                else:
                    r = 0
                    g = self._bright
                    b = 0
                phatbeat.set_pixel(pixel, r, g, b, channel=0)

            for pixel in range(rightRange,8):
                if pixel < 0:
                    pixel = 0

                if leftVol <= 0:
                    r = self._bright
                    g = 0
                    b = 0
                elif pixel < 2:
                    r = self._bright
                    g = 0
                    b = 0
                elif pixel == 7:
                    r = 0
                    g = 0
                    b = self._bright
                else:
                    r = 0
                    g = self._bright
                    b = 0
                phatbeat.set_pixel(pixel, r, g, b, channel=1)
            phatbeat.show()
        self._vol = volume
        return self._vol

    # Test all pixels on L & R channels
    def test(self): 
        while True:
            volume = self._getVolume()
            leftVol = volume[0]
            rightVol = volume[1]

            for channel in (1,0):
                phatbeat.set_pixel(self._pixel, self._r, self._g, self._b, channel=channel)
            phatbeat.show()
            if self._r > 0: 
                self._r=0 
                self._g=self._bright
            elif self._g > 0: 
                self._g=0 
                self._b=self._bright
            elif self._b > 0: 
                self._b=0 
                self._r=self._bright
            self._pixel += 1
            if self._pixel > 7:
               self._pixel = 0

def usage():
    print ("Usage:",sys.argv[0],"[--test]")

# Main routine
if __name__ == "__main__":

    pivumeter = PiVumeter()

    if len(sys.argv) > 1:
        for i in range(1,len(sys.argv)):
            param = sys.argv[i]
            if param == '--test':
                pivumeter.test()
            else:
                usage()
                exit(1)
    else:
        while True:
            vol = pivumeter.getVolume()
            pivumeter.display(vol)
            time.sleep(0.01)

# set tabstop=4 shiftwidth=4 expandtab
# retab
