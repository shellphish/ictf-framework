#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The scriptbot is responsible for checking the service status of all teams. It
updates flags on vulnerable services, and checks that these flags are
accessible. Each service has at least one setflag, one getflag, and one benign
script. The setflag and getflag scripts are used to check the status of the
service by setting and getting the flags, while the benign script is used to
create some benign traffic. Scriptbot pulls these scripts and corresponding
execution intervals from the database.
"""

__authors__ = "Dhilung Kirat and Fish Wang"
__version__ = "0.1.1"

import os
import sys
import shutil
import time
import datetime
import random
import subprocess
import json
import argparse
import logging
import copy
import hashlib
import docker
import traceback
import threading
import resource
import logstash
from collections import defaultdict

import requests
import nose.tools

import settings

ERROR_SCRIPT_EXECUTION = (0x100, "Script execution failed.")
ERROR_WRONG_FLAG = (0x100, "Incorrect flag.")
ERROR_MISSING_FLAG = (0x101, "Missing 'FLAG' field.")
ERROR_DB = (0x102, "DB error.")
ERROR_SCRIPT_KILLED = (0x103, "Script was killed by the scheduler.")

LOGSTASH_PORT = 1717
LOGSTASH_IP = "localhost"

verbose = False
DEBUG = False


#
# Custom exceptions
#

class DBClientError(Exception):
    pass

class RegistryClientPullError(Exception):
    pass

class DBClientQueryError(DBClientError):
    def __init__(self, message, status_code):
        DBClientError.__init__(self, message)

        self.status_code = status_code

class SchedulerError(Exception):
    pass

class ScriptExecError(Exception):
    pass


class RegistryClient:
    def __init__(self, 
        registry_username=settings.REGISTRY_USERNAME, 
        registry_password=settings.REGISTRY_PASSWORD, 
        registry_endpoint=settings.REGISTRY_ENDPOINT):

        self.registry_username = registry_username
        # FIXME: The login token will expire! we need to refresh it if we want a game that
        #        last more than 8 hours
        self.registry_password = registry_password 
        self.registry_endpoint = registry_endpoint
        self.docker_client = docker.from_env()
        self.log = logging.getLogger('scriptbot.registryClient')
        self.log.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))
        if not settings.IS_LOCAL_REGISTRY:
            self._authenticate()

    def _authenticate(self):
        self.docker_client.login(
            username=self.registry_username,
            password=self.registry_password,
            registry="https://{}".format(self.registry_endpoint)
        )

    def pull_new_image(self, image_name):
        try:
            if not settings.IS_LOCAL_REGISTRY:
                path = '{}/{}'.format(self.registry_endpoint, image_name)
                self.log.info("Pulling new image {} from {}...".format(image_name, path))
                res = self.docker_client.images.pull(path)
                self.log.info("Pulled image {}: {}".format(image_name, res))
            else:
                path = image_name
                self.log.info("The framework is running locally... there is no need to pull the image {}".format(image_name))

        except docker.errors.APIError as ex:
            raise RegistryClientPullError("Error during pull of {}: {}".format(image_name, ex))


class DBClient:
    def __init__(self, host=settings.DB_HOST, pwd=settings.DB_SECRET):
        self.host = host
        self.pwd = pwd
        self.log = logging.getLogger('scriptbot.dbclient')
        self.log.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))


    def _query(self, api, authentication=True):
        """
        Make a query to the database backend

        :param api: The API string
        :param authentication: Should we pass secret or not
        :return: The result dict
        """

        # pre-process the API
        if api.startswith('/'):
            api = api[1 : ]

        url = 'http://{}/{}'.format(self.host, api)
        params = {'secret': self.pwd} if authentication else None

        retry_times = settings.DATABASE_REQUEST_RETRIES

        while retry_times >= 0:
            try:
                r = requests.get(url, timeout=5, params=params)

            except requests.exceptions.Timeout:
                raise DBClientQueryError(
                    "Database request [GET]'%s' timed out" % (api),
                    0
                )

            except requests.exceptions.RequestException as ex:
                raise DBClientQueryError(
                    "Database request [GET]'%s' failed due to exception %s" % (api, str(ex)),
                    0
                )

            if r.status_code == 200:
                return json.loads(r.content.decode('utf-8'))

            elif r.status_code == 502 and retry_times > 0:
                # Retry in case of HTTP 502

                self.log.error(
                    "Database request [GET]'%s' failed with HTTP 502. Will retry after %s seconds",
                    api,
                    settings.DATABASE_REQUEST_RETRY_INTERVAL,
                )

                retry_times -= 1

                # back off and pause a while
                time.sleep(settings.DATABASE_REQUEST_RETRY_INTERVAL)

                # retry...
                continue

            else:
                # HTTP request failed?
                raise DBClientQueryError(
                    "Database request [GET]'%s' returns an unexpected HTTP status code %d" % (api, r.status_code),
                    r.status_code
                )

    def _post(self, api, data, authentication=True):
        """
        Make aaa post to the database backend

        :param api: The API string
        :param data: The data to post to the remote server
        :param authentication: Should we pass secret or not
        :return: The result dict, or None if nothing is returned
        """

        # pre-process the API
        if api.startswith('/'):
            api = api[1 : ]

        url = 'http://{}/{}'.format(self.host, api)
        params = {'secret': self.pwd} if authentication else None

        retry_times = settings.DATABASE_REQUEST_RETRIES

        while retry_times >= 0:
            try:
                r = requests.post(url, data=data, timeout=5, params=params)

            except requests.exceptions.Timeout:
                raise DBClientQueryError(
                    "Database request [POST]'%s'(data: %s) timed out" % (api, data),
                    0
                )

            except requests.exceptions.RequestException as ex:
                raise DBClientQueryError(
                    "Database request [POST]'%s'(data: %s) failed due to exception %s" % (api, data, str(ex)),
                    0
                )

            if r.status_code == 200:
                return json.loads(r.content.decode('utf-8'))

            elif r.status_code == 502 and retry_times > 0:
                # Retry in case of HTTP 502

                self.log.error(
                    "Database request [POST]'%s'(data: %s) failed with HTTP 502. Will retry after %s seconds",
                    api,
                    data,
                    settings.DATABASE_REQUEST_RETRY_INTERVAL,
                )

                retry_times -= 1

                # back off and pause a while
                time.sleep(settings.DATABASE_REQUEST_RETRY_INTERVAL)

                # retry...
                continue

            else:
                # HTTP request failed?
                raise DBClientQueryError(
                    "Database request [POST]'%s'(data: %s) returns an unexpected HTTP status code %d" % (
                        api,
                        data,
                        r.status_code
                    ),
                    r.status_code
                )

    def get_game_state(self):
        """
        Get the game state

        API: /game/state

        :return: A huge dict that contains almost everything
        """

        state = self._query("/game/state")

        # Some basic sanity checks
        # Removing these sanity checks, because they are not true when the game is not running
        return state

    def get_teams(self, validated=None):
        """
        Get a dict of all teams from the database backend

        API: /teams/info

        :return: a dict of all team info
        """

        team_info = self._query("/teams/info")

        teams = team_info['teams']

        # Convert all team IDs to integers
        converted = {}
        for team_id, val in teams.items():
            converted[int(team_id)] = val

        return converted

    def generate_flag(self, team_id, service_id):
        """
        Generate a flag for a specific team and service, which will be used by setflag script

        API: /flag/latest/team/<int:team_id>/service/<int:service_id>
        Note that this API is a POST

        :param team_id: ID of the team
        :param service_id: ID of the specific service
        :return: A tuple of (flag_idx, flag), where flag_idx is the ID of the flag in database
        """

        flag_info = self._post("/flag/generate/service/%d/team/%d" % (service_id, team_id), {})

        if not flag_info:
            return None

        else:
            if "flag" not in flag_info:
                raise DBClientError('Expecting non-existent key "flag" in the result dict')

            if "id" not in flag_info:
                raise DBClientError('Expecting non-existent key "id" in the result dict')

            return int(flag_info['id']), flag_info['flag']

    def get_current_flag(self, team_id, service_id):
        """
        Get the latest flag for a specific team and service.

        API: /flag/latest/team/<int:team_id>/service/<int:service_id>

        :param team_id: ID of the team
        :param service_id: ID of the specific service
        :return: A tuple of (flag, flag_id, secret_token) if we have a flag, (None, None, None) otherwise
        """

        flag_info = self._query("/flag/latest/team/%d/service/%d" % (team_id, service_id))

        if not flag_info:
            return None, None, None

        else:
            if "flag" not in flag_info:
                raise DBClientError('Expecting non-existent key "flag" in the result dict')

            if "flag_id" not in flag_info:
                raise DBClientError('Expecting non-existent key "flag_id" in the result dict')

            if "cookie" not in flag_info:
                raise DBClientError('Expecting non-existent key "cookie" in the result dict')

            return flag_info['flag'], flag_info['flag_id'], flag_info['cookie']

    def set_secret_token(self, flag_idx, flag_id, secret_token):
        """
        Set flag_id and secret_token to a specific flag identified by flag_idx

        API: /flag/set/<int:flag_idx>

        :param flag_idx: The ID of the flag in database.
        :param flag_id: The flag ID
        :param secret_token: The secret_token
        :return: True if successfully updated, False otherwise
        """

        data = {
            'flag_id': flag_id,
            'cookie': secret_token,
        }

        r = self._post("/flag/set/%d" % flag_idx, data)

        if "result" not in r:
            raise DBClientError('Expecting non-existent key "result" in the result dict')

        if r["result"] == 'success':
            return True

        return False

    def push_result(self, execution_id, result, script_output=None):
        """
        Push the result of an executed script to the server

        API: /script/ran/<int:execution_id>

        :param execution_id: ID of the run of the script, as in database
        :param result: Result to push
        :param script_output: Output of the script
        :return: True/False
        """

        if script_output is None:
            script_output = ""

        data = {
            'output': script_output,
            'error': result['error'],
            'error_message': result.get('error_msg', None),
        }

        r = self._post("/script/ran/%d" % execution_id, data)

        if 'result' not in r:
            raise DBClientError('Expecting non-existent key "result" in the result dict')

        if r['result'] == 'success':
            return True

        return False

    def get_scripts_to_run(self):
        """
        Get a list of all scripts to run in the current tick.

        API: /scripts/get/torun

        :return: a list of script execution records
        """

        r = self._query("/scripts/get/torun")

        if not isinstance(r, dict):
            raise DBClientError('Expecting a dict as result, getting %s instead' % type(r))

        if "scripts_to_run" not in r:
            raise DBClientError('Expecting non-existent key "scripts_to_run" in the result dict')

        return r['scripts_to_run']

class ScriptExecution(object):
    """
    ScriptExecution describes a specific run of a script against a certain team in some tick
    """
    def __init__(self, idx, script_id, target_team_id):
        """
        Constructor

        :param idx: ID of the execution, as in database
        :param script_id: ID of the script
        :param target_team_id: ID of the target team
        :return: None
        """

        self.idx = idx
        self.script_id = script_id
        self.target_team_id = target_team_id

class ScriptExecutor(threading.Thread):

    def __init__(self, state_id, team_id, execution_id, script_id, service_id, service_name, script_image_path,
                 script_type, script_name, ip, port, delay=0, setflag_lock=None, db_client=None):
        threading.Thread.__init__(self)

        self.state_id = state_id
        self.delay = delay
        self.result = {'error': 0, 'error_msg': 'Init'}
        self.setflag_lock = setflag_lock

        self.execution_id = execution_id
        self.team_id = int(team_id)
        self.script_id = int(script_id)
        self.service_id = int(service_id)
        self.service_name = service_name
        self.script_image_path = script_image_path
        self.script_type = script_type
        self.script_name = script_name
        self.ip = ip
        self.port = int(port)
        self.log = logging.getLogger('scriptbot.script_exec')
        self.log.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))

        self.db = DBClient() if db_client is None else db_client
        self.stop = False
        self.flag_meta = {}
        self.max_output_send_bytes = settings.MAX_SCRIPT_OUTPUT_BYTES

        global verbose
        if verbose:
            self.log.setLevel(logging.DEBUG)

        self.log.info('ScriptExec Init')

    def update_current_flag(self):
        """
        Update the current flag from database.

        :return: True/False
        """

        self.log.info('Getting current flag info for service %d', self.service_id)

        flag, flag_id, secret_token = self.db.get_current_flag(self.team_id, self.service_id)

        self.flag_meta['flag'] = flag
        self.flag_meta['flag_id'] = flag_id
        self.flag_meta['secret_token'] = secret_token

        self.log.info('New flag: %s (flag ID: %s, secret_token %s, team ID: %d, service ID: %d)',
                      flag,
                      flag_id,
                      secret_token,
                      self.team_id,
                      self.service_id
                      )

        if flag is None:
            self.log.warning("Service %d of team %d does not have a flag available", self.service_id, self.team_id)
            return False

        return True

    def get_execution_arguments(self):
        arg_prefix = ["docker", "run", "--rm"]
        # The networking changes if we are running locally because we want to use
        # THe dns service provided by docker compose
        if settings.IS_LOCAL_REGISTRY:
            arg_prefix += ['--network=container:docker_scriptbot{}_1'.format(settings.BOT_ID)]
        # Otherwise we use the VPN when we run remotely
        else:
            arg_prefix += ["--network", "host" ]
        arg_prefix += ['-e', 'TERM=linux', '-e', 'TERMINFO=/etc/terminfo']
        arg_prefix += [self.script_image_path]
        # PROPOSAL: prepend timeout --signal=SIGKILL str(self.timeout)
        # We want to use the host network so we have the correct address resolution for teams
        arg_prefix += ['timeout', str(settings.SCRIPT_TIMEOUT_HARD)]                           # HARD limit for a real kill
        arg_prefix += ['timeout', '-s', 'INT', str(settings.SCRIPT_TIMEOUT_SOFT)]              # soft limit so we can get a traceback
        arg_prefix += [self.script_name]
        arg_prefix += [str(self.ip), str(self.port)]
        try:
            if self.script_type == 'benign':
                self.update_current_flag() # TODO: is it necessary?

                self.flag_meta['flag_id'] = ''
                self.flag_meta['secret_token'] = ''
                args = arg_prefix + [
                    "'%s'" % self.flag_meta['flag_id'],
                    "'%s'" % self.flag_meta['secret_token']
                ]

            elif self.script_type == 'exploit':
                if not self.update_current_flag():
                    raise ScriptExecError('No flag has been set for this service yet')

                if self.flag_meta['flag'] is None:
                    raise ScriptExecError('Could not get current flag from database.')

                if self.flag_meta['flag_id'] is None:
                    raise ScriptExecError('Could not get current flag_id from database.')

                args = arg_prefix + [
                    self.flag_meta['flag_id']
                ]

            elif self.script_type == 'setflag':
                # Generate a new flag
                self.log.info('Getting new flag for service %d', self.service_id)

                self.flag_meta['flag_idx'], self.flag_meta['flag'] = \
                    self.db.generate_flag(self.team_id, self.service_id)

                args = arg_prefix + [
                    self.flag_meta['flag']
                ]

            elif self.script_type == 'getflag':
                if not self.update_current_flag():
                    raise ScriptExecError('No flag has been set for this service yet')

                if self.flag_meta['flag'] is None:
                    raise ScriptExecError('Could not get current flag from database.')

                if self.flag_meta['flag_id'] is None:
                    raise ScriptExecError('Could not get current flag_id from database.')

                args = arg_prefix + [
                    self.flag_meta['flag_id'],
                    self.flag_meta['secret_token']
                ]

            else:
                raise ScriptExecError('Unsupported script type "%s"' % self.script_type)

        except ScriptExecError as ex:
            # Expected exceptions

            error_msg = ERROR_SCRIPT_EXECUTION[1] + \
                  " | An expected exception occurred in ScriptExec.get_execution_arguments(): " + \
                  str(ex) + \
                  " | script details: %s" % self.get_status()

            self.log.warning(error_msg)

            self.result = {
                'error': ERROR_SCRIPT_EXECUTION[0],
                'error_msg': error_msg
            }

            args = None

        except Exception as ex:
            # Unexpected exceptions

            error_msg = ERROR_SCRIPT_EXECUTION[1] + \
                  " | An unexpected exception occurred in ScriptExec.get_execution_arguments(): " + \
                  str(ex) + \
                  str(traceback.format_exc()) + \
                  ' | script details: %s' % self.get_status()
            self.log.error(error_msg)
            self.result = {
                'error': ERROR_SCRIPT_EXECUTION[0],
                'error_msg': error_msg
            }

            args = None

        return args

    def push_result(self, result, output, execution_args):
        try:
            payload = result.get('payload', {})
            if result['error'] == 0:
                if self.script_type == 'setflag':
                    if 'flag_id' not in payload or 'secret_token' not in payload:
                        self.log.error('"flag_id" or "secret_token" is missing. WTF. %r', result)

                    else:
                        self.db.set_secret_token(self.flag_meta['flag_idx'], payload['flag_id'], payload['secret_token'])

                elif self.script_type == 'getflag':
                    if 'flag' not in payload:
                        result['error'] = ERROR_MISSING_FLAG[0]
                        result['error_msg'] = ERROR_MISSING_FLAG[1]

                    elif self.flag_meta['flag'] is not None:
                        if self.flag_meta['flag'] != payload['flag']:
                            # Incorrect flag
                            error_message = \
                                ('[script %d] getflag received an incorrect flag:' +
                                 'expected_flag:%s returned_flag:%s') % (
                                    self.script_id,
                                    self.flag_meta['flag'],
                                    str(payload['flag'])
                                )
                            result['error'] = ERROR_WRONG_FLAG[0]
                            result['error_msg'] = ERROR_WRONG_FLAG[1] + error_message

                elif self.script_type == 'exploit':
                    # No longer supported, but it's not removed in case it's needed in the future
                    if 'flag' not in result:
                        result['error'] = ERROR_MISSING_FLAG[0]
                        result['error_msg'] = ERROR_MISSING_FLAG[1]

                    elif self.flag_meta['flag'] is not None:
                        if self.flag_meta['flag'] != payload['flag']:
                            # Incorrect flag
                            error_message = \
                                ('[script %d] exploit received an incorrect flag:' +
                                 'expected_flag:%s returned_flag:%s') % (
                                    self.script_id,
                                    self.flag_meta['flag'],
                                    str(payload['flag'])
                                )
                            result['error'] = ERROR_WRONG_FLAG[0]
                            result['error_msg'] = ERROR_WRONG_FLAG[1] + error_message

        except Exception as ex:
            # Unexpected exceptions

            self.log.error(
                'An unexpected exception occurred in push_result(): %s\n%s',
                str(ex),
                str(traceback.format_exc())
            )
            result = {
                'error': ERROR_SCRIPT_EXECUTION[0],
                'error_msg': ERROR_SCRIPT_EXECUTION[1] + \
                             " Exception at ScriptExec.push_result(): " + \
                             str(ex) + \
                             ' | script details: %s' % self.get_status()
            }

        self.result = result

        if self.result['error'] != 0:
            msg_prefix = '{{service: %s, type: %s, script_id: %d, ip: %s, port: %d, args: %s}}' % (
                self.service_name, self.script_type, self.script_id, self.ip, self.port, execution_args
            )
            self.log.warning("%s %s", msg_prefix, result['error_msg'])

        else:
            if self.script_type == 'setflag':
                self.log.info("SETFLAG TEAM %s:%d: (flag_id: %s, secret_token: %s) correctly set for service %s",
                 self.ip, self.port, payload['flag_id'], payload['secret_token'], self.service_name)
            elif self.script_type == 'getflag':
                self.log.info("GETFLAG TEAM %s:%d: (flag_id: %s, secret_token: %s, flag: %s) correctly set for service %s",
                 self.ip, self.port, self.flag_meta['flag_id'], self.flag_meta['secret_token'], payload['flag'], self.service_name)
            else:
                pass
                # import ipdb; ipdb.set_trace()

        # Push the result to databas
        self.db.push_result(self.execution_id, result, output)

    def get_status(self):
        s = {
            'team_id': self.team_id,
            'script_id': self.script_id,
            'script_type': self.script_type,
            'dest_ip': self.ip,
            'dest_port': self.port,
            'delay': self.delay,
            'service': self.service_name
        }
        return s

    def run(self):

        self.log.info(
            '[script %d] Running. (script type: %s, target IP: %s, target port: %d, delay: %.2f s)',
            self.script_id,
            self.script_type,
            self.ip,
            self.port,
            self.delay
        )
        time.sleep(self.delay)

        if self.script_type == 'getflag':
            # wait until setflag is done

            start = time.time() # Just for debugging
            self.log.info("[script %d] Waiting for setflag script to terminate...", self.script_id)
            self.setflag_lock.acquire()
            self.log.info("[script %d] setflag script terminated. Took %f seconds to wait for the lock.",
                          self.script_id,
                          time.time() - start
                          )
            # release it immediately since we don't really have to hold it...
            try: self.setflag_lock.release()
            except threading.ThreadError: pass

        try:
            self._run()

            if self.script_type == 'setflag':
                try: self.setflag_lock.release()
                except threading.ThreadError: pass

        except Exception:
            # Make sure the lock is released
            if self.script_type == "setflag":
                try: self.setflag_lock.release()
                except threading.ThreadError: pass

            # re-raise the Exception
            raise

    def _run(self):

        if self.stop:
            # Stop execution. Just terminate.
            self.log.error("[script %d] Script execution terminates prematurely. Are we scheduling too many scripts?" +
                           " (tick: %d, script type: %s, target IP: %s, target port: %d, delay: %d s)",
                           self.script_id,
                           self.state_id,
                           self.script_type,
                           self.ip,
                           self.port,
                           self.delay
                           )
            return

        stdout, stderr = ('', '')
        args = None
        script_outputs = {}

        try:
            args = self.get_execution_arguments()
            if not args:
                raise SchedulerError('Not enough arguments for execution')

            self.log.info('[script %d] Running container (tick: %d, script type: %s, target IP: %s, target port: %d)',
                          self.script_id,
                          self.state_id,
                          self.script_type,
                          self.ip,
                          self.port
                          )
            self.log.debug('[script %d] Container arguments: [ %s ]', self.script_id, ' '.join([str(x) for x in args]))

            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()

            self.log.info('[script %d] Container run returned. ' +
                          '(tick: %d, script type: %s, target IP: %s, target port: %d, self.status: %s)',
                          self.script_id,
                          self.state_id,
                          self.script_type,
                          self.ip,
                          self.port,
                          str(self.get_status())
                          )

            if stdout is None:
                raise SchedulerError('No output from the script')

            decoded_stdout = stdout.decode('utf-8').strip()
            decoded_stderr = stderr.decode('utf-8').strip()
            script_outputs = {
                'stdout': decoded_stdout[:self.max_output_send_bytes],
                'stderr': decoded_stderr[:self.max_output_send_bytes]
            }

            try:
                self.result = json.loads(decoded_stdout)
            except ValueError:
                # Invalid JSON
                raise SchedulerError('Invalid output from the script. Arguments: {}, output: {}'.format(
                    args, decoded_stdout))

            if self.result['error']:
                self.result["error_msg"] += repr(' | Script Object:' + str(
                    self.get_status()) + " | Script output stdout:\n" + decoded_stdout + '\n| stderr:\n' + decoded_stderr)

        except SchedulerError as ex:
            # Expected exceptions

            if stderr is None:
                stderr = b''

            if isinstance(stderr, bytes):
                stderr = stderr.decode('utf-8').strip()

            if stdout is None:
                stdout = b''

            if isinstance(stdout, bytes):
                stdout = stdout.decode('utf-8').strip()

            self.result = {
                'error': ERROR_SCRIPT_EXECUTION[0],
                'error_msg': ERROR_SCRIPT_EXECUTION[1] + \
                             " Exception at ScriptExec.run(): " + \
                             str(ex) + \
                             str(traceback.format_exc()) + \
                             ' | script details: %s' % self.get_status() + \
                             " | script output: stdout:\n" + \
                             stdout + \
                             '\n | stderr:\n' + \
                             stderr
            }

        except Exception as ex:
            # Unexpected exceptions

            if stderr is None:
                stderr = b''

            if isinstance(stderr, bytes):
                stderr = stderr.decode('utf-8').strip()

            if stdout is None:
                stdout = b''

            if isinstance(stdout, bytes):
                stdout = stdout.decode('utf-8').strip()

            error_msg = ERROR_SCRIPT_EXECUTION[1] + \
                         " Exception at ScriptExec.run(): " + \
                         str(ex) + \
                         str(traceback.format_exc()) + \
                         ' | script details: %s' % self.get_status() + \
                         " | script output: stdout:\n" + \
                         stdout + \
                         '\n | stderr:\n' + \
                         stderr

            self.log.error("An unexpected exception occurred in running sandbox: %s", error_msg)
            self.result = {
                'error': ERROR_SCRIPT_EXECUTION[0],
                'error_msg': error_msg
            }

        if self.stop:
            # We should stop, but let's keep pushing result anyway
            self.log.warning("[script %d] It's a little bit late to push results. Are we scheduling too many scripts?" +
                           " (tick: %d, script type: %s, target IP: %s, target port: %d, delay: %d s)",
                           self.script_id,
                           self.state_id,
                           self.script_type,
                           self.ip,
                           self.port,
                           self.delay
                           )

        try:
            script_outputs = str(script_outputs)
            self.log.info('[script %d] Tick %d, pushing result to remote side: %s | %s',
                          self.script_id,
                          self.state_id,
                          self.result,
                          script_outputs
                          )
            self.push_result(self.result, script_outputs, args)

        except Exception as ex:
            # Unexpected exceptions
            self.log.error('An unexpected exception occurred when updating service state: %s\n%s',
                           str(ex),
                           str(traceback.format_exc())
                           )


class Scheduler(object):

    def __init__(self,
                 status_path=settings.STATUS_PATH,
                 tmp_script_path=settings.TMP_SCRIPT_PATH,
                 tmp_script_path_salt=settings.TMP_SCRIPT_PATH_SALT,
                 state_check_interval=settings.STATE_CHECK_INTERVAL,
                 is_local_test=False,
                 db_client=None,
                 registry_client=None,
                 is_synchronous=False
                 ):

        global verbose

        self.state_id = None
        self.state_changed = False
        self.services = {}
        self.scripts = {}
        self.scripts_to_run = {}
        self.test_user = None
        self.teams = {}
        self.state_expire = settings.STATE_EXPIRE_MIN
        self.state_check_interval = state_check_interval
        self.status_path = status_path
        self.db = DBClient() if db_client is None else db_client
        self.registry = RegistryClient() if registry_client is None else registry_client
        # A list of all ScriptExecutor objects
        self._script_executors = [ ]
        # Saves all updated script IDs. We assume that an uploaded script cannot be modified later.
        self._updated_script_ids = set()
        # All setflag locks in the current tick
        self._setflag_locks = [ ]
        # A lock that guards self._setflag_locks
        self._setflag_locks_list_lock = threading.Lock()
        self.tmp_script_path = tmp_script_path
        self.tmp_script_path_salt = tmp_script_path_salt
        self.status = {
            'state_id': 'INIT',
            'last_error': None,
            'script_err': None,
            'script_ok': 0,
            'script_fail': 0,
            'script_tot': 0
        }
        self.log = logging.getLogger('scriptbot.scheduler')
        self.log.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))

        self.is_synchronous = is_synchronous

        if verbose:
            self.log.setLevel(logging.DEBUG)

        # seed
        random.seed(time.time())
        self.log.info('#' * 80)
        self.log.info('#' * 80)
        self.log.info('Init')

    def _get_gamebox_ip(self, team_id):
        # Ugly workaround for local testing.
        # hopefully we will never have 10000 teams playing
        return "team%d" % (team_id) if team_id != 9999 else "127.0.0.1"

    def _pick_teams(self, team_id_list):
        """
        From a list of all team IDs, pick 1/n teams for this bot based on the current scriptbot ID and the total number
        of scriptbots we have.

        :param team_id_list: A list of all team IDs
        :return: a new list of team IDs
        """
        sorted_list = sorted([ int(i) for i in team_id_list ])
        result = [ ]
        self.log.info("IN PICK TEAMS : %r", sorted_list)

        # Fix setting when testing scriptbot locally
        scriptbot_num = settings.ALL_BOTS
        scriptbot_id = settings.BOT_ID

        for i, team_id in enumerate(sorted_list):
            if i % scriptbot_num == (scriptbot_id - 1):
                result.append(team_id)

        return result

    def _add_setflag_lock(self, lock):
        """
        Put a setflag lock into our list

        :param lock: a Lock object
        :return: None
        """

        if lock is None:
            return

        self._setflag_locks_list_lock.acquire()
        self._setflag_locks.append(lock)
        self._setflag_locks_list_lock.release()

    def _release_all_setflag_locks(self):
        """
        Release all setflag locks

        :return: None
        """

        self._setflag_locks_list_lock.acquire()

        for lock in self._setflag_locks:
            try: lock.release()
            except threading.ThreadError: pass

        # Clear the list
        self._setflag_locks = [ ]

        self._setflag_locks_list_lock.release()

    def __del__(self):
        self.status['state_id'] = 'EXIT'
        self.update_status()

    def get_scripts_to_run(self, team_id, service_id):
        """
        Get all scripts to run in the current tick for a specific combination of team and service.
        The order of those scripts will be respected when scheduling.

        :param team_id: ID of the team
        :param service_id: ID of the service
        :return: A list of ScriptExecution instances.
        """

        if team_id not in self.scripts_to_run:
            return []

        if service_id not in self.scripts_to_run[team_id]:
            return []

        return self.scripts_to_run[team_id][service_id]

    def get_teams(self):
        """
        Get a list of all teams
        """

        team_dict = self.db.get_teams()

        return team_dict

    def update_status(self):
        """
        Update game status to an external JSON file.

        :return: None
        """

        self.status['teams'] = list(self.teams.keys())
        self.status['state_expire'] = self.state_expire

        with open(self.status_path, 'wb') as o:
            o.write(json.dumps(self.status).encode('utf-8'))

    def _load_scripts_to_run(self):
        # Get a list of all scripts to run in the current tick

        run_scripts = self.db.get_scripts_to_run()

        self.log.info("Got %d script execution requests", len(run_scripts))

        self.scripts_to_run = { }

        for run_script in run_scripts:
            execution_id = run_script['id']
            script_id = run_script['script_id']
            target_team_id = run_script['against_team_id']

            if target_team_id not in  self.scripts_to_run:
                self.scripts_to_run[target_team_id] = defaultdict(list)

            script_meta = self.scripts[script_id]
            service_id = script_meta['service_id']

            self.scripts_to_run[target_team_id][service_id].append(
                ScriptExecution(execution_id, script_id, target_team_id)
            )

    def load_game_state(self, state=None):
        """
        Load a new game state from the database.

        :param state: A state dict used for testing.
        :return: None
        """

        try:
            if state is None:
                state = self.db.get_game_state()

            # Get data out of the dict

            self.state_expire = state['state_expire']
            if self.state_expire < settings.STATE_EXPIRE_MIN:
                self.state_expire = settings.STATE_EXPIRE_MIN

            for service in state['services']:
                self.services[int(service['service_id'])] = service

            for script in state['scripts']:
                d = dict(script)
                d['service_name'] = self.services[d['service_id']]['service_name']
                d['docker_image_name'] = d['service_name'] + '_scripts'
                if settings.IS_LOCAL_REGISTRY:
                    d['docker_image_path'] = d['docker_image_name']
                else:
                    d['docker_image_path'] = '{}/{}'.format(self.registry.registry_endpoint, d['docker_image_name'])

                self.scripts[int(script['script_id'])] = d

            if self.state_id == state['state_id']:
                # State is not changed - we are still in the last state
                self.state_changed = False
                self.log.debug('We are still in previous game state, state ID %d.', self.state_id)

            else:
                # The game ticks forward
                self.state_changed = True
                new_state_id = state['state_id']

                self.log.info(
                    'Game ticks forward. The game state changed from %s to %s.', # new_state_id might be None at first
                    self.state_id,
                    new_state_id
                )
                self.log.debug(
                    "All services: %s",
                    self.services
                )
                self.log.debug(
                    "All scripts: %s",
                    self.scripts
                )

                # Update all info
                self.state_id = new_state_id
                self.status['state_id'] = self.state_id

        except Exception as ex:
            # Unexpected exceptions
            error_msg = "An unexpected exception occurred when updating game state: %s\n%s" % (
                str(ex),
                str(traceback.format_exc())
            )

            self.log.error(error_msg)

            self.status['last_error'] = str(datetime.datetime.now()) + ': ' + error_msg

    def update_script(self, script_id):
        script_id = int(script_id)

        try:
            scripts_image_name = self.scripts[script_id]['docker_image_name']
            self.log.info('SCRIPT: ID: %s, IMAGE PATH: %s', script_id, scripts_image_name)

            try:
                self.registry.pull_new_image(scripts_image_name)
                
            except RegistryClientPullError as ex:
                msg = "An unexpected exception occurred when pulling from registry and updating script %d (image %s): %s\n%s" % (
                    script_id,
                    scripts_image_name,
                    str(ex),
                    str(traceback.format_exc())
                )
                self.log.error(msg)
                self.status['last_error'] = str(datetime.datetime.now()) + ': ' + msg


        except Exception as ex:
            # Unexpected exceptions
            error_msg = 'An unexpected exception occurred when updating script %d: %s\n%s' % (
                script_id,
                str(ex),
                str(traceback.format_exc())
            )
            self.log.error(error_msg)
            self.status['last_error'] = str(datetime.datetime.now()) + ': ' + error_msg
            return None

    def get_random_delay(self, run_list):
        """
        Add random delay between execution of scripts

        :param run_list: A list of ScriptExecution objects to be executed
        :return: A new list of tuples (script_id, delay)
        """
        # TODO: What is this? it seems to return a constant value everytime...
        items = len(run_list)

        interval = float(self.state_expire - settings.STATE_EXPIRE_MIN) / items

        d = []
        last_delay = None
        for i, script_exec in enumerate(run_list):
            script_id = script_exec.script_id

            delay = i * interval + interval - random.gauss(interval, settings.SIGMA_FACTOR * interval)
            # delay = interval - random.gauss(interval, settings.SIGMA_FACTOR * interval)
            delay = abs(delay)
            script_type = self.scripts[script_id]['type']

            if script_type == 'setflag':
                last_delay = delay

            elif script_type == 'getflag':
                if last_delay is not None:
                    if (delay - last_delay) < settings.SET_GET_FLAG_TIME_DIFFERENCE_MIN:
                        self.log.info(
                            'delay (%.2f) - last_delay (%.2f) < SET_GET_FLAG_TIME_DIFFERENCE_MIN (%.2f)',
                            delay,
                            last_delay,
                            settings.SET_GET_FLAG_TIME_DIFFERENCE_MIN
                        )
                        delay = last_delay + settings.SET_GET_FLAG_TIME_DIFFERENCE_MIN

            d.append(delay)

        return list(zip(run_list, d))

    def run_scripts(self, team_meta):
        """
        Start a new thread to run a bunch of scripts.

        :param team_meta: A descriptor (dict) for a team

        :return: The Thread object
        """

        th = threading.Thread(target=self._run_scripts, args=(team_meta, ))
        th.setDaemon(True)

        th.start()
        return th

    def _run_scripts(self, team_meta):
        """
        Run a bunch of scripts.

        :param team_meta: A descriptor (dict) for a team
        :return: None
        """
        team_id = team_meta['id']

        ip = self._get_gamebox_ip(team_id)

        if team_id not in self.scripts_to_run:
            self.log.info('No script to run for %s.' % (str(team_meta)))
            return

        self.status['script_tot'] += len(self.scripts_to_run[team_id])

        for service_id, script_exec_list in self.scripts_to_run[team_id].items():

            script_id_and_delay = self.get_random_delay(script_exec_list)

            # Create a lock for setflag and getflag
            setflag_lock = threading.Lock()
            setflag_lock.acquire()

            # Log this lock so we can release all locks in time when tha game moves to a new tick
            self._add_setflag_lock(setflag_lock)

            for script_exec, delay in script_id_and_delay:
                service_name = self.services[service_id]['service_name']
                script_meta = self.scripts[script_exec.script_id]
                script_type = script_meta['type']
                script_name = script_meta['script_name']
                script_image_path = script_meta['docker_image_path']

                self.run_script(
                    team_id,
                    script_exec.idx,
                    script_exec.script_id,
                    service_id,
                    service_name,
                    script_image_path,
                    script_type,
                    script_name,
                    ip,
                    self.services[service_id]['port'],
                    delay,
                    synchronous=self.is_synchronous,
                    setflag_lock=(setflag_lock if script_type in ('setflag', 'getflag') else None)
                )

    def run_script(self, team_id, execution_id, script_id, service_id, service_name, script_image_path, script_type, script_name,
                   ip, port, delay, synchronous=True, setflag_lock=None):
        """
        Synchronously or asynchronously run a single script.

        :param team_id:
        :param execution_id:
        :param script_id:
        :param service_id:
        :param timeout:
        :param script_type:
        :param script_image_name:
        :param ip:
        :param port:
        :param delay:
        :param synchronous:
        :param setflag_lock:
        :return: None
        """

        self.log.info('executing script for team {}'.format(team_id))

        se = ScriptExecutor(
            self.state_id,
            team_id,
            execution_id,
            script_id,
            service_id,
            service_name,
            script_image_path,
            script_type,
            script_name,
            ip,
            port,
            delay,
            setflag_lock=setflag_lock,
            db_client=self.db
        )

        self._add_script_executor(se)

        # Start the thread
        se.start()

        if synchronous:
            se.join()

    def schedule_scripts(self):
        self.log.info('schedule_scripts')
        teams = self._pick_teams(list(self.teams.keys()))
        self.log.info("%d teams for this bot: %s", len(teams), teams)

        # Shuffle those teams
        random.shuffle(teams)

        all_threads = [ ]

        for i in teams:
            t = self.teams[i]
            try:
                self.log.info('Creating a new thread to run all scripts against team %d', i)
                thread = self.run_scripts(t)
                all_threads.append(thread)

            except Exception as ex:
                # Unexpected exceptions
                error_msg = 'An unexpected exception occurred when launching scripts: %s\n%s' % (
                    str(ex),
                    str(traceback.format_exc())
                )
                self.log.error(error_msg)
                self.status['last_error'] = str(datetime.datetime.now()) + ': ' + error_msg

        # Join all threads
        for thread in all_threads:
            thread.join()

    def execute_round(self, state):

        try:
            self.load_game_state()
            if self.state_changed:

                # Stop execution of all old threads
                self._stop_old_script_executors()
                # Release all past setflag locks
                self._release_all_setflag_locks()

                # Load new scripts to run
                self._load_scripts_to_run()

                for script_id in self.scripts:
                    self.update_script(script_id)

                self.state_changed = False
                st = time.time()
                self.schedule_scripts()
                lt = time.time()
                self.log.info('Schedule_scripts time:%f' % (lt - st))

        except Exception as ex:
            # Unexpected exceptions
            error_msg = 'An unexpected exception occurred in Scheduler thread: %s\n%s' % (
                str(ex),
                str(traceback.format_exc())
            )
            self.log.error(error_msg)

            self.status['last_error'] = str(datetime.datetime.now()) + ' : ' + error_msg

        finally:
            try:
                self.update_status()
            except Exception as ex:
                # Unexpected exceptions
                error_msg = 'An unexpected exception occurred in Scheduler thread: %s\n%s' % (
                    str(ex),
                    str(traceback.format_exc())
                )
                self.log.error(error_msg)
                self.status['last_error'] = str(datetime.datetime.now()) + ' : ' + error_msg

    def run(self):
        self.log.info('Scheduler begins')

        while True:
            state = self.db.get_game_state()

            self.execute_round(state)

            # Sleep until next state check
            time.sleep(self.state_check_interval)

    def _stop_old_script_executors(self):
        """
        Stop execution of all old threads that are created in the previous tick.

        :return: None
        """

        for se in self._script_executors:
            se.stop = True

        self._script_executors = [ ]

    def _add_script_executor(self, script_executor):
        """
        Add script executor to a list.

        :param script_executor: A ScriptExecutor instance.
        :return: None
        """

        self._script_executors.append(script_executor)

    def wait_game_is_ready(self):
        while True:
            try:
                state = self.db.get_game_state()
                if not 'game_id' in state:
                    self.log.info('Game not ready, waiting')
                    time.sleep(5)
                    continue
                return 
            except DBClientError as ex:
                self.log.info("The database is not ready yet...")
                time.sleep(5)
                continue


def main():

    # Adjust open file limit
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    if soft < 65536 or hard < 65536:
        l = logging.getLogger('main')
        l.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))

        l.warning('Open file limits (soft %d, hard %d) are too low. 65536 recommended. ' +
                  'Will increase soft limit. ' +
                  'You might want to adjust hard limit as well.',
                  soft,
                  hard
                  )
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))
        except ValueError:
            l.error('Failed to adjust open file limits. Please adjust them manually.')

    if (not os.path.exists("/var/log/scriptbot/error.log")):
        open("/var/log/scriptbot/error.log","w+").write("\n")
        os.chmod("/var/log/scriptbot/error.log", 0o666)

    s = Scheduler()
    s.wait_game_is_ready()
    s.teams = s.get_teams()
    s.log.info("RETRIEVED TEAMS : %r", s.teams)
    s.run()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", default=False, action='store_true')
    ap.add_argument("-t", "--test", default=False, action='store_true')

    args = ap.parse_args()

    verbose = args.verbose

    try:
        logdir = os.path.dirname(settings.LOG_PATH)
        if not os.path.exists(logdir):
            os.makedirs(logdir)
    except Exception as e:
        print(e)
        pass
    
    logging.basicConfig(
        level="INFO",
        format='%(levelname)-1s | %(asctime)-23s | %(name)-24s | %(message)s',
        handlers = [
            logging.FileHandler(settings.LOG_PATH),
            logging.StreamHandler(),
        ]
    )

    main()
