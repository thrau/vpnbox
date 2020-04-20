import logging
import os

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

    def _get_list(self):
        return commands.systemctl_list()

    def _get_status(self, service):
        return commands.systemctl_show(service)

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
    logging.basicConfig(level=logging.INFO)
    api.add_route('/api/devices', DevicesResource())

    services = ServicesResource()
    api.add_route('/api/services', services, suffix='list')
    api.add_route('/api/services/{service}', services, suffix='status')

    # static resources
    working_dir = os.getcwd()
    api.add_static_route('/static', os.path.join(working_dir, 'vpnbox/webapp/static/'))
    api.add_route('/', HtmlResource(os.path.join(working_dir, 'vpnbox/webapp/static/index.html')))
