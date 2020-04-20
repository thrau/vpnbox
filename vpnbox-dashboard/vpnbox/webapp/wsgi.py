import logging

import falcon

import vpnbox.webapp.app as app

logger = logging.getLogger(__name__)

api = falcon.API(middleware=[])
app.setup(api)
