#!/bin/sh

# Create Rabbitmq user and delete default Guest user
( rabbitmqctl wait --timeout 60 $RABBITMQ_PID_FILE ; \
rabbitmqctl add_user $RABBIT_USERNAME $RABBIT_PASSWORD 2>/dev/null ; \
rabbitmqctl set_user_tags $RABBIT_USERNAME administrator ; \
rabbitmqctl set_permissions -p / $RABBIT_USERNAME  ".*" ".*" ".*" ; \
rabbitmqctl delete_user guest ; \
echo "*** User '$RABBIT_USERNAME' with password '$RABBIT_PASSWORD' completed. ***" ; \
echo "*** User guest deleted. ***" ; \
echo "*** Log into the WebUI at port 15672 (example: http://localhost:15672) ***") &

# $@ is used to pass arguments to the rabbitmq-server command.
# For example if you use it like this: docker run -d rabbitmq arg1 arg2,
# it will be as you run in the container rabbitmq-server arg1 arg2
rabbitmq-server $@
