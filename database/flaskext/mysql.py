# -*- coding: UTF-8 -*-
from __future__ import absolute_import
import MySQLdb
import MySQLdb.cursors

from flask import _request_ctx_stack


class MySQL(object):
    def __init__(self, app=None):
        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def init_app(self, app):
        self.app = app
        self.app.config.setdefault('MYSQL_DATABASE_HOST', 'localhost')
        self.app.config.setdefault('MYSQL_DATABASE_PORT', 3306)
        self.app.config.setdefault('MYSQL_DATABASE_USER', None)
        self.app.config.setdefault('MYSQL_DATABASE_PASSWORD', None)
        self.app.config.setdefault('MYSQL_DATABASE_DB', None)
        self.app.config.setdefault('MYSQL_DATABASE_CHARSET', 'utf8')
        self.app.teardown_request(self.teardown_request)
        self.app.before_request(self.before_request)

    def connect(self):
        kwargs = {}
        if self.app.config['MYSQL_DATABASE_HOST']:
            kwargs['host'] = self.app.config['MYSQL_DATABASE_HOST']
        if self.app.config['MYSQL_DATABASE_PORT']:
            kwargs['port'] = self.app.config['MYSQL_DATABASE_PORT']
        if self.app.config['MYSQL_DATABASE_USER']:
            kwargs['user'] = self.app.config['MYSQL_DATABASE_USER']
        if self.app.config['MYSQL_DATABASE_PASSWORD']:
            kwargs['passwd'] = self.app.config['MYSQL_DATABASE_PASSWORD']
        if self.app.config['MYSQL_DATABASE_DB']:
            kwargs['db'] = self.app.config['MYSQL_DATABASE_DB']
        if self.app.config['MYSQL_DATABASE_CHARSET']:
            kwargs['charset'] = self.app.config['MYSQL_DATABASE_CHARSET']
	kwargs['cursorclass'] = MySQLdb.cursors.DictCursor
        return MySQLdb.connect(**kwargs)

    def before_request(self):
        ctx = _request_ctx_stack.top
        ctx.mysql_db = self.connect()

    def teardown_request(self, exception):
        ctx = _request_ctx_stack.top
        if hasattr(ctx, "mysql_db"):
            ctx.mysql_db.close()

    def get_db(self):
        ctx = _request_ctx_stack.top
        if ctx is not None:
            return ctx.mysql_db
