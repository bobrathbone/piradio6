Running Shoutcast
==============================
## Operation
Shoutcast can be invoked in two ways:
1) From the Web Interface
2) From the Command Line

## Running Shoutcast from the Web Interface
Using any Web browser open the Web Interface (if installed) by entering the URL for your Raspberry Pi, for example **http://\<your IP address\>**. Click on the Shoutcast tab to open the interface. Fill in the search form and press the Submit button once and wait until the summary page is displayed.the Web Interfdace

## Running Shoutcast from the Command Line
The Shoutcast program **get_shoutcast.py program** can be run from the Command Line

```
$ cd /usr/share/radio
$ ./get_shoutcast.py
```
This will display the following:
```
Shoutcast UDP connect host localhost port 5100
This program must be run with sudo or root permissions!

Usage: sudo ./get_shoutcast.py id=<id> limit=<limit> search="<string>"|genre="<genre>" install
        Where:  <id> is a valid shoutcast ID.
                <limit> is the maximum stations that will be returned (default 100).
                <string> is the string to search the shoutcast database.
                <genre> is the genre search string.
                install - Install playlist to MPD without prompting.

        See http://www.shoutcast.com for availble genres.
```
### Examples
```
sudo ./get_shoutcast.py id=anCLSEDQODrElkxl limit=50 search="Beatles" install
sudo ./get_shoutcast.py limit=100 genre="Country" 
```

If id= isn't specified it will be picked up from **/etc/radiod.conf**
See the **shoutcast_key** in **/etc/radiod.conf** for the id=parameter
shoutcast_key=anCLSEDQODrElkxl

End of tutorial
===============
