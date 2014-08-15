from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from database_service import app
from tornado import autoreload
import logging

logging.getLogger('tornado').setLevel(logging.DEBUG)
logging.getLogger(__name__).setLevel(logging.DEBUG)

handler = logging.FileHandler('/tmp/db_runs')

logging.getLogger('tornado').addHandler(handler)
logging.getLogger(__name__).addHandler(handler)

import newrelic.agent
newrelic.agent.initialize('newrelic.ini')


http_server = HTTPServer(WSGIContainer(app))
http_server.bind(5000)
http_server.start(0)
ioloop = IOLoop.instance()
autoreload.start(ioloop)
ioloop.start()
