# sphincterd

Daemon to communicate with [Sphincter](http://github.com/openlab-aux/sphincter) and exposes a HTTP API.

Starts a webserver and triggers hooks when a user with a registered token calls the webserver.
Used to toggle GPIOs on a Raspberry PI to open a door when a user sends the registered token to the web server.

# Installation

Install dependencies:

```
pip3 install pyserial sqlalchemy RPi.GPIO
```
or
```
apt install python3-serial python3-sqlalchemy python3-rpi.gpio
```

Copy folder sphinkter to `/usr/share/sphinkter`.
Copy `dist/lib/systemd/system/sphinkter.service` to `/etc/systemd/system/sphinkter.service`.
Create a user sphinkter `adduser sphinkter`
Start service `systemctl start sphinkter`.
Add users `./sphinkterd --adduser foo`.
