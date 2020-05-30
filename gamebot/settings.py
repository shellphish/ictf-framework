import os

# Logstash settings
LOGSTASH_PORT = 1717
LOGSTASH_IP = "localhost"

# DB settings
DB_HOST = 'THE_API_ADDRESS_GOES_HERE'
DB_SECRET = 'THESECRETPASSPHRASEGOESHERE'

# RabbitMQ settings
RABBIT_USERNAME = os.environ['RABBIT_USERNAME']
RABBIT_PASSWORD = os.environ['RABBIT_PASSWORD']
RABBIT_ENDPOINT = os.environ['RABBIT_ENDPOINT']

# For scriptbot task division
SCRIPTBOT_INSTANCES = int(os.environ['NUM_SCRIPTBOTS'])
