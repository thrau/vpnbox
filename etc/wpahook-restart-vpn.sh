#!/bin/sh

logger System "detected wpa event $2 on $1"
case "$2" in
CONNECTED)
	echo "connected $1"
	systemctl restart 'openvpn-client@*'
	;;
DISCONNECTED)
	echo "disconnected $1"
	;;
*)
	echo "unhandled event $2 on $1"
	;;
esac

