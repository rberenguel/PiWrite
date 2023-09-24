# PiWrite

#### What?

Have you ever wanted to use your Kindle Paperwhite to write, even more, with a vim-like editor? This is what PiWrite is for.

#### How?

The TL;DR is _a webserver running somewhere a keyboard can be plugged, and a page opened in the Kindle's web browser_.

The not-so-short version requires more effort and details, but is the UX I wanted to get:

- A Raspberry Pi Zero W…
- Paired with a Bluetooth keyboard…
- Set up in access point mode…
- With this package installed…
- And configured to start automatically on boot.

#### Why?

I was inspired by [SolarWriter by Michael Solomon](https://solarwriter.msol.io). I had always wanted to use my Kindle for writing. SolarWriter solves that by setting up a local web server on your phone (iOS or Android), then you type with a Bluetooth keyboard paired with it. But you need to set up hotspot, keep your screen on… I didn't like those parts. So I wrote this.

#### Contributions?

This is open source, and I'll be happy to see it extended and improved. But I'm unlikely to accept contributions: I want a reduced feature set, with only what _I_ need. This is why I didn't release this to PyPI, so anybody can have its own version with custom tweaks and installs it easily from their own repository.

---

<a href="https://www.buymeacoffee.com/rberenguel" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="51" width="217"></a>

---

# Installing the package

With a current enough version of `pip` you can install directly from the repository (or from your fork) with

```bash
pip install piwrite@git+https://github.com/rberenguel/PiWrite
```

Or with pipx (**recommended**) with

```bash
pipx install piwrite@git+https://github.com/rberenguel/PiWrite
```
You might need to add `/home/YOU/.local/bin` to your `PATH` (like adding `export PATH="/home/YOU/.local/bin:$PATH"` at the end of your `.bashrc`, `.zshenv` or similar).

# Trying it before installing

Once you have installed it you can try it locally (by default it will serve back at `127.0.0.1:80`), and optionally configure host and port, like:

```bash
PIWRITE_HOST=pi
PIWRITE_PORT=31415
```

Point your web browser to this address and try! The editor is vim inspired, and the instructions can be found in [help](piwrite/help)

# Setting up your Raspberry Pi Zero

If you need a Pi, I can't recommend [Pimoroni](https://shop.pimoroni.com) enough. I'm not affiliated, I just buy always from them.

## Basics

Best is installing a lightweight Raspbian version, since the Zero is not a terribly fast machine. By "mistake" (I was trying something) I updated the lite version (on Buster, I think) to Bookworm. Don't do that, not needed.

To configure everything you will need to set up the Raspberry for `ssh` access, and better with password. For using it as a "magical thing that lets the Kindle work as a text editor" is better if you disable requiring password for logging in via `tty`. You can enable this (known as autologin) by running `sudo raspi-config`, in the _System Options_ section. You specifically want _Console autologin_.

You also better set up wifi connectivity too. You can set this up by adding a wpa_supplicant.conf file to the boot partition of the SD card with contents like the following:

```
network={
    ssid="YOUR_NETWORK_NAME"
    psk="YOUR_PASSWORD"
    key_mgmt=WPA-PSK
}
```

Steps needed after this:
- Pair with a Bluetooth keyboard;
- Set up a wireless access point on your Raspberry;
- Install the package and set it up;
- Nice-to-have: ssh via USB (there are many tutorials for this).

## Pairing with a Bluetooth keyboard

Pick your poison. The standard way is using `bluetoothctl`. I found that installing [Bluetuith](https://darkhz.github.io/bluetuith/Installation.html) was more convenient to be sure the pairing had worked. On the con side, you need to install the whole Go runtime. 

Remember: the keyboard will be usable in the `tty` session, not in any ssh-initiated session.

If you want any fancy keyboard configuration (I use Colemak, and like my caps to be control) you will have to edit `/etc/default/keyboard` and add something like the following:

```
XKBMODEL="pc105"
XKBLAYOUT="us"
XKBVARIANT="colemak"
XKBOPTIONS="ctrl:nocaps"
```

## Wireless access point

I followed the instructions from here: [Turn a Raspberry Pi into a Web Server with Its Own Wifi Network (Tech Note)](https://www.stevemurch.com/setting-up-a-raspberry-pi-for-ad-hoc-networking-tech-note/2022/12). From these instructions, you can (optionally) skip the routing stuff for this. Although the post mentions _only_ working in Buster, I followed the exact same steps and worked just fine in Bookworm.

The TL;DR version:


Get the access point and DNS services
```
sudo apt install hostapd dnsmasq
```

Turn it on
```
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
```

Edit `/etc/dhcpcd.conf` (sudo) and add at the end

```
interface wlan0
    static ip_address=192.168.11.1/24
    nohook wpa_supplicant
```

> [!IMPORTANT]
> When you want to re-connect your Zero to your wifi, you need to comment this out, otherwise you are out of AP access and out of SSH via Wifi (or even USB gadget) access. If you forget, you'll need to edit the raw disk from another Linux device.

You now need to configure `/etc/dnsmasq.conf` with

```
interface=wlan0 # Listening interface
dhcp-range=192.168.11.2,192.168.11.20,255.255.255.0,24h
                # Pool of IP addresses served via DHCP
domain=write     # Local wireless DNS domain
address=/pi/192.168.11.1
                # Alias for this router
```
and now that you are at it, change `/etc/hostname` to be `pi`.

Finally, configure `/etc/hostapd/hostapd.conf` with (use your country code, of course)

```
country_code=CH
interface=wlan0
ssid=EnchantedRose
hw_mode=g
channel=7
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=CHOOSE SOMETHING
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

Now, reboot (`sudo shutdown -r now` or `sudo systemctl reboot`).

If you ever want to disable AP and enable normal wifi, run `sudo systemctl disable hostapd dnsmasq` AND remove the static IP setting mentioned above.

## Install the package and set it up

Install pipx with `sudo apt install pipx` and then install piwrite with

```bash
pipx install piwrite@git+https://github.com/rberenguel/PiWrite
```

You'll want to add `pipx`'s binaries to the path, for example by adding `export PATH="/home/YOU/.local/bin:$PATH"`.

Since the ideal experience is _not_ having to add a port in the Kindle browser, the default port piwrite uses is 80. But that needs allowlisting:

`sudo setcap CAP_NET_BIND_SERVICE=+eip /usr/bin/python3.11`

Tweak the Python version depending on what you have.

You can test if it works (i.e.. if it is the right version or not) or not by starting piwrite now (you may need to change the exported host).

You'll also want to start piwrite on `tty` user start, you can do this by adding the following to the end of your `.profile`

```
export PIWRITE_HOST=pi.write # or pi, if it's not under the access point
piwrite
```

---

## Some oddities

The Kindle browser is weird and does not support everything. No websockets, only longpolling (or so it seems). For some reason, only version 3.0 of the socketio JavaScript libraries worked correctly. I found no way to get the Kindle browser to rotate the whole page via CSS so I could have a landscape view.

My first trial implementation tried using pynvim (the NeoVim API layer) as the underlying editor. That would have been awesome, real vim! But it didn't work for obscure reasons (I had to do some unholy things with asyncio that caused it to explode easily).

## Development

I wrote half of this directly on the Zero from my iPad, using [Blink](https://blink.sh) to SSH into it. The second half, I wrote it on my iPad with [iVim](https://apps.apple.com/es/app/ivim/id1266544660?l=en-GB), [ish](https://ish.app) and [Inspect Browser](https://apps.pdyn.net/inspect/). The finishing touches (moving to Poetry and cleaning up), on my Mac. For local development, you can then use basically anything. Just choose a valid port for your system and make sure the host is valid. 127.0.0.1 is the default choice and the one that should work.

---

<a href="https://www.buymeacoffee.com/rberenguel" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="51" width="217"></a>

---
