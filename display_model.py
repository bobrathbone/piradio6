#!/usr/bin/env python3
"""
$Id: display_model.py,v 1.13 2024/05/28 11:29:11 bob Exp $

Author: Chris Hager <chris@linuxuser.at>
License: MIT
URL: https://github.com/metachris/raspberrypi-utils

Modified by: Bob Rathbone  (bob@bobrathbone.com)
Site: http://www.bobrathbone.com

License: GNU V3, See https://www.gnu.org/copyleft/gpl.html

Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
            The authors shall not be liable for any loss or damage however caused.

This script detects a Raspberry Pi's model, manufacturer and mb ram, based
on the cpu revision number. Data source:
https://www.raspberrypi.org/documentation/computers/raspberry-pi.html#raspberry-pi-revision-codes

You can instantiate the ModelInfo class either with a parameter `rev_hex`
(eg. `m = ModelInfo("000f")`), or without a parameter
(eg. `m = ModelInfo()`) in which case it will try to detect it via
`/proc/cpuinfo`. Accessible attributes:


    class ModelInfo:
        model = ''     # 'A' or 'B'
        revision = ''  # '1.0' or '2.0'
        ram_mb = 0     # integer value representing ram in mb
        maker = ''     # manufacturer (eg. 'Qisda')
        info = ''      # additional info (eg. 'D14' removed)

"""
import re
import os


# From http://elinux.org/RPi_HardwareHistory
model_data = {
    '2': ('B', '1.0', 256, 'Cambridge', ''),
    '3': ('B', '1.0', 256, 'Cambridge', 'Fuses mod and D14 removed'),
    '4': ('B', '2.0', 256, 'Sony UK', ''),
    '5': ('B', '2.0', 256, 'Qisda', ''),
    '6': ('B', '2.0', 256, 'Egoman', ''),
    '7': ('A', '2.0', 256, 'Egoman', ''),
    '8': ('A', '2.0', 256, 'Sony UK', ''),
    '9': ('A', '2.0', 256, 'Qisda', ''),
    'd': ('B', '2.0', 512, 'Egoman', ''),
    'e': ('B', '2.0', 512, 'Sony UK', ''),
    'f': ('B', '2.0', 512, 'Qisda', ''),
    '10': ('B+', '1.0', 512, 'Sony UK', ''),
    '11': ('Compute Module 1', '1.0', 512, 'Sony UK', ''),
    '12': ('A+', '1.1', 256, 'Sony UK', ''),
    '13': ('B+', '1.2', 512, 'Unknown', ''),
    '14': ('Compute Module 1', '1.0', 512, 'Embest', ''),
    '15': ('A+', '1.1', 512, 'Embest', '256MB or 512MB'),
    'a01040': ('2B', '1.0', 1024, 'Sony UK', ''),
    'a01041': ('2B', '1.1', 1024, 'Embest', ''),
    'a21041': ('2B', '1.1', 1024, 'Embest', ''),
    'a22042': ('2B', '1.2', 1024, 'Embest', 'with BCM2837'),
    'a02082': ('3B', '2.0', 1024, 'Sony UK', 'Quad Core 1.2MHz, Onboard WiFi and Bluetooth 4.1'),
    'a22082': ('3B', '2.0', 1024, 'Embest', 'Quad Core 1.2MHz, Onboard WiFi and Bluetooth 4.1'),
    'a22083': ('3B', '1.3', 1024, 'Embest', 'Quad Core 1.2MHz, Onboard WiFi and Bluetooth 4.1'),
    'a02082': ('3B', '1.2', 1024, 'Sony UK', 'Quad Core 1.2MHz, Onboard WiFi and Bluetooth 4.1'),
    'a020a0': ('Compute Module 3', '1.0', 1024, 'Sony UK', 'and CM3 Lite'),
    'a22082': ('3B', '1.2', 1024, 'Embest', 'Quad Core 1.2MHz, Onboard WiFi and Bluetooth 4.1'),
    'a32082': ('3B', '1.2', 1024, 'Sony UK (Japan)', 'Quad Core 1.2MHz, Onboard WiFi and Bluetooth 4.1'),
    'a220a0': ('CM3', '1.0', 1024, 'Embest', 'Quad Core 1.2MHz, Compute module DDR2 SODIMM connector '),
    'a22100': ('CM3+', '1.0', 1024, 'Sony', 'Quad Core 1.2MHz, Compute module DDR2 SODIMM connector '),
    '900061': ('CM', '1.1', 512, 'Embest', 'Compute module DDR2 SODIMM connector'),
    '900091': ('A+', '1.1', 512, 'Sony UK', ''),
    '902120': ('Zero 2 W', '1.0', 512, 'Sony UK', '1GHz 64-bit quad core, Onboard WiFi and Bluetooth 4.1'),
    '9020e0': ('3A+', '1.0', 512, 'Sony UK', ''),
    '900032': ('B+', '1.2', 512, 'Sony UK', ''),
    '900092': ('Zero', '1.2', 512, 'Sony UK', ''),
    '920092': ('Zero', '1.0', 512, 'Embest', ''),
    '920093': ('Zero', '1.3', 512, 'Embest', ''),
    '9000c1': ('Zero W', '1.1', 1024, 'Sony UK', 'Onboard WiFi and Bluetooth 4.1'),
    '9000d3': ('3B+', '1.1', 1024, 'Sony UK', 'Onboard WiFi and Bluetooth 4.1'),
    '9000e0': ('3A+', '1.0', 512, 'Sony UK', 'Onboard WiFi and Bluetooth 4.1'),
    'a02082': ('3 Model B', '1.2', 1024, 'Sony UK', 'Onboard WiFi and Bluetooth 4.1'),
    'a020a0': ('Compute Module 3 (and CM3 Lite)', '1.0', 1024, 'Sony UK', 'Onboard WiFi and Bluetooth 4.1'),
    'a22082': ('3B', '1.2', '1GB', 'Embest', 'Onboard WiFi and Bluetooth 4.1'),
    'a32082': ('3B', '1.2', '1GB', 'Sony UK', 'Onboard WiFi and Bluetooth 4.1'),
    'a52082': ('3B', '1.2', '1GB', 'Stadium', 'Onboard WiFi and Bluetooth 4.1'),
    'a020d3': ('3B+', '1.3', '1GB', 'Sony UK', '1.4GHz quad core, Bluetooth 4.2, POE support'),
    'a03111': ('4B', '1.1', '1GB', 'Sony UK', '1.5GHz quad core, Bluetooth 5, USB 2/3'),
    'b03111': ('4B', '1.1', '2GB', 'Sony UK', '1.5GHz quad core, Bluetooth 5, USB 2/3'),
    'b03111': ('4B', '1.2', '2GB', 'Sony UK', '1.5GHz quad core, Bluetooth 5, USB 2/3'),
    'b03114': ('4B', '1.4', '2GB', 'Sony UK', '1.5GHz quad core, Bluetooth 5, USB 2/3'),
    'b03115': ('4B', '1.5', '2GB', 'Sony UK', '1.5GHz quad core, Bluetooth 5, USB 2/3'),
    'c03111': ('4B', '1.1', '4GB', 'Sony UK', '1.5GHz quad core, Bluetooth 5, USB 2/3'),
    'c03112': ('4B', '1.2', '4GB', 'Sony UK', '1.5GHz quad core, Bluetooth 5, USB 2/3'),
    'c03114': ('4B', '1.4','8GB', 'Sony UK', '1.5GHz quad core, Bluetooth 5, USB 2/3'),
    'c03115': ('4B', '1.4','4GB', 'Sony UK', '1.5GHz quad core, Bluetooth 5, USB 2/3'),
    'c03130': ('400', '1.0','4GB', 'Sony UK', '64-bit 1.8GHz quad core, Bluetooth 5, USB 2/3'),
    'c04170': ('5', '1.0','4GB', 'Sony UK', '64-bit 2.4GHz quad core + VideoCore VII GPU, Bluetooth 5, USB 2/3'),
    'd04170': ('5', '1.0','8GB', 'Sony UK', '64-bit 2.4GHz quad core + VideoCore VII GPU, Bluetooth 5, USB 2/3'),
    'd03115': ('4B', '1.5','8GB', 'Sony UK', '1.5GHz quad core, Bluetooth 5.0, USB 2/3'),
    '902120': ('Zero 2W', '1.0','512MB', 'Sony UK', '64 bit 1.0GHz quad core, Bluetooth 4.2, USB 2.0'),
}


