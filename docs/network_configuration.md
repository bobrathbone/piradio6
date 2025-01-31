Configuring network roaming on a Raspberry Pi
============================================= 
Normally the network is configured by the Rpi-imager software when creating the SD-card. However, you may wish to add a second or third Wi-Fi access point to enable Wi-Fi roaming for example between your home and office. 

To see what Wi-Fi access points are available run the following **iwlist** command:


```
$ sudo iwlist scan | grep ESSID
lo        Interface doesn't support scanning.

                    ESSID:"EE-K7TZ9R"
                    ESSID:"Garden Office"
                    ESSID:"WATERSTONES"
                    ESSID:"TP-Link_D7D4"
      :
```

This will display all available Wi-Fi access points available in your immediate vicinity. You will of course only be able to connect to those networks that you have a password for. 

Bullseye OS network configuration using network manager
=======================================================
Edit the **/etc/wpa_supplicant/wpa_supplicant.conf** configuration file and add a second network definition. 


```
$ cat /etc/wpa_supplicant/wpa_supplicant.conf
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
        psk="<Your-second-Router-Password>"
        key_mgmt=WPA-PSK
}
 
```

Bookworm OS network configuration using network manager
=======================================================
**Bookworm** does not use wpa_suplicant.conf but now uses Network Manager using the following **nmcli** commands. 


**sudo nmcli radio wifi on**
**sudo nmcli dev wifi connect \<wifi-ssid\> password "\<network-password\>"**

Each Wi-Fi network has a separate config file in **/etc/NetworkManager/system-connections/** in a well configured system these will have a 256bit WPA PSK rather than a plain text passphrase.


```
/etc/NetworkManager/system-connections/preconfigured.nmconnection
[connection]
id=preconfigured
uuid=026304ea-6b98-4e52-8765-0e71125962c8
type=wifi
[wifi]
mode=infrastructure
ssid=EE-K7TZ9R
hidden=false
[ipv4]
method=auto
[ipv6]
addr-gen-mode=default
method=auto
[proxy]
[wifi-security]
key-mgmt=wpa-psk
psk=5e3415b308da9e7cb5c633a5dd78d597c77262e73473f63c93ba3552f7cadf21
```

To configure a second Wi-Fi connection use nmcli:
**sudo nmcli dev wifi connect \<SSID\> password \<password\>**

Where SSID is the name of the second Wi-Fi access point (router or repeater) and password is an encrypted key or password. Note that a plain text password must be enclosed in quotes ("").

**sudo nmcli dev wifi connect TP-Link_D7D4 password "89157405"**

The above command if successful will create a file called in **TP-Link_D7D4.nmconnection** in the directory **/etc/NetworkManager/system-connections/** as shown in the following example.


```
[connection]
id=TP-Link_D7D4
uuid=4ad31ca8-64ce-41ad-bcb2-34b8b7447117
type=wifi
interface-name=wlan0
timestamp=1725363073

[wifi]
mode=infrastructure
ssid=TP-Link_D7D4

[wifi-security]
auth-alg=open
key-mgmt=wpa-psk
psk=88358475

[ipv4]
method=auto

[ipv6]
addr-gen-mode=default
method=auto

[proxy]

```

End of tutorial
===============
