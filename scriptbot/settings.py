import os
import logging

VERBOSE = False
DEBUG   = False

# Log settings
LOG_LEVEL = logging.INFO if not VERBOSE else logging.DEBUG
LOG_PATH = '/var/log/scriptbot/scheduler.log'
STATUS_PATH = '/var/log/scriptbot/scheduler.status.json'
LOGSTASH_IP = "localhost"
LOGSTASH_PORT = 1717

# Registry settings
REGISTRY_USERNAME = os.environ['REGISTRY_USERNAME']
REGISTRY_PASSWORD = os.environ['REGISTRY_PASSWORD']
REGISTRY_ENDPOINT = os.environ['REGISTRY_ENDPOINT']
IS_LOCAL_REGISTRY = int(os.environ['IS_LOCAL_REGISTRY']) == 1

# RabbitMQ settings
RABBIT_USERNAME = os.environ['RABBIT_USERNAME']
RABBIT_PASSWORD = os.environ['RABBIT_PASSWORD']
RABBIT_ENDPOINT = os.environ['RABBIT_ENDPOINT']

# DB settings
DB_HOST = "database.ictf"
DB_SECRET = os.environ['API_SECRET']
DATABASE_REQUEST_RETRIES        = 2 # Retry at most 2 times if we get a HTTP 502 back
DATABASE_REQUEST_RETRY_INTERVAL = 1 # Sleep 1 second before each retry
MAX_SCRIPT_OUTPUT_BYTES = 1000      # how much output to send to DB

# Scheduler settings
SCRIPT_TIMEOUT_SOFT = 60 # 1 minute, roughly 1/3 of the length of a tick
SCRIPT_TIMEOUT_HARD = SCRIPT_TIMEOUT_SOFT + 10 # give the script 10 seconds to die and traceback

# Let's mark the scriptbot with an ID so we can tag it in logstash
BOT_ID = os.environ['SCRIPTBOT_ID']
