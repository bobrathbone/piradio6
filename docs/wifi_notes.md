WiFi Link Quality Notes
=========================

## To get WiFi status 
1) Log into the Raspberry Pi and run the **radio-config** utility
2) Select option **5 Diagnostics and Information**
3) Select option **7 Display Radio and OS configuration**
4) Run option **5 Display WiFi**
5) See the line called **Link Quality=70/70  Signal level=-38 dBm**

## Interpretation of Signal level
**-30 dBm** Maximum signal strength, usually attained if the RPi is very close to the Wi-Fi access point    Excellent for all services

**-50 dBm** Anything down to this level can be regarded as excellent signal strength    Excellent for all services

**-60 dBm** This is still a good, reliable signal strength  Good for all services

**-67 dBm** This is the minimum value for all services that require smooth and reliable data traffic.       Minimum required for streaming services including for the radio

**-70 dBm** The signal is not very strong, but mostly sufficient.   Only good for Web browsing, email, and the like

**-80 dBm** Minimum value required to make a connection. You cannot count on a reliable connection or sufficient signal strength to use services at this level  The radio will not work reliably at this level

**-90 dBm** It is very unlikely that you will be able to connect or make use of any services with this signal strength. The radio cannot operate reliably at this level.

## Poor signal
If the signal strength is poor, try re-positioning the radio nearer the router or use a repeater (TP-Link or similar). Position away from radiators or other large metal objects such as fridges and freezers.

End of notes
============
