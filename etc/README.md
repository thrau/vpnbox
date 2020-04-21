WPA Hook
========

Restarts any running OpenVPN clients registered as systemd services when the wifi reconnects

Uses `wpa_cli` and a hook script to react on wpa_supplicant CONNECT events.
