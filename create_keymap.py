#!/usr/bin/env python3
# $Id: create_keymap.py,v 1.7 2024/12/01 11:07:30 bob Exp $
"""
Script to capture remote control key presses and generate a TOML file.
Modified by: Bob Rathbone  (bob@bobrathbone.com)
Site: http://www.bobrathbone.com

Original script Name: ir-keytable-record.py
Author: Vince Ricosti
Url: https://raw.githubusercontent.com/vricosti/infrared-resources/main/ir-keytable-record.py

License: GNU V3, See https://www.gnu.org/copyleft/gpl.html

Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
            The authors shall not be liable for any loss or damage however caused.

Usage: Run the script with -h or --help to see usage options.
"""
import os
import sys
import subprocess
import re
import time
import signal
import argparse

# Array of required key names for the radio
keys = ()

# Basic keys are for the RPi mini remote control or devices with few keys
basic_keys=('KEY_VOLUMEUP','KEY_VOLUMEDOWN','KEY_MUTE','KEY_CHANNELUP','KEY_CHANNELDOWN',
      'KEY_MENU','KEY_NUMERIC_0','KEY_NUMERIC_1','KEY_NUMERIC_2',
      'KEY_NUMERIC_3','KEY_NUMERIC_4', 'KEY_NUMERIC_5','KEY_NUMERIC_6',
      'KEY_NUMERIC_7','KEY_NUMERIC_8','KEY_NUMERIC_9','KEY_EXIT','KEY_RECORD'
     )

# Extra keys ar for remote controls with more keys
extra_keys = ('KEY_LEFT','KEY_RIGHT','KEY_UP','KEY_DOWN','KEY_OK')

remotes_dir = '/usr/share/radio/remotes/'
sys_rc = '/sys/class/rc'

def get_ir_keytable_output(sysdev):
    cmd = ["stdbuf", "-oL", "ir-keytable", "-s", sysdev, "-t"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)

    lines = []
    for line in iter(process.stdout.readline, ''):
        lines.append(line)
        if "lirc protocol" in line:
            break

    process.send_signal(signal.SIGINT)
    process.communicate()

    return ''.join(lines)

def extract_protocol_and_scancode(output):
    # Extract lines containing "lirc protocol"
    match = re.search(r"lirc protocol\(([^)]+)\): scancode = (0x[\da-fA-F]+)", output)
    if match:
        protocol, scancode = match.groups()
        if protocol == 'necx':
            protocol = 'nec'
        return protocol, scancode
    return None, None

def parse_arguments():
    ir_device = get_ir_device('gpio_ir_recv')

    parser = argparse.ArgumentParser(description='Script to capture remote control key presses and generate a TOML file.')
    parser.add_argument('-s', '--sysdev', default=ir_device, help='Defaults to rc0 if not specified.')

    return parser.parse_args()

# Returns the device name for the "gpio_ir_recv" overlay (rc0...rc6)
# Used to load ir_keytable
def get_ir_device(sName):
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

## Main routine ##
def main():
    args = parse_arguments()
    sysdev = args.sysdev

    # Get the name of the new remote control toml file (noextension)
    filename = input("Enter the name for your remote control: ").strip()
    filename_no_ext, ext = os.path.splitext(filename)
    if not ext:
        filename = f"{filename}.toml"
    filename = remotes_dir + filename

    print("\nThe Raspberry Pi mini remote control has less keys than most")
    print("other remote controls - Select 'y' if using the RPi mini otherwise 'n' ")
    yesno = input("Are you using the Raspberry Pi mini remote control y/n: ").strip()
    if yesno != 'y': 
        keys = basic_keys + extra_keys
    else:
        keys = basic_keys
    
    keys_dict = {}
    global_protocol = None

    # Create the array of key names and scan codes
    last_scan_code = ''
    print("Start recording")
    for key_name in keys:
        print("\nPlease press the button on your remote control for key:", key_name)
        output = get_ir_keytable_output(sysdev)
        protocol, scancode = extract_protocol_and_scancode(output)
        if protocol and scancode:
            print(f'{scancode} = "{key_name}" #protocol ="{protocol}"')
            keys_dict[key_name] = scancode
            if not global_protocol:
                global_protocol = protocol
                if global_protocol == 'rc5x_20':
                    global_protocol = 'rc5'
            time.sleep(1.5)
        last_scan_code = scancode
                    

    with open(filename, 'w') as f:
        f.write("[[protocols]]\n")
        f.write(f'name = "{filename_no_ext}"\n')
        f.write(f'protocol = "{global_protocol}"\n')
        f.write(f'variant = "{global_protocol}"\n')
        f.write("[protocols.scancodes]\n")
        for key_name, scancode in keys_dict.items():
            f.write(f'{scancode} = "{key_name}"\n')

    print(f"\nRemote control definition file '{filename}' has been written.")

if __name__ == "__main__":
    main()
