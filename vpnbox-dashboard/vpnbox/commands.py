import json

import sh


def ip_a():
    out: sh.RunningCommand = sh.ip('--json', 'a')
    doc = json.loads(out.stdout)
    return doc


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


if __name__ == '__main__':
    print(systemctl_list())
