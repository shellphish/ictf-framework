FROM rabbitmq:management

ENV RABBITMQ_PID_FILE /var/lib/rabbitmq/mnesia/rabbitmq

COPY ./dispatcher /opt/ictf/dispatcher

WORKDIR /opt/ictf/dispatcher

RUN chmod +x ./start.sh

ENTRYPOINT ./start.sh
