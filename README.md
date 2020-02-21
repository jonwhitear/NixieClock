# NixieClock
A clock using "nixie" numerical indicator tubes with LED backlights. Written in Python using a Flask web app to expose the API, which allows you to control the brightness of the nixies, and the brightness and colour of the LED backlights.

## Install

Read this for setting up a headless Raspberry Pi: https://www.raspberrypi.org/documentation/configuration/wireless/headless.md.

1. Download the latest Raspbian Lite image (smallest, no desktop needed)
2. Flash the image to SD card. I use Balena Etcher.
3. For headless setup, SSH can be enabled by placing a file named 'ssh', without any extension, onto the boot partition of the SD card. On Mac Os try this: 
````
cd /Volumes/boot
touch ssh
````
4. Make sure your RPi can boot with a network connection, i.e. if you're using Wifi, put the wpa_supplicant.conf file in the boot folder, per the link above.
5. Put the SD card back in the Pi, and boot it.
6. SSH to your Pi. Default credentials for Raspbian are username: pi, password: raspberry.
7. Create a new user and delete user pi: https://www.raspberrypi.org/documentation/linux/usage/users.md
8. Change your hostname, locale etc: sudo raspi-config.
9. Reboot and log in as new user.
10. Update your install: sudo apt-get update, sudo apt-get upgrade.
11. Install git: sudo apt-get install git
12. Clone this repo to your Pi: git clone https://github.com/jonwhitear/NixieClock.git
sudo apt-get install python-rpi.gpio python3-rpi.gpio python-flask
113. Update /etc/rc.local to add your command before the exit line
````
python /home/jon/NixieClock/clock_queue.py &
exit 0
````

