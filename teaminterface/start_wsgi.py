from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from team_interface import app
from tornado import autoreload
import logging
logging.getLogger('tornado').setLevel(logging.DEBUG)
logging.getLogger(__name__).setLevel(logging.DEBUG)
http_server = HTTPServer(WSGIContainer(app))
http_server.bind(8000)
http_server.start(0)
ioloop = IOLoop.instance()
autoreload.start(ioloop)
ioloop.start()

