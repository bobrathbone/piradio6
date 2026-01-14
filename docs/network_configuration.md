Configuring network roaming on a Raspberry Pi
============================================= 
Normally the network is configured by the Rpi-imager software when creating the SD-card. However, you may wish to add a second or third Wi-Fi access point to enable Wi-Fi roaming for example between your home and office. These extra WiFi network points will be typically another router at a different location for example "office" or a repeater in the same building. 

To see what Wi-Fi access points are available run the following **iwlist** command:

**sudo iwlist scan | grep ESSID**
```
      lo    Interface doesn't support scanning.

                    ESSID:"EE-K50J9R"
                    ESSID:"Office"
                    ESSID:"NEIGHBOUR"
                    ESSID:"TP-Link_D7D4"
      :
```
This will display all available Wi-Fi access points available in your immediate vicinity. You will of course only be able to connect to those networks that you have a password for. Note: Your iwlist display will be different from that above.

---

Bullseye OS network configuration using wpa_supplicant.conf 
===========================================================
**Bullseye** used extra entries in **wpa_supplicant.conf**. Edit the **/etc/wpa_supplicant/wpa_supplicant.conf** configuration file and add a second network definition. More network definitions can be added as required.


Example **/etc/wpa_supplicant/wpa_supplicant.conf** configured for two WiFi access points.
```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=GB

network={
        ssid="<Your-SSID>"
        psk="<Your-Router-Password>"
        key_mgmt=WPA-PSK
}

network={
        ssid="<Your-second-SSID>"
        psk="<Your-second-router-password>"
        key_mgmt=WPA-PSK
}
 
```

---

Bookworm and Trixie OS network configuration using Network Manager
==================================================================
**Bookworm** and **Trixie** do not use **wpa_suplicant.conf** but now use Network Manager using the following **nmcli** commands. 

## Switch on WiFi ##
**sudo nmcli radio wifi on**

## Add the new WiFi interface
**sudo nmcli connection add con-name "\<Your second SSID\>" type wifi ifname wlan0 ssid "\<Your second SSID\>"**

## Set up the password and authentication method
**sudo nmcli connection modify \<Your second SSID\> 802-11-wireless-security.key-mgmt wpa-psk wifi-sec.psk "\<Your 2nd router password\>"**


Each new Wi-Fi network added has a separate config file in **/etc/NetworkManager/system-connections/** in a well configured system these will have a 256bit WPA PSK rather than a plain text passphrase.
For example for an SSID **EE-GH6J42** the previous instructions will produce a file called **EE-GH6J42.nmconnection** in the **/etc/NetworkManager/system-connections** directory.

You may wonder where the original connection for router, for example **EE-B944TH** is to be found. If you look in the **/run/NetworkManager/system-connections/** you will see the following files.

```
 lo.nmconnection   netplan-wlan0-EE-B944TH.nmconnection  'Wired connection 1.nmconnection'
```
This is because Debian Linux is now using a product called **netplan** to configure the Raspberry Pi which takes the parameters specified using the **Raspberry Pi Imager software** and configures the initial network configuration in the **/run** directory. This is rather confusing to have network configurations in two seperate directories and perhaps, for this reason, this may well change in the future! 


```
[connection]
id=<Your second SSID>
uuid=8e2ed8c9-faa2-4ad2-a8f5-a956d8afc7c1
type=wifi
interface-name=wlan0

[wifi]
mode=infrastructure
ssid=<Your second SSID>

[wifi-security]
key-mgmt=wpa-psk
psk=<Your 2nd router password>

[ipv4]
method=auto

[ipv6]
addr-gen-mode=default
method=auto

[proxy]
```

## To connect and enable data roaming to the second router enter the following command:

**sudo nmcli connection up \<Your 2nd router SSID\>**
NB. Do not use quotes around your router SSID for example
**sudo nmcli connection up "EE-Router2"** WRONG!
**sudo nmcli connection up EE-Router2**   CORRECT

---

Using the Network Manager nmtui utility
=======================================
Network manager provides the **nmtui** utility to add, delete and connect to new WiFi access points. To access it run:

```
sudo nmtui
```
Select \<Edit\> then \<Add\> then select **Wi-Fi** from the drop down list

```
 -------------------[ Edit Connection ]----------------------
|                                                            |
|            Profile name <Your SSID>                        |
|                  Device wlan0                              |
|                                                            |
|   WI-FI                                          <Hide>    |
|                    SSID <Your SSID>                        |
|                    Mode <Client>                           |
|                                                            |
|                Security WPA & WPA2 Personal                |
|                Password <Your router password>             |
|                [X] Show password                           |
|                                                            |
|                   BSSID ________________________           |
|      Cloned MAC address ________________________           |
|                     MTU __________ (default)               |
|                                                            |
|                                                            |
|   IPv4 CONFIGURATION    <Automatic>              <Show>    |
|   IPv6 CONFIGURATION    <Automatic>              <Show>    |
|                                                            |
| [X] Automatically connect                                  |
| [X] Available to all users                                 |
|                                                            |
|                                             <Cancel> <OK>  |   
|                                                            |
 ------------------------------------------------------------
```
Use the arrow keys to move around the screen. The space bar selects [X] 
Enter your router SSID into *both* the **Profile name** and **SSID** fields
The **Device** will always be **wlan0** unless you have an extra WiFi adapter
Select **WPA & WPA2 Personal** in the Security drop-down box
Enter your router password into the **Password** field
Leave all other fields as they are then press \<OK\>

Unfortunately connecting to the 2nd router doesn't work using **nmtui** because it doesn't display the new router just added. Use the following command:
**sudo nmcli connection up \<Your SSID\>**
NB. Do not use quotes around your router SSID.

More details will be found in the Radio Constructors manual


---

End of tutorial
===============
