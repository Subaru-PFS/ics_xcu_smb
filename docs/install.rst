Create bootable microSD card
----------------------------

Raspberry Pis need a bootable micro-SD card. We start with `Raspbian
Lite <https://www.raspberrypi.org/downloads/raspbian/>` and add on to
that. That is actually all you need to do, but for PFS we build a
mostly-configured image, documented in buildPfsImage_ and
download that instead.

- Find a decent micro-SD card. 
- Write (using dd, `Etcher <https://www.balena.io/etcher/>`, etc.) the
  pre-configured image to the sd card.

- Plug it in to the PFS network and boot it. ssh to
  pi@raspberrypi.local. Password is the PFS default (or "raspberry" if
  the image has not been configured for PFS).

- The get the MAC address, ``ifconfig`` at the command-line and look
  for the MAC address on the "ether" line for ``eth0``.
  
- Finish configuring the Pi by running ``sudo raspi-config``, then:
  - Network Options, set hostname to "localhost" (yes, I mean that)

.. _buildPfsImage:

Build PFS Image
---------------

To turn a vanilla Raspbian Lite image into a mostly-configured PFS image,

- Find a decent micro-SD card. 
- Write (using dd, `Etcher <https://www.balena.io/etcher/>`, etc.) the
  Raspbian image to the sd card.
- mount it (easier with Linux/OS X)
- touch /boot/ssh (enables ssh server for 1st (!!) connection).
- eject and insert into a Pi for further configuration.
  
Plug it in to any network with a DHCP server and boot it. ssh to
pi@raspberrypi.local. Password is "raspberry".

Install some additional packages. We need to update the installed
pacakges first, or there can be conflicts:

- sudo apt-get update
- sudo apt-get upgrade
- sudo apt-get install emacs25-nox tcpdump strace lsof sqlite3 git
# - sudo apt-get install lightdm lxde-core x11-utils x11-apps
- sudo apt-get install ipython3 python3-numpy cython3 python3-pip python3-pyqt5 python3-pyqt5.qtsql
- sudo apt-get install christ what a clusterfuck.
- pip3 install RPi.GPIO
- pip3 install spidev
- pip3 install smbus
- pip3 install natsort
  
- add /software to /etc/fstab (``nano /etc/fstab``, and add ``tron:/software /software defaults,ro 0 0``

- "sudo raspi-config", then:
  - Change User Password to PFS standard
  - Interfacing Options, enable ssh

Reboot and ssh back in, finish configuring:

- "sudo raspi-config", and
  - Interfacing Options, enable SPI, enable I2C, enable VNC (this will install tons of packages)
  - Boot Options, B1: select B4 (Autologin to desktop GUI)
  - Advanced Options, A1 (Expand filesystem), A5 Resolution to 1280x1024

Add boot image:
- sudo mkdir /db
- sudo chown pi:pi /db
- sudo chmod 2775 /db
- other stuff

Disable interfaces:
- Add "dtoverlay=pi3-disable-wifi" to /boot/config.txt
- Add "dtoverlay=pi3-disable-bt" to /boot/config.txt
  
Shutdown the pi, copy image _off_ of micro-SD card. Use that to build new systems.


