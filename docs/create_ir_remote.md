
If you are using the Raspberry Pi Mini IR Remote Control you can skip this tutorial. Run the following command: There are two methods:


1) Use the radio-config utility and select **Create an IR remote control definition**
2) Create an IR remote control definition (.toml) file manually

Method 1: Create an IR remote control definition using radio-config
===================================================================
1) Run **radio-config** from the command line
2) Select **8 Install/configure drivers and software components** 
3) Select **Install IR remote control** from the Install Software menu
4) select **Create an IR remote control definition** from the Remote Control menu

You will be asked to enter name for your remote control such as 'myremote'. You can choose any name you wish.

Enter the name for your remote control: **myremote**

Please press the button on your remote control for key: KEY_OK

Press the OK key on your remote control. 
0x833341 = "KEY_OK" #protocol ="nec"
Repeat for every key identififier requested

The key identifiers  are:
'KEY_OK','KEY_VOLUMEUP','KEY_VOLUMEDOWN','KEY_CHANNELUP','KEY_CHANNELDOWN',
'KEY_MENU','KEY_NUMERIC_0','KEY_NUMERIC_1','KEY_NUMERIC_2',
'KEY_NUMERIC_3','KEY_NUMERIC_4', 'KEY_NUMERIC_5','KEY_NUMERIC_6',
'KEY_NUMERIC_7','KEY_NUMERIC_8','KEY_NUMERIC_9', 'KEY_UP','KEY_DOWN',
'KEY_LEFT','KEY_RIGHT','KEY_EXIT'

When finished the following will be displayed:

File '/usr/share/radio/remotes/myremote.toml' has been written.

Press enter to continue:

Back in the IR remote control menu select:

**Select IR remote control definition (keytable)*

```
"1" "eeremote.toml"
"2" "mini.toml"                               │
"3" "myremote.toml"
```

The program will the copy myremote.toml to the /etc/rc_keymaps directory

Reboot the Raspberry Pi

Method 2: Manual creation of an IR remote control definition
============================================================

Run the following command:

```
$ ir-keytable
```

This will list the available input devices of which there can be several.  These devices can change depending what drivers and in what order they are specified. There should be one with  Driver: gpio_ir_recv specified although the /sys/class/rc/rc0/ name might have a different number such as rc2.

```
Found /sys/class/rc/rc0/ with:
        Name: gpio_ir_recv
        Driver: gpio_ir_recv
        Default keymap: rc-rc6-mce
        Input device: /dev/input/event0
        LIRC device: /dev/lirc0
        Attached BPF protocols: Operation not permitted
        Supported kernel protocols: lirc rc-5 rc-5-sz jvc sony nec sanyo mce_kbd rc-6 sharp xmp imon
        Enabled kernel protocols: lirc nec
        bus: 25, vendor/product: 0001:0001, version: 0x0100
        Repeat delay = 500 ms, repeat period = 125 ms
```

The ireventd.py program locates the correct device for the gpio_ir_recv device driver when it is loaded. If you don't see one with **Driver: gpio_ir_recv** defined check that there is an entry similar in the /boot/firmware/config.txt (Bookworm) or /boot/config.txt (Bullseye) file to the example entry below. If not re-run **radio-config** and reinstall the IR remote control software.

```
dtoverlay=gpio-ir,gpio_pin=25
```

Now run:
```
$ sudo ir-keytable -v -t -p  rc-5,rc-5-sz,jvc,sony,nec,sanyo,mce_kbd,rc-6,sharp,xmp
```

**Note:** The above is all one line. This will display the protocols available.
```
Found device /sys/class/rc/rc0/
:
Opening /dev/input/event0
Input Protocol version: 0x00010001
Protocols changed to rc-5 rc-5-sz jvc sony nec sanyo mce_kbd rc-6 sharp xmp
```

Now press a button on the remote control such as Volume Up. This will display the scancode for that button. In this case it is the code for KEY_VOLUMEUP. 

```
228.396048: lirc protocol(necx): scancode = 0x833356
228.396069: event type EV_MSC(0x04): scancode = 0x833356
228.396069: event type EV_SYN(0x00).
228.456056: lirc protocol(necx): scancode = 0x833356 repeat
228.456073: event type EV_MSC(0x04): scancode = 0x833356
228.456073: event type EV_SYN(0x00).
228.564074: lirc protocol(necx): scancode = 0x833356 repeat
228.564098: event type EV_MSC(0x04): scancode = 0x833356
228.564098: event type EV_SYN(0x00).
```

Example remote control definition - myremote.toml 
=================================================

Now create file called myremote.toml as shown in the example below. The scancode in the above example is for KEY_VOLUMEUP.The name can be anything you wish, but it must end in the toml extension. 
Note that you can use another name but it must end in **.toml**. Whatever name that you use it must amend the **keytable** parameter in **/etc/radiod.conf** configuration file (See later)

