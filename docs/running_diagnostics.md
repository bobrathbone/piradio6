Running diagnostics
===================
 
1) Run **radio-config**
2) Select option **5 Diagnostics and Information**

The following menu will be displayed

```
                Select diagnostic
    1 Run the radio in diagnostic mode (nodaemon)
    2 Test rotary encoders
    3 Test push buttons
    4 Test events layer
    5 Test configured display
    6 Test GPIOs
    7 Display Radio and OS configuration
                                                      
       <Ok>                 <Cancel>       
```
## Option 1 - Running the radio in diagnostic mode
This option stops the Radio service and starts the radio in foreground mode. It  uses the command:
```
sudo /usr/share/radio/radiod.py nodaemon
```
Should the radio crash for any reason this will be displayed on the screen allowing the problem to be analysed. Use this if the radio seems to just hang.  

## Option 2 Test rotary encoders
If experiencing problems with rotary encoders, stop the radio and select option 2. The following will be displayed showing the configuration as set in **/etc/radiod.conf**:
```
Press Ctrl-C to exit diagnostic mode
Test standard rotary encoder Class
Left switch GPIO 14
Right switch GPIO 15
Up switch GPIO 24
Down switch GPIO 23
Mute switch GPIO 4
Menu switch GPIO 17
Rotary encoder step size = half
KY040 encoder R1 resistor fitted = no
Waiting for events
```
Operate the Volume and Tuner rotary encoders and push buttons. The following should be seen.
```
Volume event  1 CLOCKWISE
Volume event  1 CLOCKWISE
Volume event  2 ANTICLOCKWISE
Volume event  2 ANTICLOCKWISE
Tuner event  2 ANTICLOCKWISE
Tuner event  2 ANTICLOCKWISE
Tuner event  1 CLOCKWISE
Tuner event  1 CLOCKWISE
Tuner event  3 BUTTON DOWN
Volume event  3 BUTTON DOWN
```
If not check that your rotary encoder wiring matches the displayed configuration.

## Option 3 Test push-buttons
If experiencing problems with rotary encodersstop the radio and select option 2. The following will be displayed showing the configuration as set in **/etc/radiod.conf**:
```
Test Button Class
Left switch GPIO 14
Right switch GPIO 15
Mute switch GPIO 4
Up switch GPIO 24
Down switch GPIO 23
Menu switch GPIO 17
Pull Up/Down resistors UP
Record switch GPIO 27 Pull Up
```
Operate each of the buttons inturn. The following should be seen:
```
Button pressed on GPIO 24
Button pressed on GPIO 15
Button pressed on GPIO 14
Button pressed on GPIO 15
Button pressed on GPIO 14
Button pressed on GPIO 4
Button pressed on GPIO 17
Button pressed on GPIO 27
```
If not check that your button wiring matches the displayed configuration.

## Option 4 Test events layer
It may well be that all buttons and rotary encoders are working with the diagostic tests but the radio still isn't responding to the radio controls. If not run option 4.

```
Waiting for events:
```
Operate each of the buttons inturn. The following should be seen:
```
Event 7 MENU_BUTTON_DOWN
Event 6 DOWN_SWITCH
Event 6 DOWN_SWITCH
Event 5 UP_SWITCH
Event 5 UP_SWITCH
Event 3 MUTE_BUTTON_DOWN
Event 2 LEFT_SWITCH
Event 1 RIGHT_SWITCH
Event 22 RECORD_BUTTON
Event 22 RECORD_BUTTON
Event 22 RECORD_BUTTON
```
If the above is seen you can rule out the Rotary Encoders or Buttons being the problem. Most likely cause of a lack of response to the controls is that the radio program has either crashed or has hung. 

## Option 5 Test configured display
If you are having display problems this can be tested by selecting option 5 which should display the following:
```
Press Ctrl-C to exit diagnostic mode
Test display_class.py
Screen LCD Lines=4 Character width=20
Display type 1 LCD
bg_color 7 White
```
On the screen something similar to the following should be displayed:
```
bobrathbone.com
Line 2 123456789
Line 3 123456789
End of test
```
Again if this isn't working check your wiring and that the correct display that you are using has been configured in **radio-config**

## Option 6 Test GPIOs 
This is a very basic test of all of the available GPIOs. It is simplest way to check which GPIO a particular button or rotary encoder is connected to and can show any wiring faults. 
```
GPIO: 2 State:High
GPIO: 3 State:High
GPIO: 4 State:High
GPIO: 5 State:High
GPIO: 6 State:High
GPIO: 7 State:High
GPIO: 8 State:High
GPIO: 9 State:High
GPIO: 10 State:High
GPIO: 11 State:High
GPIO: 12 State:High
GPIO: 13 State:High
GPIO: 14 State:High
GPIO: 15 State:High
GPIO: 16 State:High
GPIO: 17 State:High
GPIO: 18 State:High
GPIO: 19 State:High
GPIO: 20 State:Low
GPIO: 21 State:High
GPIO: 22 State:High
GPIO: 23 State:High
GPIO: 24 State:High
Error: GPIO 25 'GPIO busy'
Check conflict with GPIO 25 in other programs or in /boot/config.txt
GPIO: 26 State:High
GPIO: 27 State:High
Waiting for input events:
```
**Note:** The conflict with GPIO 25 is because GPIO 25 in this case is being used for the IR remote sensor and may be ignored. Operate either the buttons or rotary encoders. Activity should be seen as shown in the example below: 
```
GPIO 15 falling
GPIO 4 falling
GPIO 4 rising
GPIO 15 rising
```

## Option 7 Display Radio and OS configuration
Option 7 displays details of the Operating System and radio using the following menu: 

```
          Select information to display 
    1 Display radio version and build
    2 Display Operating System details
    3 Display Raspberry Pi model
    4 Display wiring
    5 Display WiFi
    6 Display full radio configuration
    7 Display formatted /etc/radiod.conf
    8 Display current Music Player Daemon output
    9 Display Sound Cards
   
          <Ok>                    <Cancel>
```
The best way to become familiar with this information is to try each option in turn.

End of tutorial
===============
