#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""These are the default settings for the central database API server.

You should not edit this file. You should edit /ictf/settings.py instead.
"""

# General
DEBUG = True
LISTEN = "0.0.0.0"
API_SECRET = "lol"

# MySQL
MYSQL_DATABASE_USER = "ictf"
MYSQL_DATABASE_PASSWORD = ""
MYSQL_DATABASE_DB = "ictf"
MYSQL_DATABASE_UNIX_SOCKET = "/var/run/mysqld/mysqld.sock"

# Flag Generation
FLAG_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
FLAG_LENGTH = 13
FLAG_PREFIX = "FLG"
FLAG_SUFFIX = ""

# Submitting Flags
MAX_INCORRECT_FLAGS_PER_TICK = 1000
NUMBER_OF_TICKS_FLAG_VALID = 3
ATTACKUP_HEAD_BUCKET_SIZE = 10  # The top N teams can freely attack each other

# Database API
USER_PASSWORD_SALT = "YOU SHOULD OVERWRITE THIS"
