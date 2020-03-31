import os
import subprocess
import logging
import copy

import scriptbot

from database_mockup import DatabaseMockup
from registry_mockup import RegistryMockup

test_service_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../test_service/simplecalc/")

l = logging.getLogger('scriptbot.TestScriptbot')
ch = logging.StreamHandler()
l.setLevel(logging.DEBUG)
l.addHandler(ch)

class TestingException(Exception):
    """
    Exception raised when we want to inject a fault in our tests
    """

class TestScriptbot:

    def __init__(self):
        self.game_state = None
        self.db_client = None
        self.registry_client = None
        self.scheduler = None
    
    def _raise_testing_exception(self):
        raise TestingException

    def _raise_registry_exception(self, *args, **kwargs):
        raise scriptbot.RegistryClientPullError

    def setup(self):
        
        self.db_client = DatabaseMockup()
        self.registry_client = RegistryMockup()

        self.scheduler = scriptbot.Scheduler(
            db_client=self.db_client,
            registry_client=self.registry_client,
            status_path="/tmp/scriptbot_status.json",
            is_synchronous=True
        )

    def test_setflag(self):
        self.db_client.scripts = [
            {"upload_id": 1, "script_id": 2, "script_name": "ictf-test-simplecalc-scripts", "should_run": 1 , "type": "setflag", "service_id": 1}
        ]
        self.db_client.scripts_to_run = [
            {"id" : 1, "script_id" : 2, "against_team_id": self.db_client.TEST_TEAM_ID, "tick_id" : 1 }
        ]
        state = self.db_client.get_game_state()
        self.scheduler.execute_round(state)
        assert self.scheduler.status['last_error'] is None

    def test_getflag(self):
        self.db_client.scripts = [
            {"upload_id": 1, "script_id": 3, "script_name": "ictf-test-simplecalc-scripts", "should_run": 1 , "type": "setflag", "service_id": 1},
            {"upload_id": 1, "script_id": 2, "script_name": "ictf-test-simplecalc-scripts", "should_run": 1 , "type": "getflag", "service_id": 1}
        ]
        self.db_client.scripts_to_run = [
            {"id" : 1, "script_id" : 3, "against_team_id": self.db_client.TEST_TEAM_ID, "tick_id" : 1 },
            {"id" : 2, "script_id" : 2, "against_team_id": self.db_client.TEST_TEAM_ID, "tick_id" : 1 }
        ]
        state = self.db_client.get_game_state()
        self.scheduler.execute_round(state)
        assert self.scheduler.status['last_error'] is None

    def test_fail_load_game_state(self):
        state = self.db_client.get_game_state()
        # Inject the fault in this method
        self.db_client.get_game_state = self._raise_testing_exception
        self.scheduler.execute_round(state)
        assert "An unexpected exception occurred when updating game state" in self.scheduler.status['last_error']


    def test_fail_load_scripts_to_run(self):
        state = self.db_client.get_game_state()
        # Inject the fault in this method
        self.db_client.get_scripts_to_run = self._raise_testing_exception
        self.scheduler.execute_round(state)
        assert "An unexpected exception occurred in Scheduler thread" in self.scheduler.status['last_error']

    def test_fail_update_script(self):
        self.db_client.scripts = [
            {"upload_id": 1, "script_id": 2, "script_name": "ictf-test-simplecalc-scripts", "should_run": 1 , "type": "setflag", "service_id": 1}
        ]
        self.db_client.scripts_to_run = [
            {"id" : 1, "script_id" : 2, "against_team_id": self.db_client.TEST_TEAM_ID, "tick_id" : 1 }
        ]
        state = self.db_client.get_game_state()
        # Inject the fault in this method
        self.registry_client.pull_new_image = self._raise_registry_exception
        self.scheduler.execute_round(state)
        assert "An unexpected exception occurred when pulling from registry and updating script" in self.scheduler.status['last_error']