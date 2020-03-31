#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Flask extension that provides easy MySQL connector functionality.
"""

from __future__ import absolute_import

import mysql.connector

from flask import _request_ctx_stack


class MySQL(object):
    """Flask object that wraps requests to provide MySQL functionality
    transparently.

    Note: MYSQL_DATABASE_UNIX_SOCKET takes preference over TCP parameters.
          Set it to None to use MYSQL_DATABASE_HOST and PORT.
    """

    def __init__(self, app=None):
        """Initialize the MySQL request extension for the Flask app ``app``.

        :param app: Flask application (optional)
        """
        self.app = app
        if self.app is not None:
            self.app = app
            self.app.config.setdefault('MYSQL_DATABASE_UNIX_SOCKET', '/var/run/mysqld/mysqld.sock')
            self.app.config.setdefault('MYSQL_DATABASE_HOST', None)
            self.app.config.setdefault('MYSQL_DATABASE_PORT', 3306)
            self.app.config.setdefault('MYSQL_DATABASE_USER', None)
            self.app.config.setdefault('MYSQL_DATABASE_PASSWORD', None)
            self.app.config.setdefault('MYSQL_DATABASE_DB', None)
            self.app.config.setdefault('MYSQL_DATABASE_CHARSET', 'utf8')
            self.app.teardown_request(self.teardown_request)
            self.app.before_request(self.before_request)

    def connect(self):
        """Connect to the MySQL database specified in the Flask application's
        configuration file.

        :return: MySQL database connector.
        """
        kwargs = {}
        if self.app.config['MYSQL_DATABASE_UNIX_SOCKET']:
            kwargs['unix_socket'] = self.app.config['MYSQL_DATABASE_UNIX_SOCKET']
        else:
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
        return mysql.connector.connect(**kwargs)    # pylint:disable=star-args

    def before_request(self):
        """Connect to the database before handling the request.
        """
        ctx = _request_ctx_stack.top
        ctx.database = self.connect()

    # pylint:disable=unused-argument,no-self-use
    def teardown_request(self, exception):
        """After handling the request, close the database connection.
        """
        ctx = _request_ctx_stack.top
        if hasattr(ctx, "cursor"):
            ctx.cursor.close()
        if hasattr(ctx, "database"):
            ctx.database.close()
    # pylint:enable=unused-argument,no-self-use

    @property
    def database(self):  # pylint:disable=no-self-use
        """Ugly, but convenient access to the existing database connection.

        :return: MySQL database connector.
        """
        ctx = _request_ctx_stack.top
        if ctx is not None:
            return ctx.database

    def cursor(self, dictionary=True, **kwargs):  # pylint:disable=no-self-use
        """Create and return a cursor for the current database connection.

        :param bool dictionary: flag if the cursor should return rows as
                                dictionaries (optional, True by default).
        :param **kwargs: optional keyword arguments that are passed to the
                         cursor initalization function.
        :return: database cursor :)
        """
        ctx = _request_ctx_stack.top
        if ctx is not None:
            return ctx.database.cursor(dictionary=dictionary, **kwargs)
