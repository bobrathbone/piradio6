#!/usr/bin/env python3
import spidev
import sys
import time

class VFD:
    def __init__(self, spi_num, spi_ce):
        self.spi = spidev.SpiDev()
        self.spi.open(spi_num, spi_ce)
        self.setDisplay(True, False, False)
        self.setDirection(True, False)

    def write(self, data, rs):
        if rs:
            self.spi.writebytes([0xFA, data])
        else:
            self.spi.writebytes([0xF8, data])
        time.sleep(0.00001)

    def writeCmd(self, c):
        self.write(c, False)

    def writeStr(self, s):
        for c in s:
            self.write(ord(c), True)

    def cls(self):
        self.writeCmd(0x01)
        time.sleep(0.005)

    def setPosition(self, x, y):
        self.writeCmd(0x80 | (0x40*y + x))
        time.sleep(0.005)

    def setDirection(self, leftToRight, autoScroll):
        cmd = 4
        if leftToRight:
            cmd = cmd | 2
        if autoScroll:
            cmd = cmd | 1

        self.writeCmd(cmd)

    def setDisplay(self, display, cursor, blink):
        cmd = 8
        if display:
            cmd = cmd | 4
        if cursor:
            cmd = cmd | 2
        if blink:
            cmd = cmd | 1

        self.writeCmd(cmd)

def usage():
   print ("vfd.py  [args...]")
   print ("     write \"<text>\"")
   print ("     goto  ")
   print ("     cls")
   sys.exit(1)

def main():
   vfd = VFD(0,0)

   if len(sys.argv)<2:
       usage()

   cmd=sys.argv[1]
   if (cmd=="write"):
       if len(sys.argv)!=3:
           usage()
       vfd.writeStr(sys.argv[2])
   elif (cmd=="goto"):
       if len(sys.argv)!=4:
           usage()
       vfd.setPosition(int(sys.argv[2]), int(sys.argv[3]))
   elif (cmd=="cls"):
       vfd.cls()
   else:
       usage()

if __name__ == "__main__":
    main()

