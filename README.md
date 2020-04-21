VPN Box
=======

Use your Raspberry PI as a WiFi VPN middlebox.

Description
-----------

Assumes two WiFi interfaces: `wlan0` (the internal WLAN module) that is used as uplink, and one `wlan1` that is used with hostapd to create an access point.
All traffic from `wlan1` is routed through a VPN tunnel running on `tun0`.

The OpenVPN client runs as an instance of a systemd service (`openvpn-client@.service`), and is restarted using the `wpahook-restart-vpn` any time the `wlan0` uplink reconnects to some other WLAN.

### Requires:

* hostapd
* dnsmasq
* python3
* `wpa_cli`

### Project

* `etc` service scripts to make it work
* `vpnbox-dashboard` Web UI hosted on the box used for diagnostics

### Resources/Docs

* https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md
* https://community.openvpn.net/openvpn/wiki/Systemd

iptables are configured slightly different than in the RPi doc:

```
iptables -t nat -A POSTROUTING -o tun0 -j MASQUERADE
iptables -A FORWARD -i tun0 -o wlan1 -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i wlan1 -o tun0 -j ACCEPT
```
