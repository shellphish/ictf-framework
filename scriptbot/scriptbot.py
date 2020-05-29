#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A scriptbot instance receives tasks and executes the scripts inside them
to verify that teams' services are up and running.

Scriptbot pulls the scripts to run dynamically from a Docker Registry,
while the tasks themselves are received from a RabbitMQ dispatcher.
"""

__authors__ = "Sid Senthilkumar"
__version__ = "1.0.0"

from db_client import DBClient, DBClientError
from registry_client import RegistryClient, RegistryClientPullError
from script_executor import ScriptThread
from settings import LOGSTASH_IP, LOGSTASH_PORT
import settings

import datetime
import functools
import json
import logging
import logstash
import os
import pika
import random
import resource
import threading
import time
import traceback

class Scheduler(object):

    def __init__(self):

        # Clients
        self.db = DBClient()
        self.registry = RegistryClient()

        # All setflag locks in the current tick
        self.setflag_locks = []

        # A lock that guards self.setflag_locks
        self.setflag_locks_list_lock = threading.Lock()

        # Logs
        self.log = logging.getLogger('scriptbot.scheduler')
        self.log.setLevel(settings.LOG_LEVEL)
        self.log.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))
        self.log.info('#' * 80)
        self.log.info("Initialization")
        self.log.info('#' * 80)


    def add_setflag_lock(self, lock):
        if lock is None:
            return

        self.setflag_locks_list_lock.acquire()
        self.setflag_locks.append(lock)
        self.setflag_locks_list_lock.release()


    def release_all_setflag_locks(self):
        self.setflag_locks_list_lock.acquire()

        for lock in self.setflag_locks:
            try: lock.release()
            except threading.ThreadError: pass

        self.setflag_locks = [] # clears the list
        self.setflag_locks_list_lock.release()


    def get_random_delay(self):
        """
        Adds a random delay between the execution of scripts
        TODO: Experiment with this to make the scripts execute
              at evenly distributed times across the interval.
        """
        return random.randint(0, 5)


    def run_team(self, team_id):
        team_meta = self.teams[team_id]
        thread_list = []

        for service_id in team_meta:

            # Create a lock for setflag and getflag and save it so we can
            # release all locks when new tick script request comes in
            setflag_lock = threading.Lock()
            setflag_lock.acquire()
            self.add_setflag_lock(setflag_lock)

            # Execute each script in new thread
            for script in team_meta[service_id]:
                script_type = script['script_type']
                self.log.info('Executing script for team {}'.format(team_id))

                st = ScriptThread(
                    team_id=int(team_id),
                    execution_id=int(script['execution_id']),
                    script_id=int(script['script_id']),
                    service_id=int(service_id),
                    service_name=self.services[str(service_id)]['service_name'],
                    script_image_path=self.services[str(service_id)]['docker_image_path'],
                    script_type=script_type,
                    script_name=script['script_name'],
                    ip="team%d" % int(team_id),
                    port=self.services[str(service_id)]['port'],
                    db_client=self.db,
                    tick_id=self.tick_id,
                    delay=self.get_random_delay(),
                    setflag_lock=(setflag_lock if script_type in ('setflag', 'getflag') else None),
                )

                st.start()
                thread_list.append(st)

        return thread_list


    def schedule_scripts(self):
        self.log.info('Scheduling scripts for tick')

        all_threads = []
        for team_id in self.teams:
            try:
                new_threads = self.run_team(team_id)
                all_threads.extend(new_threads)
            except Exception as ex:
                msg = 'An unexpected exception occurred when launching scripts: %s\n%s' % (
                    str(ex),
                    str(traceback.format_exc())
                )
                self.log.error(msg)

        # Wait for all threads to complete
        for thread in all_threads:
            thread.join()


    def update_scripts(self, service_id):
        try:
            image_name = self.services[service_id]['docker_image_name']
            image_path = self.services[service_id]['docker_image_path']
            self.registry.pull_new_image(image_name, image_path)
        except RegistryClientPullError as ex:
            msg = "An unexpected exception occurred when pulling from registry"
            msg += " and updating service %s (image %s): %s\n%s" % (
                service_id,
                image_name,
                str(ex),
                str(traceback.format_exc())
            )
            self.log.error(msg)

        except Exception as ex:
            msg = "An unexpected exception occurred when updating service"
            msg += " %s: %s\n%s" % (
                service_id,
                str(ex),
                str(traceback.format_exc())
            )
            self.log.error(msg)


    def parse_scripts(self, body):

        try:
            # Parse JSON body
            all_data      = json.loads(body)
            self.teams    = all_data['teams']
            self.services = all_data['services']
            self.tick_id  = all_data['tick_id']

            # Generate Docker image names/paths for each service
            for service_id in self.services:

                # Insert image name
                service_name = self.services[service_id]['service_name']
                image_name = '{}_scripts'.format(service_name)
                self.services[service_id]['docker_image_name'] = image_name

                # Insert image path
                if settings.IS_LOCAL_REGISTRY:
                    path = image_name
                else:
                    path = '{}/{}'.format(self.registry.registry_endpoint, image_name)
                self.services[service_id]['docker_image_path'] = path

        except Exception as ex:
            msg = "An unexpected exception occurred while parsing scripts"
            msg += ": %s\n%s" % (
                str(ex),
                str(traceback.format_exc())
            )

            self.log.error(msg)


    def scheduler_callback(self, channel, body, delivery_tag, connection):
        try:
            body = body.decode('ascii')

            # A service's setflag must execute before it's getflag
            # We use locks to prevent getflag from running first

            # Release all past setflag locks
            self.release_all_setflag_locks()

            # Parse script information to execute
            self.parse_scripts(body)

            # Get most recent versions of scripts from Docker Registry
            # (in case the scripts had bugs and needed to be changed)
            for service_id in self.services:
                self.update_scripts(service_id)

            # Execute scripts
            st = time.time()
            self.schedule_scripts()
            lt = time.time()
            self.log.info('Scripts Finished. Time:%f' % (lt - st))

        except Exception as ex:
            msg = "An unexpected exception occurred in scheduler thread:"
            msg += " %s\n%s" % (
                str(ex),
                str(traceback.format_exc())
            )
            self.log.error(msg)

        def ack_message(channel, delivery_tag):
            channel.basic_ack(delivery_tag=delivery_tag)
            self.log.info("Completed script tasks")

        cb = functools.partial(ack_message, channel, delivery_tag)
        connection.add_callback_threadsafe(cb)


    def receive_tasks(self):

        self.log.info('Connecting to RabbitMQ dispatcher')
        host        = settings.RABBIT_ENDPOINT
        username    = settings.RABBIT_USERNAME
        password    = settings.RABBIT_PASSWORD
        credentials = pika.PlainCredentials(username, password)
        conn_params = pika.ConnectionParameters(host=host, credentials=credentials)
        while True:
            try:
                connection = pika.BlockingConnection(conn_params)
                self.log.info('Connected to RabbitMQ. Waiting for tasks')
                break
            except pika.exceptions.AMQPConnectionError as ex:
                self.log.info('The RabbitMQ dispatcher is not ready yet...')
                time.sleep(5)
                continue

        # Define callback
        def callback(channel, method, properties, body, args):
            self.log.info("Received script tasks")
            connection = args[0]

            # Execute received tasks in new thread.
            # Otherwise, scriptbot will disconnect from the dispatcher
            # because it's not replying to RabbitMQ's heartbeats.
            thread = threading.Thread(
                target=self.scheduler_callback,
                args=(channel, body, method.delivery_tag, connection)
            )

            # If the child threads cause scriptbot to die, the main thread should die too
            thread.setDaemon(True)
            thread.start()

        try:
            # Ensure fair task scheduling between scriptbot instances
            # Receive 1 message at a time from dispatcher
            channel = connection.channel()
            channel.basic_qos(prefetch_count=1)

            # Declare which queue to receive messages from
            # Durability ensures messages are not lost if dispatcher is rebooted
            on_message_callback = functools.partial(callback, args=(connection,))
            channel.queue_declare(queue='scripts_queue', durable=True)
            channel.basic_consume(queue='scripts_queue', on_message_callback=on_message_callback)
            channel.start_consuming()
        except Exception as e:
            self.log.error("Scriptbot Died!")
            channel.close()
            connection.close()


def main():

    # Adjust open file limit
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    if soft < 65536 or hard < 65536:
        l = logging.getLogger('main')
        l.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))
        l.warning(
            'Open file limits (soft %d, hard %d) are too low. 65536 recommended. '
            'Will increase soft limit. '
            'You might want to adjust hard limit as well.',
            soft,
            hard
        )
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))
        except ValueError:
            l.error('Failed to adjust open file limits. Please adjust them manually.')

    # Retrieve and execute jobs
    s = Scheduler()
    s.receive_tasks()

if __name__ == "__main__":
    main()
