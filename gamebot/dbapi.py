__author__ = 'machiry'
import urllib
import json
import logging
import logstash
import coloredlogs
import requests
from datetime import datetime
from settings import *


class DBApi:

    LOG_FMT = '%(levelname)s - %(asctime)s (%(name)s): %(msg)s'
    LATEST_WORKING_SCRIPTS = 'scripts/latest/enabled'
    UPDATE_SCRIPTS_TO_RUN = 'scripts/torun/update/%s'
    GET_AFFECTED_FLAG_INFO = 'flags/affected/tick/%s'
    GET_SERVICES_STATE = 'services/states/tick/%s'
    GET_EXPLOITED_SERVICES = 'services/exploited'
    GET_TICK_SCORES = 'scores'
    GET_FIRST_BLOODS = 'scores/firstbloods/tick/%s'
    UPDATE_TICK_SCORES = 'scores/store/tick/%s'
    GET_ALL_TEAMS = 'teams/info'
    GET_ALL_SERVICES = 'services/state/enabled'
    GET_CURRENT_TICK = 'game/tick'
    UPDATE_TICK_INFO = 'game/tick/update'
    GET_TICK_CONFIG = 'game/tick/config'
    GAME_STATE = 'game/state'
    GET_SCRIPTS_RUN_STATS = 'scripts/runstats/tick/%s'
    SET_SERVICE_STATE = 'service/state/set/%s/team/%s'
    BULK_UPDATE_SERVICE_STATE = 'service/state/set/bulk'
    PING_DBAPI = 'game/ping'

    GET_SCRIPTS_TO_RUN = 'scripts/get/torun/%s'
    GET_FULL_GAME_STATE = 'game/state'

    def __init__(self, db_host=DB_HOST, db_secret=DB_SECRET, log_level=logging.INFO):

        # Set up db
        self.db_host = db_host
        self.db_secret = db_secret

        # Set up logging
        log = logging.getLogger('gamebot_dbapi')
        log.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))
        log.setLevel(log_level)
        log_formatter = coloredlogs.ColoredFormatter(DBApi.LOG_FMT)
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(log_formatter)
        log.addHandler(log_handler)

        self.log = log

    @staticmethod
    def _get_json_response(url_secret_pair, post_data=None, target_logger=None):
        """
        Fetches the provided url content and reads them as json object.
        :param url_secret_pair: Pair of URL and corresponding DB secret.
        :param post_data: dictionary that need to be passed as post parameter
        :return: Response as json object.
        """

        target_url = url_secret_pair[0]
        db_secret = url_secret_pair[1]
        params = {'secret': db_secret}
        if post_data is None:
            if target_logger is not None:
                target_logger.debug("Get Url:" + str(target_url))
            r = requests.get(target_url, params=params)
        else:
            if target_logger is not None:
                target_logger.debug("Post Url:" + str(target_url))
            r = requests.post(target_url, params=params, data=post_data)
        try:
            ans = json.loads(r.content)
        except ValueError:
            target_logger.critical("Error Happened while trying to decode json response from URL:" + str(target_url) +
                                   ", Content Received:" + str(r.content))
            raise ValueError("Non Json Response from DB.")
        return ans

    def __build_url(self, rel_path):
        url = "http://%s/%s" % (self.db_host, rel_path)
        return url, self.db_secret

    def check_connection(self):
        """
        Method to check if connection to db is up or not.
        :return: True/False depending on whether the db api is up or not.
        """
        target_url = self.__build_url(DBApi.PING_DBAPI)
        try:
            ping_response = urllib.request.urlopen(target_url[0]).read()
            return ping_response == b'lareneg'
        except IOError:
            return False

    def get_tick_config(self):
        """
        Gets the tick configuration.
        :return: tuple containing tick time,
                number of benign scripts,
                number of exploit scripts and
                number of get flag scripts
                respectively.
        """
        target_url = self.__build_url(DBApi.GET_TICK_CONFIG)
        # No need to profile.
        tick_config_response = DBApi._get_json_response(target_url, target_logger=self.log)
        tick_time = tick_config_response["TICK_TIME"]
        num_ben = tick_config_response["NO_BEN"]
        num_exp = tick_config_response["NO_EXP"]
        num_get_flag = tick_config_response["NO_GET_FLAGS"]
        return tick_time, num_ben, num_exp, num_get_flag

    def get_current_tick_info(self):
        """
        Gets the current tick information
        :return: Pair of tick id and approximate seconds left
        """
        target_url = self.__build_url(DBApi.GET_CURRENT_TICK)
        # No need to profile.
        tick_response = DBApi._get_json_response(target_url, target_logger=self.log)
        return tick_response["tick_id"], tick_response["approximate_seconds_left"]

    def get_game_state(self):
        """
        Gets the current game state
        :return: Either the game_id (int) or None
        """
        target_url = self.__build_url(DBApi.GAME_STATE)
        # No need to profile.
        game_state_response = DBApi._get_json_response(target_url, target_logger=self.log)
        if 'game_id' in game_state_response:
            game_id = int(game_state_response['game_id'])
        else:
            game_id = None

        return game_id


    def get_all_team_ids(self):
        """
        Gets all the team ids from the database.
        :return: List of all team ids
        """
        target_url = self.__build_url(DBApi.GET_ALL_TEAMS)
        teams_response = DBApi._get_json_response(target_url, target_logger=self.log)
        team_ids = []
        if "teams" not in teams_response:
            self.log.error("Invalid Response for DB Url:" + str(target_url))
        else:
            for curr_team in teams_response["teams"]:
                # Adding only validated teams.
                if str(teams_response["teams"][curr_team]["validated"]) == "1":
                    team_ids.append(curr_team)
        return team_ids

    def update_tick_info(self, time_to_change, created_on):
        """
        Updated the ticks with information of new tick.

        :param time_to_change: datetime ISO string representing time to change.
        :param created_on: datetime indicating creation time
        :return: latest tick id
        """
        target_url = self.__build_url(DBApi.UPDATE_TICK_INFO)
        # No need to profile
        # prepare post data
        post_data = {"time_to_change": time_to_change, "created_on": created_on}
        update_tick_response = DBApi._get_json_response(target_url, post_data=post_data, target_logger=self.log)
        return update_tick_response["tick_id"]

    def get_working_scripts(self):
        """
        Get all working scripts
        :return: json object containing the response.
        """
        target_url = self.__build_url(DBApi.LATEST_WORKING_SCRIPTS)
        # Profiling, get old time
        old_time = datetime.now()
        script_response = DBApi._get_json_response(target_url, target_logger=self.log)
        # Log time taken to perform the query
        self.log.debug("Time for get_working_scripts api " + str(datetime.now() - old_time))
        all_scripts = []
        if "scripts" not in script_response:
            self.log.error("Invalid Response from DB API for:" + DBApi.LATEST_WORKING_SCRIPTS)
            return all_scripts
        self.log.info("Got Working Scripts Response")
        return script_response["scripts"]

    def get_scripts_to_run(self, tick_id):
        """
        Get a list of all scripts to run in the current tick.
        API: /scripts/get/torun
        :return: a list of script execution records
        """
        target_url = self.__build_url(DBApi.GET_SCRIPTS_TO_RUN % str(tick_id))
        r = DBApi._get_json_response(target_url, target_logger=self.log)
        return r['scripts_to_run']

    def get_full_game_state(self):
        """
        Get the game state
        API: /game/state
        :return: A huge dict that contains almost everything
        """
        target_url = self.__build_url(DBApi.GET_FULL_GAME_STATE)
        return DBApi._get_json_response(target_url, target_logger=self.log)

    def set_service_state(self, service_id, team_id, state, reason):
        """
        Sets state of particular service for particular team.
        :param service_id: Id of the service to set the state.
        :param team_id: team id for which the state to be set.
        :param state: state name
        :param reason: reason for setting this state
        :return: True if success else False
        """
        target_url = self.__build_url(DBApi.SET_SERVICE_STATE % (str(service_id), str(team_id)))
        # prepare post data
        post_data = {"state": state, "reason": reason}
        # Profiling, get old time
        old_time = datetime.now()
        update_response = DBApi._get_json_response(target_url, post_data=post_data, target_logger=self.log)
        self.log.debug("Time for set service state api " + str(datetime.now() - old_time))
        if "result" not in update_response:
            self.log.error("Invalid Response from DB API for:" + DBApi.UPDATE_SCRIPTS_TO_RUN)
            return False
        self.log.debug("Got set service state Response")
        return update_response["result"] == "success"

    def get_scripts_run_stats(self, tick_id):
        """
        Gets run state of all the scripts in the provided tick.
        :param tick_id: Tick id for which the run stats information need to be fetched.
        :return: Json object in the following format:
            {"team_id":{"service_id" : <non_negative number for up else down>}}
        """
        target_url = self.__build_url(DBApi.GET_SCRIPTS_RUN_STATS % str(tick_id))
        # Profiling, get old time
        old_time = datetime.now()
        scripts_run_stats = DBApi._get_json_response(target_url, target_logger=self.log)
        self.log.debug("Time for get_scripts_run_stats api " + str(datetime.now() - old_time))
        scripts_resp = {}

        if "script_runs" not in scripts_run_stats:
            self.log.error("Invalid Response from DB API for:" + str(target_url))
        else:
            self.log.info("Got scripts run stats Response")
            script_run_response_list = scripts_run_stats["script_runs"]
            for curr_run_info in script_run_response_list:
                curr_team_id = str(curr_run_info["against_team_id"])
                curr_service_id = str(curr_run_info["service_id"])
                num_runs = int(curr_run_info["number_runs"])
                num_success = int(curr_run_info["successes"])
                not_ran = int(curr_run_info["not_ran"])
                if curr_team_id not in scripts_resp:
                    scripts_resp[curr_team_id] = {}
                scripts_resp[curr_team_id][curr_service_id] = (num_success, num_runs, not_ran)

        return scripts_resp

    def bulk_update_team_service_state(self, bulk_info):
        """
        Updates the state of service for each team in bulk.
        :param bulk_info: dictionary containing info to be updated
        :return: True if success else False
        """
        to_send_data = []
        for curr_team in bulk_info:
            for curr_service in bulk_info[curr_team]:
                tick_id = bulk_info[curr_team][curr_service][0]
                state = bulk_info[curr_team][curr_service][1]
                reason = bulk_info[curr_team][curr_service][2]
                to_send_data.append({"team_id": curr_team, "service_id": curr_service, "state": state,
                                     "tick_id": tick_id, "reason": reason})
        # Profiling, get old time
        old_time = datetime.now()
        target_url = self.__build_url(DBApi.BULK_UPDATE_SERVICE_STATE)
        bulk_update_status = DBApi._get_json_response(target_url,
                                                      post_data={"bulk_update_info": json.dumps(to_send_data)},
                                                      target_logger=self.log)
        if "result" not in bulk_update_status:
            self.log.error("Invalid Response from DB API for:" + str(target_url))
            return False
        self.log.debug("Got bulk update scripts Response in:" + str(datetime.now() - old_time))
        return bulk_update_status["result"] == "success"

    def update_scripts_to_run(self, team_id, tick_id, list_of_scripts):
        """
        Update scripts to be run for the given team and tick
        :param team_id: Team id against which scripts should be run.
        :param tick_id: Tick id during which the scripts should be scheduled to run.
        :param list_of_scripts: List of script ids that need to be run
        :return: True or False indicating success or Failure respectively.
        """
        target_url = self.__build_url(DBApi.UPDATE_SCRIPTS_TO_RUN % str(team_id))
        # prepare post data
        post_data = {"tick_id": tick_id, "scripts_in_json": json.dumps(list_of_scripts)}
        # Profiling, get old time
        old_time = datetime.now()
        update_response = DBApi._get_json_response(target_url, post_data=post_data, target_logger=self.log)
        self.log.debug("Time for update_scripts_to_run api " + str(datetime.now() - old_time))
        if "result" not in update_response:
            self.log.error("Invalid Response from DB API for:" + DBApi.UPDATE_SCRIPTS_TO_RUN)
            return False
        self.log.info("Got update scripts Response")
        return update_response["result"] == "success"

    def get_services_state(self, tick_id):
        """
        Gets state of all the services in the provided tick.
        :param tick_id: Tick id for which the service state information need to be fetched.
        :return: Json object returned by db endpoint
        """
        target_url = self.__build_url(DBApi.GET_SERVICES_STATE % str(tick_id))
        # Profiling, get old time
        old_time = datetime.now()
        service_state_raw = DBApi._get_json_response(target_url, target_logger=self.log)
        self.log.debug("Time for get_services_state api " + str(datetime.now() - old_time))
        service_state_response = {}
        if "service_states" not in service_state_raw:
            self.log.error("Invalid Response from DB API for:" + str(target_url))
        else:
            service_state_response = service_state_raw["service_states"]
            self.log.info("Got service state info Response")
        return service_state_response

    def get_exploited_services(self):
        """
        Gets dictionary of all exploited services and corresponding teams.
        :return: Json object returned by db endpoint.
        """
        target_url = self.__build_url(DBApi.GET_EXPLOITED_SERVICES)
        # Profiling, get old time
        old_time = datetime.now()
        exploited_services = DBApi._get_json_response(target_url, target_logger=self.log)
        self.log.debug("Time for get_exploited_services api " + str(datetime.now() - old_time))
        if 'exploited_services' not in exploited_services:
            self.log.error("Invalid Response from DB API for:" + DBApi.GET_EXPLOITED_SERVICES)
            return {"exploited_services": {}}
        self.log.info("Got exploited services Response")
        return exploited_services

    def get_tick_scores(self):
        """
        Gets dictionary of latest scores of all the teams.
        :return: Json object returned by db endpoint.
        """
        target_url = self.__build_url(DBApi.GET_TICK_SCORES)
        # Profiling, get old time
        old_time = datetime.now()
        tick_scores_resp = DBApi._get_json_response(target_url, target_logger=self.log)
        self.log.debug("Time for get_tick_scores api " + str(datetime.now() - old_time))
        tick_scores = {}
        if "scores" not in tick_scores_resp:
            self.log.error("Invalid Response from DB API for:" + str(target_url))
        else:
            tick_scores = tick_scores_resp["scores"]
        return tick_scores

    def update_tick_scores(self, tick_id, all_teams, team_sla_points, team_attack_points, team_service_points,
                           team_total_points, team_valid_ticks):
        """
        Updates the scores of all the teams up to the current tick.
        :param all_teams: all teams
            List containing all team ids
        :param tick_id: Target tick id to be updated
        :param team_sla_points:
            Dictionary containing for each team the corresponding sla points.
             {
               team_id:<sla_points>,
             }
        :param team_attack_points:
            Dictionary containing for each team the corresponding attack points.
             {
               team_id:<attack_points>,

             }
        :param team_service_points:
            Dictionary containing for each team the corresponding service points.
             {
               team_id:<service_points>,

             }
        :param team_total_points:
            Dictionary containing for each team the total points.
             {
               team_id:<total_points>,

             }
        :param team_valid_ticks:
            Dictionary containing for each team the number of valid ticks.
             {
               team_id: <number_of_valid_ticks>,

             }
        :return:
        """
        # Prepare request JSON
        request_json = {}
        for curr_team_id in all_teams:
            scores_dic = {}
            sla_points = 0.0
            if curr_team_id in team_sla_points:
                sla_points = team_sla_points[curr_team_id]
            attack_points = 0.0
            if curr_team_id in team_attack_points:
                attack_points = team_attack_points[curr_team_id]
            service_points = 0.0
            if curr_team_id in team_service_points:
                service_points = team_service_points[curr_team_id]
            total_points = 0.0
            if curr_team_id in team_total_points:
                total_points = team_total_points[curr_team_id]
            num_valid_ticks = team_valid_ticks[curr_team_id]
            scores_dic["service_points"] = service_points
            scores_dic["attack_points"] = attack_points
            scores_dic["sla"] = sla_points
            scores_dic["total_points"] = total_points
            scores_dic["num_valid_ticks"] = num_valid_ticks
            scores_dic["team_id"] = curr_team_id
            request_json[curr_team_id] = scores_dic

        target_url = self.__build_url(DBApi.UPDATE_TICK_SCORES % str(tick_id))
        # Profiling, get old time
        old_time = datetime.now()
        update_response = DBApi._get_json_response(target_url, post_data={"scores": json.dumps(request_json)},
                                                   target_logger=self.log)
        self.log.debug("Time for update_tick_scores api " + str(datetime.now() - old_time))
        if "result" not in update_response:
            self.log.error("Invalid Response from DB API for:" + DBApi.UPDATE_TICK_SCORES)
            return False
        self.log.info("Got update tick scores Response")
        return update_response["result"] == "success"

    def get_first_bloods(self, tick_id):
        """
        Gets dictionary of all teams and their corresponding first blood services during the specified tick.
        :param tick_id: Tick id for which the first blood information need to be fetched.
        :return: Json object in the form below:
            {
            team_id1: [service_id2, service_id2..]
            team_id2: [...]
            }
        """
        target_url = self.__build_url(DBApi.GET_FIRST_BLOODS % str(tick_id))
        # Profiling, get old time
        old_time = datetime.now()
        first_blood_raw_resp = DBApi._get_json_response(target_url, target_logger=self.log)
        self.log.debug("Time for get_first_bloods api " + str(datetime.now() - old_time))
        team_first_bloods = {}
        if 'first_bloods' in first_blood_raw_resp:
            self.log.info("Got First Blood Response")
            first_blood_info = first_blood_raw_resp['first_bloods']
            for curr_service_id in first_blood_info:
                curr_info = first_blood_info[curr_service_id]
                curr_team_id = str(curr_info["team_id"])
                if curr_team_id not in team_first_bloods:
                    team_first_bloods[curr_team_id] = []
                team_first_bloods[curr_team_id] = list(set(team_first_bloods[curr_team_id] + [curr_service_id]))

        else:
            self.log.error("Invalid Response from DB API for:" + DBApi.GET_FIRST_BLOODS)

        return team_first_bloods

    def get_all_services(self):
        """
        Gets dictionary of all services and their corresponding teams.
        :return: Json object in the form below:
            {
            team_id1: [service_id2, service_id2..]
            team_id2: [...]
            }
        """
        target_url = self.__build_url(DBApi.GET_ALL_SERVICES)
        # Profiling, get old time
        old_time = datetime.now()
        services_raw_resp = DBApi._get_json_response(target_url, target_logger=self.log)
        self.log.debug("Time for get_all_services api " + str(datetime.now() - old_time))
        team_services = {}
        if services_raw_resp is not None:
            self.log.info("Got All Services Response")
            for curr_service_info in services_raw_resp:
                curr_service_id = str(curr_service_info["id"])
                curr_team_id = str(curr_service_info["team_id"])
                if curr_team_id not in team_services:
                    team_services[curr_team_id] = []
                team_services[curr_team_id] = list(set(team_services[curr_team_id] + [curr_service_id]))
        else:
            self.log.error("Invalid Response from DB API for:" + DBApi.GET_ALL_SERVICES)

        return team_services

    def get_all_service_ids(self):
        """
            Gets list of all service ids
        :return: list containing all service ids.
        """

        all_service_ids = set()
        all_team_services = self.get_all_services()
        for curr_team in all_team_services:
            all_service_ids.update(set(all_team_services[curr_team]))
        return list(all_service_ids)

    def get_captured_flag_info(self, tick_id):
        """
        Gets all the captured and lost flags of all the teams
        :param tick_id: Tick id for which the flag information need to be fetched.
        :return: Json object returned by db endpoint.
        """
        target_url = self.__build_url(DBApi.GET_AFFECTED_FLAG_INFO % str(tick_id))
        # Profiling, get old time
        old_time = datetime.now()
        flags_response = DBApi._get_json_response(target_url, target_logger=self.log)
        self.log.debug("Time for get_captured_flag_info api " + str(datetime.now() - old_time))
        if ("captured_flags" not in flags_response) or ("lost_flags" not in flags_response):
            self.log.error("Invalid Response from DB API for:" + DBApi.GET_AFFECTED_FLAG_INFO)
            return {"captured_flags": {}, "lost_flags": {}}

        self.log.info("Got captured flag info Response")
        return flags_response
