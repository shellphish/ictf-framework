class DatabaseMockup():

    TEST_TEAM_ID = 9999
    FLAG_IDX = 10
    FLAG = "FLGabcdefghijklm"
    # these particular flag_id and secret_token have been set directly in the setflag scripts of the testing service located
    # in <ICTF_ROOT>/test_services/simplecalc/scripts/setflag
    #
    # If for some reason someone needs to change these values here, these same values need to be changed there as well
    FLAG_ID = "someid"
    SECRET_TOKEN = "totallyrandomtoken"

    def __init__(self):
        """
        Let's parametrize the scripts and the scripts to run so we can have different tests
        """
        # Format of scripts: [{"upload_id": 1, "script_id": 2, "script_name": "ictf-test-simplecalc-scritps", "should_run": 1 , "type": "setflag", "service_id": 1}]
        self.scripts = []
        # Format of scripts_to_run: [{"id" : 1, "script_id" : 2, "against_team_id": self.TEST_TEAM_ID, "tick_id" : 1 },]" 
        self.scripts_to_run = []
    
    def get_teams(self):
        """
        Get a dict of all teams from the database backend
        API: /teams/info
        :return: a dict of all team info
        """

        response = {
            "teams":{
                self.TEST_TEAM_ID: { "id": self.TEST_TEAM_ID, "name": "dummy_1", "url": "dummy_url", "country": "ITA", "validated": 1, "academic_team": 1, "email": "dummy1@dummy.com"},
                # 2: { "id": 2, "name": "dummy_2", "url": "dummy_url", "country": "ITA", "validated": 1, "academic_team": 1, "email": "dummy2@dummy.com"},
                # 3: { "id": 3, "name": "dummy_3", "url": "dummy_url", "country": "ITA", "validated": 1, "academic_team": 1, "email": "dummy3@dummy.com"},
            }
        }

        return response['teams']

    def get_game_state(self):
        """
        Get the game state
        API: /game/state
        :return: A huge dict that contains almost everything
        """

        response = {  
            "state_id": 1,
            "game_id": 1,
            "services": [
                {"service_id": 1, "service_name": 'simplecalc', "is_up":1, "port":6666}
            ],
            "scripts": self.scripts,
            "run_scripts": [{"team_id":1,"run_list":[1,2,3,4]}],
            "state_expire": 60,
        }

        return response


    def get_scripts_to_run(self):
        """
        Returns all scripts that needs to be run for current tick.
        API: /scripts/get/torun
        :return: a JSON dictionary that contains all script that needs to be run.
        """
        response = {
            "scripts_to_run": self.scripts_to_run
        }

        return response['scripts_to_run']

    def generate_flag(self, team_id, service_id):
        """
        Generate a flag for a specific team and service, which will be used by setflag script
        API: /flag/latest/team/<int:team_id>/service/<int:service_id>
        :param team_id: ID of the team
        :param service_id: ID of the specific service
        :return: A tuple of (flag_idx, flag), where flag_idx is the ID of the flag in database
        """
        return (self.FLAG_IDX, self.FLAG)


    def set_secret_token(self, flag_idx, flag_id, secret_token):
        """
        Set flag_id and secret_token to a specific flag identified by flag_idx

        API: /flag/set/<int:flag_idx>

        :param flag_idx: The ID of the flag in database.
        :param flag_id: The flag ID
        :param secret_token: The secret_token
        :return: True if successfully updated, False otherwise
        """
        return True

    def push_result(self, execution_id, result, script_output=None):
        """
        Push the result of an executed script to the server

        API: /script/ran/<int:execution_id>

        :param execution_id: ID of the run of the script, as in database
        :param result: Result to push
        :param script_output: Output of the script
        :return: True/False
        """
        return True

    
    def get_current_flag(self, team_id, service_id):
        """
        Get the latest flag for a specific team and service.

        API: /flag/latest/team/<int:team_id>/service/<int:service_id>

        :param team_id: ID of the team
        :param service_id: ID of the specific service
        :return: A tuple of (flag, flag_id, secret_token) if we have a flag, (None, None, None) otherwise
        """
        return (self.FLAG, self.FLAG_ID, self.SECRET_TOKEN)