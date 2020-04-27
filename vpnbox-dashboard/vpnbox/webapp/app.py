import json
import logging
import os
import urllib.request

import falcon

from vpnbox import commands

logger = logging.getLogger(__name__)


class DevicesResource:
    def on_get(self, req: falcon.Request, resp: falcon.Response):
        resp.media = self._ip_a()

    def _ip_a(self):
        return commands.ip_a()


class ServicesResource:

    def on_get_list(self, req, resp):
        resp.media = self._get_list()

    def on_get_status(self, req, resp, service):
        resp.media = self._get_status(service)

    def on_get_log(self, req, resp: falcon.Response, service):
        resp.content_type = 'text/plain'
        resp.body = self._get_log(service)

    def on_get_running(self, req, resp, service):
        status = self._require_service(service)

        resp.media = status['SubState'] == 'running'

    def on_patch_running(self, req, resp: falcon.Response, service):
        code = commands.systemctl_start(service)
        if code == 0:
            resp.media = True
        else:
            resp.media = False
            raise falcon.HTTPUnauthorized

    def on_put_running(self, req, resp: falcon.Response, service):
        code = commands.systemctl_restart(service)
        if code == 0:
            resp.media = True
        else:
            resp.media = False
            raise falcon.HTTPUnauthorized

    def on_delete_running(self, req, resp: falcon.Response, service):
        code = commands.systemctl_stop(service)
        if code == 0:
            resp.media = True
        else:
            resp.media = False
            raise falcon.HTTPUnauthorized

    def _get_list(self):
        return commands.systemctl_list()

    def _get_status(self, service):
        return commands.systemctl_show(service)

    def _get_log(self, service):
        return commands.journalctl(service)

    def _require_service(self, service):
        status = self._get_status(service)
        if status['LoadState'] == 'not-found':
            raise falcon.HTTPNotFound
        return status


class WifiScanResource:
    def on_get(self, req, resp):
        resp.media = commands.wpa_scan_result()


class WifiNetworksResource:
    def on_get(self, req, resp):
        resp.media = commands.wpa_list_networks()


class WifiStatusResource:
    def on_get(self, req, resp):
        resp.media = commands.wpa_status()


class IpInfoResource:
    def on_get(self, req, resp):
        try:
            doc = urllib.request.urlopen('http://ipinfo.io/json', timeout=5).read()
            resp.media = json.loads(doc.decode('utf-8'))
        except:
            logger.exception("Exception while fetching ipinfo.io/json")
            resp.media = {}


class HealthResource:
    def on_get(self, req, resp):
        wifi_status = self._get_wifi_status()
        internet_status = self._get_internet_status()
        vpn_status = self._get_vpn_status()

        resp.media = {
            'wifi': wifi_status,
            'internet': internet_status,
            'vpn': vpn_status,
        }

    def _get_vpn_status(self):
        try:
            status = commands.systemctl_show('openvpn-client@vpnbox')
            if status['SubState'] != 'running':
                return False
        except:
            return False

        ifs = commands.ip_a()
        for i in ifs:
            if i['ifname'] != 'tun0':
                continue

            for addr in i['addr_info']:
                if addr['family'] == 'inet':
                    if addr['local']:
                        return True

        return False

    def _get_wifi_status(self):
        try:
            return commands.wpa_status()['wpa_state'] == 'COMPLETED'
        except:
            return False

    def _get_internet_status(self):
        try:
            return commands.is_host_up('1.1.1.1')
        except:
            logger.exception("error while checking if host is up")
            return False


class HtmlResource:

    def __init__(self, fpath) -> None:
        super().__init__()
        self.fpath = fpath

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        with open(self.fpath, 'r') as f:
            resp.body = f.read()


def setup(api: falcon.API):
    logging.basicConfig(level=logging.WARNING)

    api.add_route('/api/devices', DevicesResource())

    api.add_route('/api/ipinfo', IpInfoResource())

    api.add_route('/api/health', HealthResource())

    services = ServicesResource()
    api.add_route('/api/services', services, suffix='list')
    api.add_route('/api/services/{service}', services, suffix='status')
    api.add_route('/api/services/{service}/running', services, suffix='running')
    api.add_route('/api/services/{service}/log', services, suffix='log')

    api.add_route('/api/wifi/scan', WifiScanResource())
    api.add_route('/api/wifi/networks', WifiNetworksResource())
    api.add_route('/api/wifi/status', WifiStatusResource())

    # static resources
    working_dir = os.getcwd()
    api.add_static_route('/static', os.path.join(working_dir, 'vpnbox/webapp/static/'))
    api.add_route('/', HtmlResource(os.path.join(working_dir, 'vpnbox/webapp/static/index.html')))