class ModelInfo(object):
    """
    You can instantiate ModelInfo either with a parameter `rev_hex`
    (eg. `m = ModelInfo("000f")`), or without a parameter
    (eg. `m = ModelInfo()`) in which case it will try to detect it via
    `/proc/cpuinfo`
    """
    model = ''
    revision = ''
    ram_mb = 0
    maker = ''
    info = ''

    # Model description from device tree
    dt_model = '/sys/firmware/devicetree/base/model'

    def __init__(self, rev_hex=None):
        if not rev_hex:
            with open("/proc/cpuinfo") as f:
                cpuinfo = f.read()
            rev_hex = re.search(r"(?<=\nRevision)[ |:|\t]*(\w+)", cpuinfo) \
                    .group(1)

        self.revision_hex = rev_hex[-4:] if rev_hex[:4] == "1000" else rev_hex
        try:
            self.model, self.revision, self.ram_mb, self.maker, self.info = \
                        model_data[rev_hex.lstrip("0")]
        except:
    
            if os.path.exists(self.dt_model):
                with open(self.dt_model) as f:
                    print(f.read())
            else:
                print ("Unknown model", rev_hex.lstrip("0"))

    def __repr__(self):
        s = "%s: Model %s, Revision %s, RAM: %s MB, Maker: %s%s" % ( \
            self.revision_hex, self.model, self.revision, self.ram_mb, \
            self.maker, ", %s" % self.info if self.info else "")
        return s

if __name__ == "__main__":
    m = ModelInfo()
    print(m)

# set tabstop=4 shiftwidth=4 expandtab
# retab