```
[[protocols]]
name = "myremote"
protocol = "nec"
variant = "nec"
[protocols.scancodes]
0x833356 = "KEY_VOLUMEUP"
0x833357 = "KEY_VOLUMEDOWN"
0x833395 = "KEY_MUTE"
0x833358 = "KEY_CHANNELUP"
0x833359 = "KEY_CHANNELDOWN"
0x833396 = "KEY_MENU"
0x833342 = "KEY_UP"
0x833343 = "KEY_DOWN"
0x833344 = "KEY_LEFT"
0x833345 = "KEY_RIGHT"
0x833341 = "KEY_OK"
0x833360 = "KEY_NUMERIC_0"
0x833361 = "KEY_NUMERIC_1"
0x833362 = "KEY_NUMERIC_2"
0x833363 = "KEY_NUMERIC_3"
0x833364 = "KEY_NUMERIC_4"
0x833365 = "KEY_NUMERIC_5"
0x833366 = "KEY_NUMERIC_6"
0x833367 = "KEY_NUMERIC_7"
0x833368 = "KEY_NUMERIC_8"
0x833369 = "KEY_NUMERIC_9"
0x833373 = "KEY_EXIT"
```

The name field be any name that you like for example **myremote*. The protocol should be that shown above (necx in this example). Assign the scan code for each key as show in the above event.  The variant field is normally the same as the protocol field but this will be indicated in the event output if it is different. There is an example myremote.toml file in the /usr/share/radio/remotes directory.

**Note:** There wasn’t a necx protocol. The nearest one was nec so this was used.

**Note:** The remote-control power on/off button must be called KEY_EXIT and not KEY_POWER. If KEY_POWER is us used the event system issues its own system shutdown command instead of letting the radio decide the exit action, either system shutdown or stop radio. See the exit_action parameter in /etc/radiod.conf file.

Now write the new remote-control definition (myremote.toml) to the key table:

```
$ sudo ir-keytable -c -w myremote.toml
Read myremote table
Old keytable cleared
Wrote 11 keycode(s) to driver
Protocols changed to rc-5
```

Display the new table
=====================

Run the ir-keytable command with the -r flag 
```
$ sudo ir-keytable -r
scancode 0x833341 = KEY_OK (0x160)
scancode 0x833342 = KEY_UP (0x67)
scancode 0x833343 = KEY_DOWN (0x6c)
scancode 0x833344 = KEY_LEFT (0x69)
scancode 0x833345 = KEY_RIGHT (0x6a)
scancode 0x833356 = KEY_VOLUMEUP (0x73)
scancode 0x833357 = KEY_VOLUMEDOWN (0x72)
scancode 0x833358 = KEY_CHANNELUP (0x192)
scancode 0x833359 = KEY_CHANNELDOWN (0x193)
scancode 0x833360 = KEY_NUMERIC_0 (0x200)
scancode 0x833361 = KEY_NUMERIC_1 (0x201)
scancode 0x833362 = KEY_NUMERIC_2 (0x202)
scancode 0x833363 = KEY_NUMERIC_3 (0x203)
scancode 0x833364 = KEY_NUMERIC_4 (0x204)
scancode 0x833365 = KEY_NUMERIC_5 (0x205)
scancode 0x833366 = KEY_NUMERIC_6 (0x206)
scancode 0x833367 = KEY_NUMERIC_7 (0x207)
scancode 0x833368 = KEY_NUMERIC_8 (0x208)
scancode 0x833369 = KEY_NUMERIC_9 (0x209)
scancode 0x833373 = KEY_EXIT (0x74)
scancode 0x833395 = KEY_MUTE (0x71)
scancode 0x833396 = KEY_MENU (0x8b)
Enabled kernel protocols: lirc nec
```

Testing the new IR remote control definition
============================================
Now test it:

```
$ ir-keytable -t
7427.808043: lirc protocol(necx): scancode = 0x833356
7427.808079: event type EV_MSC(0x04): scancode = 0x833356
7427.808079: event type EV_KEY(0x01) key_down: KEY_VOLUMEUP(0x0073)
7427.808079: event type EV_SYN(0x00).
7427.864040: lirc protocol(necx): scancode = 0x833356 repeat
7427.864075: event type EV_MSC(0x04): scancode = 0x833356
7427.864075: event type EV_SYN(0x00).
```

**Note:** If you press a key that you did not previously configure, it will display the scan code but it will not have a key name such as KEY_VOLUMEUP.

If all is OK it is now necessary to make the changes permanent when the RPi is rebooted.
Copy the newly created myremote.toml to /etc/rc_keymaps/

```
$ sudo cp myremote.toml /etc/rc_keymaps/myremote.toml
```

Radio program keytable parameter
================================
The radio program uses the keytable parameter in /etc/radiod.conf file to decide which IR remote control definition to load. 

```
# ireventd daemon keytable name
keytable=myremote.toml
```
You can use a different name (You might have more the one definition) if you wish. For example:

```
keytable=mini.toml
```

Using the above definition the **ireventd.py** program will load the mini.toml definition when it is executed.

End of tutorial
===============

