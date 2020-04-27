import json
import logging

import sh

logger = logging.getLogger(__name__)


def ip_a():
    out: sh.RunningCommand = sh.ip('--json', 'a')
    doc = json.loads(out.stdout)
    return doc


def is_host_up(host) -> bool:
    try:
        cmd = sh.ping('-c', '1', '-W', '2', host)
        return cmd.exit_code == 0
    except sh.ErrorReturnCode:
        return False


def systemctl_show(service):
    cmd = sh.systemctl('show', '--no-page', service)
    out = cmd.stdout.decode('utf-8')

    lines = out.splitlines()
    pairs = [tuple(line.split('=', 1)) for line in lines if line]
    return dict(pairs)


def systemctl_list():
    cmd = sh.systemctl('list-units', '-t', 'service', '--full', '--all', '--plain', '--no-legend')
    out = cmd.stdout.decode('utf-8')

    lines = out.splitlines()
    rows = [line.strip().split(maxsplit=4) for line in lines if line]

    keys = ['Id', 'LoadState', 'ActiveState', 'SubState', 'Description']
    records = [dict(zip(keys, row)) for row in rows]

    return records


def systemctl_restart(service):
    try:
        cmd: sh.RunningCommand = sh.sudo.systemctl('restart', service)
    except sh.ErrorReturnCode as e:
        logger.exception("Error executing restart %s", service)
        return e.exit_code

    return cmd.exit_code


def systemctl_stop(service):
    try:
        cmd: sh.RunningCommand = sh.sudo.systemctl('stop', service)
    except sh.ErrorReturnCode as e:
        logger.exception("Error executing stop %s", service)
        return e.exit_code

    return cmd.exit_code


def systemctl_start(service):
    try:
        cmd: sh.RunningCommand = sh.sudo.systemctl('start', service)
    except sh.ErrorReturnCode as e:
        logger.exception("Error executing start %s", service)
        return e.exit_code

    return cmd.exit_code


def journalctl(unit, boots=0):
    cmd = sh.journalctl('-u', unit, '-b', boots)
    out = cmd.stdout.decode('utf-8')
    return out


def _parse_wpa_cli_table(out, parse_flags=False):
    lines = out.splitlines()
    header = lines[0]
    rows = lines[1:]

    keys = [k.strip().replace(' ', '_') for k in header.strip().split('/')]
    data = [row.split('\t') for row in rows]
    data = [dict(zip(keys, d)) for d in data]

    if parse_flags:
        for d in data:
            if 'flags' in d:
                d['flags'] = _parse_wpa_cli_flags(d['flags'])

    return data


def _parse_wpa_cli_flags(flags_str):
    """
    :param flags_str:  [WPA-PSK-CCMP+TKIP][ESS]
    :return: ['WPA-PSK-CCMP+TKIP', 'ESS']
    """
    flags_str = flags_str.lstrip('[').rstrip(']')
    return flags_str.split('][')


def wpa_scan_result():
    # Result of wpa_cli that is parsed looks like this:
    #
    # bssid / frequency / signal level / flags / ssid
    # de:0d:17:48:09:04	2432	-16	[WPA-PSK-CCMP+TKIP][ESS]	Poolscheisser R Us
    # d8:0d:17:48:09:04	2432	-19	[WPA-PSK-CCMP+TKIP][WPA2-PSK-CCMP+TKIP][ESS]
    cmd = sh.wpa_cli('-i', 'wlan0', 'scan_result')
    out = cmd.stdout.decode('utf-8')

    return _parse_wpa_cli_table(out, parse_flags=True)


def wpa_list_networks():
    # Result of wpa_cli that is parsed looks like this:
    #
    # network id / ssid / bssid / flags
    # 1	Poolscheisser R Us	any
    # 2	Unseen University	any	[CURRENT]
    cmd = sh.wpa_cli('-i', 'wlan0', 'list_networks')
    out = cmd.stdout.decode('utf-8')

    return _parse_wpa_cli_table(out, parse_flags=True)


def wpa_status():
    # Output of `wpa_cli -i wlan0 status`:
    #
    # wpa_state=INACTIVE
    # p2p_device_address=9e:20:7b:9f:cb:ef
    # address=b8:27:eb:4c:e4:2e
    # uuid=030e3736-7413-50ff-a743-c0c1af804b67
    cmd = sh.wpa_cli('-i', 'wlan0', 'status')
    out = cmd.stdout.decode('utf-8')

    lines = out.splitlines()
    pairs = [tuple(line.split('=', 1)) for line in lines if line]
    return dict(pairs)
