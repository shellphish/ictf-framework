from settings import LOGSTASH_IP, LOGSTASH_PORT
import settings

import json
import logging
import logstash
import requests
import time


class DBClientError(Exception):
    pass

class DBClientQueryError(DBClientError):
    def __init__(self, message, status_code):
        DBClientError.__init__(self, message)
        self.status_code = status_code


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

            # Return JSON if successful
            if r.status_code == 200:
                return json.loads(r.content.decode('utf-8'))

            elif r.status_code == 502 and retry_times > 0:
                self.log.error(
                    "Database request [GET]'%s' failed with HTTP 502. "
                    "Will retry after %s seconds" %
                    (api, settings.DATABASE_REQUEST_RETRY_INTERVAL)
                )

                # back off and pause a while before retrying
                retry_times -= 1
                time.sleep(settings.DATABASE_REQUEST_RETRY_INTERVAL)
                continue

            else:
                # HTTP request failed?
                raise DBClientQueryError(
                    "Database request [GET]'%s' returns an unexpected HTTP status code %d" % (api, r.status_code),
                    r.status_code
                )


    def _post(self, api, data, authentication=True):
        """
        Make a post to the database backend

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

            # Return JSON if successful
            if r.status_code == 200:
                return json.loads(r.content.decode('utf-8'))

            elif r.status_code == 502 and retry_times > 0:
                self.log.error(
                    "Database request [POST]'%s'(data: %s) failed with HTTP 502. "
                    "Will retry after %s seconds" %
                    (api, data, settings.DATABASE_REQUEST_RETRY_INTERVAL)
                )

                # back off and pause a while before retrying
                retry_times -= 1
                time.sleep(settings.DATABASE_REQUEST_RETRY_INTERVAL)
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

