Downloading and building the radiod package from GitHub
=======================================================
## Introduction ##
When you install the **radiod** package you get all the of source files in the **/usr/share/radio** directory. However, the build scripts and package configuration files required to build the **radiod** package need to be downloaded from **GitHub**. **GitHub** is a proprietary developer platform that allows developers to create, store, manage, and share their code.

## Package creation ##
To create the radiod Debian package log into the Raspberry Pi and clone the source tree from GitHub.
```
cd
git clone https://github.com/bobrathbone/piradio6
```
Now change directory to **radio6** and make **setup.sh** executable then run it.
```
cd piradio6
chmod +x setup.sh
./setup.sh
```
This will install all of the necessary packages for the development environment and then run **build.sh**. 
The **setup.sh** script only needs to be run once. Subsequent builds can be done by just running the **./build.sh** script.
*Note:* The control file for the package build is called **piradio**
```
./build.sh
```
Finally install the new package. 
```
sudo dpkg -i radiod_8.0_all.deb
```
This will install the **radiod** package and supporting files in the **/usr/share/radio** directory. 
To configure the **radiod** package further run **radio-config** from the command line.
```
radio-config
```

Contributing to the source of radiod on GitHub
==============================================
The principle aim of **GitHub** apart from providing a repository for project sources is to provide a platform that can be used by developers in a collaborative manner. The previous instructions just create a package locally on your development machine only. If you wish to submit your code changes to be included in the **radiod** project then it is necessary to follow GitHub procedures. This normally entails creating a **fork** of the main source trre and to make your changes to the fork you created. Once your changes have been tested you need to issue a **pull request** which allows   the project owner to examine and approve your changes and then **merge** these into the main source tree.

See [GitHub documentation](https://docs.github.com/en) for further information

Licences
=====
**radiod** is released under the
[GNU General Public License version 2](https://www.gnu.org/licenses/gpl-2.0.txt)

See [bobrathbone.com/raspberrypi/pi_internet_radio.html](https://bobrathbone.com/raspberrypi/pi_internet_radio.html) for further information
