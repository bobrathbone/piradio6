Pairing a Bluetooth device
==========================

Before attempting to pair your Bluetooth device you must first install the Bluetooth software using:
 **radio-config --> Option 2 Configure audio output devices --> Option 13 Bluetooth Device**

Switch on the Bluetooth speakers or headphones.  Reboot the Raspberry Pi. 
If you are doing this setup from the command line run **rfkill** to make sure that bluetooth isn't blocked. 
```
sudo rfkill bluetooth 
```
To pair your Bluetooth device run **bluetoothctl**. This will enter its own shell.
```
bluetoothctl
Agent registered
[bluetooth]#
```
Do not mistake the # prompt for the root (super-user) prompt. 

Make sure that the Bluetooth interface is powered on 

```
[bluetooth]# power on
[bluetooth]# scan on
[bluetooth]# agent on
Agent registered
[bluetooth]# default-agent
Default agent request successful
```

Switch on scanning.
```
[bluetooth]# scan on
Discovery started
[CHG] Controller DC:A6:32:05:36:9D Discovering: yes
[NEW] Device C0:48:E6:73:3D:FA [TV] Samsung Q7 Series (65)
[NEW] Device 00:75:58:41:B1:25 SP-AD70-B
```

When you see your Bluetooth speaker or headphones switch scan back off.

```
[bluetooth]# scan off
:
[CHG] Controller DC:A6:32:05:36:9D Discovering: no
Discovery stopped
```

In this example the device name is SP-AD70-B and has a Bluetooth ID of 00:75:58:41:B1:25.
Now pair the device using its ID:

```
[bluetooth]# pair 00:75:58:41:B1:25
Attempting to pair with 00:75:58:41:B1:25
[CHG] Device 00:75:58:41:B1:25 Connected: yes
[CHG] Device 00:75:58:41:B1:25 UUIDs: 0000110b-0000-1000-8000-00805f9b34fb
[CHG] Device 00:75:58:41:B1:25 UUIDs: 0000110e-0000-1000-8000-00805f9b34fb
[CHG] Device 00:75:58:41:B1:25 UUIDs: 0000111e-0000-1000-8000-00805f9b34fb
[CHG] Device 00:75:58:41:B1:25 ServicesResolved: yes
[CHG] Device 00:75:58:41:B1:25 Paired: yes
Pairing successful
[CHG] Device 00:75:58:41:B1:25 ServicesResolved: no
[CHG] Device 00:75:58:41:B1:25 Connected: no
```

Now connect and trust the device:

```
[bluetooth]# connect 00:75:58:41:B1:25
Attempting to connect to 00:75:58:41:B1:25
[CHG] Device 00:75:58:41:B1:25 Connected: yes
Connection successful
[CHG] Device 00:75:58:41:B1:25 ServicesResolved: yes
```
Note that from now on you now will see the name of the connected device ([SP-AD70-B]) in the bluetoothctl prompt. 
Now trust the new Bluetooth device

```
[SP-AD70-B]#trust 00:75:58:41:B1:25
[CHG] Device 00:75:58:41:B1:25 Trusted: yes
Changing 00:75:58:41:B1:25 trust succeeded
```

Check the newly paired device

```
[SP-AD70-B]# info 00:75:58:41:B1:25
Device 00:75:58:41:B1:25 (public)
        Name: SP-AD70-B
        Alias: SP-AD70-B
        Class: 0x00240404
        Icon: audio-headset
        Paired: yes
        Bonded: yes
        Trusted: yes
        Blocked: no
        Connected: yes
        LegacyPairing: no
        UUID: Audio Sink                (0000110b-0000-1000-8000-00805f9b34fb)
        UUID: A/V Remote Control        (0000110e-0000-1000-8000-00805f9b34fb)
        UUID: Handsfree                 (0000111e-0000-1000-8000-00805f9b34fb)

[SP-AD70-B]# exit
```

Display Bluetooth devices with bluealsa-aplay

```
bluealsa-aplay -l
**** List of PLAYBACK Bluetooth Devices ****
hci0: 00:75:58:41:B1:25 [SP-AD70-B], trusted audio-headset
  A2DP (SBC): S16_LE 2 channels 48000 Hz
**** List of CAPTURE Bluetooth Devices ***
```
Note: Your display will vary depending upon the Bluetooth device just paired

Testing the Bluetooth device
============================
Stop the radio software (Important).
```
sudo systemctl stop radiod
```
Now run the following:
```
aplay -D bluealsa:SRV=org.bluealsa,DEV=00:75:58:41:B1:25,PROFILE=a2dp /usr/share/sounds/alsa/Front_Center.wav
```

**Note:** The above is all one line. Substitute the above Bluetooth address with your own address. 
If things are working correctly, a spoken “Front Center” should be heard from the Bluetooth device.
 
End of tutorial
