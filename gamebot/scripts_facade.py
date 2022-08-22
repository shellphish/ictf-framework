#!/usr/bin/env python
__author__ = 'machiry'

"""Interface or Facade for computing scripts to run. This hides the internal
details of fetching the scripts, number of scripts to run etc and exposes a
standard interface which can be used to fetch/update scripts to run for each tick.
"""
from collections import defaultdict
from datetime import datetime
import coloredlogs
import itertools
import json
import logging
import logstash
import pika
import random
import time

from utils import flatten_list
from settings import LOGSTASH_IP, LOGSTASH_PORT
import settings


class ScriptsFacade:

    LOG_FMT = '%(levelname)s - %(asctime)s (%(name)s): %(msg)s'

    def __init__(self, db_api, log_level=logging.INFO):

        self.db_api = db_api

        # Set up logging
        log = logging.getLogger('gamebot_scripts')
        log.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))
        log.setLevel(log_level)
        log_formatter = coloredlogs.ColoredFormatter(ScriptsFacade.LOG_FMT)
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(log_formatter)
        log.addHandler(log_handler)
        self.log = log

        # Test connection to RabbitMQ server
        host        = settings.RABBIT_ENDPOINT
        username    = settings.RABBIT_USERNAME
        password    = settings.RABBIT_PASSWORD
        credentials = pika.PlainCredentials(username, password)
        self.conn_params = pika.ConnectionParameters(host=host, credentials=credentials)
        while True:
            try:
                connection = pika.BlockingConnection(self.conn_params)
                log.info("Connection to RabbitMQ dispatcher verified")
                break
            except pika.exceptions.AMQPConnectionError as ex:
                log.info("The RabbitMQ server is not ready yet...")
                time.sleep(5)
                continue
        connection.close()


    def load_script_meta(self):
        services, scripts = {}, {}
        state = self.db_api.get_full_game_state()

        # Get data out of the dict
        for service in state['services']:
            services[int(service['service_id'])] = service

        for script in state['scripts']:
            d = dict(script)
            d['service_name'] = services[d['service_id']]['service_name']
            scripts[int(script['script_id'])] = d

        return scripts, services


    def publish_tasks(self, tick_id):

        # Get meta-information on all the scripts
        scripts, services = self.load_script_meta()

        # Get a list of all scripts to run in the current tick
        run_scripts = self.db_api.get_scripts_to_run(tick_id)
        self.log.info("Got {} script execution requests".format(len(run_scripts)))

        teams_scripts = {}
        for run_script in run_scripts:
            execution_id   = run_script['id']
            script_id      = run_script['script_id']
            target_team_id = run_script['against_team_id']
            script_meta    = scripts[script_id]
            service_id     = script_meta['service_id']

            if target_team_id not in teams_scripts:
                teams_scripts[target_team_id] = defaultdict(list)

            teams_scripts[target_team_id][service_id].append(
                {
                    'execution_id' : execution_id,
                    'script_id'    : script_id,
                    'script_type'  : script_meta['type'],
                    'script_name'  : script_meta['script_name'],
                }
            )

        # Push work into scripts_queue in equal size chunks
        chunks = settings.SCRIPTBOT_INSTANCES
        chunkdict = {}
        chunksize = len(teams_scripts) // chunks
        items = iter(teams_scripts.items())
        list_of_chunks = [dict(itertools.islice(items, chunksize)) for _ in range(chunks-1)]
        list_of_chunks.append(dict(items))

        # Create metadict with copy of "services" dict and tick_id
        task_list = []
        for scripts_to_run in list_of_chunks:
            task = {
                'teams'    : scripts_to_run,
                'services' : services,
                'tick_id'  : tick_id,
            }
            task_list.append(json.dumps(task))

        # Create channel and publish tasks
        # Durability ensures messages are not lost if dispatcher is rebooted
        connection = pika.BlockingConnection(self.conn_params)
        channel = connection.channel()
        channel.queue_declare(queue='scripts_queue', durable=True)
        for task in task_list:
            channel.basic_publish(
                exchange='',
                routing_key='scripts_queue',
                body=task,
                properties=pika.BasicProperties(
                    delivery_mode = 2, # make message persistent
                )
            )
            connection.process_data_events()
        channel.close()
        connection.close()


    def update_scripts_to_run(self, tick_id, num_benign, num_exploit, num_get_flags):
        """
        Updated the database with scripts to run for the current tick.
        NOTE: This method is not idempotent, calling this multiple times
        will change the database in non-pleasent way.
        :param tick_id: Tick id for which the scripts need to be scheduled.
        :param num_benign: Number of benign scripts to run for each service/team.
        :param num_exploit: Number of exploit scripts to run for each service/team.
        :param num_get_flags: Number of get flag scripts to run for each service/team.
        :return: True if all is well else False
        """
        # Profiling, get old time
        old_time = datetime.now()
        working_scripts_json = self.db_api.get_working_scripts()

        non_exploit_types = ["getflag", "setflag", "benign"]

        # Create an easy accessible structure for later access
        # dictionary containing for for each service, for each type,
        # a list of script ids that needs to be run
        # Dictionary for non exploit scripts
        non_exploit_scripts = {}
        # For exploit scripts, this also contain team id.
        exploit_scripts = {}
        # Exploit scripts from admin
        admin_exploits = {}
        # Set of all teams
        all_teams = set(self.db_api.get_all_team_ids())
        # Set of all services for which we have at least one script.
        all_services = set()

        for curr_script_json in working_scripts_json:
            # Get the data from all the fields.
            script_id = curr_script_json["id"]
            script_type = curr_script_json["type"]
            team_id = curr_script_json["team_id"]
            service_id = curr_script_json["service_id"]
            # Update services
            all_services.add(service_id)
            # initialize all get/set/benign flags
            if service_id not in non_exploit_scripts:
                non_exploit_scripts[service_id] = {"getflag": [], "setflag": [], "benign": []}
            if script_type in non_exploit_types:
                # Non-exploit scripts, we do not care about team.
                non_exploit_scripts[service_id][script_type].append(script_id)
            else:
                if team_id is not None:
                    # Exploit submitted from a team.
                    # We should not run this against same team
                    if team_id not in exploit_scripts:
                        exploit_scripts[team_id] = {}
                    if service_id not in exploit_scripts[team_id]:
                        exploit_scripts[team_id][service_id] = {"exploit": []}
                    exploit_scripts[team_id][service_id][script_type].append(script_id)
                else:
                    # Exploits by admin
                    if service_id not in admin_exploits:
                        admin_exploits[service_id] = {"exploit": []}
                    admin_exploits[service_id][script_type].append(script_id)

        self.log.debug("Time to get data and re-arrange scripts information:" + str(datetime.now() - old_time))

        old_time = datetime.now()
        backup_old_time = datetime.now()
        for curr_team in all_teams:
            curr_total_scripts = []
            set_flag_scripts = []
            get_flag_scripts = []
            benign_scripts = []
            curr_exploit_scripts = []
            for curr_service in all_services:
                curr_service_exploit_script = []
                # Non-exploit scripts for each service.
                if "setflag" in non_exploit_scripts[curr_service]:
                    set_flag_scripts.extend(non_exploit_scripts[curr_service]["setflag"])
                if "getflag" in non_exploit_scripts[curr_service]:
                    # Random choice, its ok to be duplicates.
                    get_flag_scripts.extend(list(random.choice(non_exploit_scripts[curr_service]["getflag"])
                                            for _ in range(num_get_flags)))
                if "benign" in non_exploit_scripts[curr_service] and \
                        len(non_exploit_scripts[curr_service]["benign"]) > 0:
                    # Random choice, its ok to be duplicates.
                    benign_scripts.extend(list(random.choice(non_exploit_scripts[curr_service]["benign"])
                                          for _ in range(num_benign)))
                # Get all exploit scripts for this service, not submitted from current team
                curr_service_exploit_script.extend(value[curr_service]["exploit"] for key, value in exploit_scripts.items()
                                                   if key != curr_team and (curr_service in value))
                # Flatten the list
                curr_service_exploit_script = flatten_list(curr_service_exploit_script)
                # if there are admin exploits for the current service, get them too.
                if curr_service in admin_exploits:
                    curr_service_exploit_script.extend(admin_exploits[curr_service]["exploit"])

                # Random sample exploit scripts to avoid duplicates.
                curr_team_exploit_scripts = []
                curr_team_exploit_scripts.extend(random.sample(curr_service_exploit_script,
                                                               min(len(curr_service_exploit_script), num_exploit)))
                curr_exploit_scripts.extend(curr_team_exploit_scripts)

            # shuffle the scripts ids to make it unpredictable.
            others = get_flag_scripts + benign_scripts + curr_exploit_scripts
            random.shuffle(others)
            random.shuffle(set_flag_scripts)
            # update the common dictionary.
            # Note that, we should have set flag scripts at beginning, we should set flag before running
            # other scripts.
            curr_total_scripts = list(set_flag_scripts + others)
            # Add these to the list of scripts to be run against the team.
            self.db_api.update_scripts_to_run(curr_team, tick_id, curr_total_scripts)

        self.log.debug("Upload time to DB for each team/service's scripts:" + str(datetime.now() - old_time))

        # Insert tasks into queue for dispatcher to disperse
        self.publish_tasks(tick_id)
        self.log.info("Time to update all teams with scripts to run:" + str(datetime.now() - backup_old_time))
        return True


    def update_state_of_services(self, tick_id):
        """
        Updates state of all services across all teams for the corresponding tick.
        :param tick_id: Tick id for which state needs to be updated.
        :return: True -> success else False
        """

        # Profiling, get old time
        old_time = datetime.now()

        # Reason to update state of service
        default_reason = "gamebot updated the state from results of scripts run"

        # Set of all teams
        all_teams = set(self.db_api.get_all_team_ids())

        # Set of all service ids
        all_services = set(self.db_api.get_all_service_ids())

        # Get scripts run stats
        scripts_run_stats = self.db_api.get_scripts_run_stats(tick_id)

        self.log.info("Time to get all scripts run stats:" + str(datetime.now() - old_time))
        # Get the state of all the services to be updated in a bulk format.
        old_time = datetime.now()
        team_service_states = {}
        for curr_team in all_teams:
            team_service_states[curr_team] = {}
            for curr_service in all_services:
                # by default service state is down
                service_state = "down"
                updating_reason = default_reason
                if (curr_team in scripts_run_stats) and (curr_service in scripts_run_stats[curr_team]):
                    print(scripts_run_stats[curr_team][curr_service])
                    success = int(scripts_run_stats[curr_team][curr_service][0])
                    scheduled = int(scripts_run_stats[curr_team][curr_service][1])
                    not_ran = int(scripts_run_stats[curr_team][curr_service][2])
                    failed = scheduled - (success + not_ran)
                    updating_reason += ", success=" + str(success) + ", scheduled=" + str(scheduled) + \
                                       ", failed to run=" + str(not_ran)
                    # If there is at least one successful and no failed script then the service is considered up.
                    if (success > 0) and (failed == 0):
                        service_state = "up"
                    else:
                        self.log.debug("Service down:" + curr_team + ", service:" + str(curr_service))
                    if not_ran > 0:
                        self.log.warning("SCRIPT BOT TOO SLOW," + str(not_ran) +
                                         "/" + str(scheduled) +
                                         " SCRIPTS NOT RAN FOR TEAM:" + str(curr_team) + ", FOR SERVICE:" +
                                         str(curr_service))

                else:
                    service_state = "notfunctional"
                    updating_reason += ", no scripts ran for this service"
                    self.log.info("No scripts ran for:" + curr_team + ", service:" + curr_service)

                team_service_states[curr_team][curr_service] = (tick_id, service_state, updating_reason)

        # update the state of all the services and all the teams
        self.db_api.bulk_update_team_service_state(team_service_states)

        self.log.info("Time to set states of all services across all teams:" + str(datetime.now() - old_time))

        return True
