#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for scheduler.
WARNING: will alter game state!
"""

__authors__ = "Dhilung Kirat"
__version__ = "0.1.0"

import urllib,json, sys
import logging
from scriptbot import *
import unittest

class DBApiTest(unittest.TestCase):
    def setUp(self):
        self.d = DBClient()
        self.handler = logging.StreamHandler()
        self.handler.setFormatter(logging.Formatter(fmt='%(asctime)s, %(name)s, %(levelname)s, %(message)s',datefmt='%m/%d/%Y %H:%M:%S'))
        self.d.log.addHandler(self.handler)
        self.d.log.setLevel(logging.INFO)

        #from http://db:5000/game/state?secret=...
        #{"service_id": 13, "state": "enabled", "port": 56098, "service_name": "temperature"}
        #{"script_name": "benign.py", "state": "enabled", "is_bundle": 1, "service_id": 13, "script_id": 52, "type": "benign"},
        #{"script_name": "exploit.py", "state": "enabled", "is_bundle": 1, "service_id": 13, "script_id": 53, "type": "exploit"},
        #{"script_name": "getflag.py", "state": "enabled", "is_bundle": 1, "service_id": 13, "script_id": 54, "type": "getflag"},
        #{"script_name": "setflag.py", "state": "enabled", "is_bundle": 1, "service_id": 13, "script_id": 55, "type": "setflag"},


        self.tid = 1
        #setflag
        self.sid = 13

        self.script_id = 55
        self.setflag_script_id = 55
        self.getflag_script_id = 54
        self.exploit_script_id = 53
        self.benign_script_id = 52


        self.flag_id = 'user_name'
        self.cookie = 'password'
        self.result = { 'ERROR':0, 'ERROR_MSG':'Success' }

        self.S = Scheduler()
        self.S.tmp_script_path  = '/tmp/test_scripts'
        self.S.log.addHandler(self.handler)
        self.S.log.setLevel(logging.INFO)
        self.S.test_user = 'test'

    def tearDown(self):
        self.d.log.removeHandler(self.handler)
        self.S.log.removeHandler(self.handler)
        pass

    def test_get_flag(self):
        flag, flag_db_id = self.d.get_flag(self.tid,self.sid)
        self.assertEqual(type(flag_db_id),int)
        self.assertEqual(flag[0],'F')

    def test_set_cookie(self):
        flag, flag_db_id = self.d.get_flag(self.tid,self.sid)
        r = self.d.set_cookie(flag_db_id,self.flag_id,self.cookie)
        self.assertEqual(r['id'],flag_db_id)
        self.assertEqual(r['result'],'success')

    def test_get_current_flag(self):
        flag, flag_db_id = self.d.get_flag(self.tid,self.sid)
        r = self.d.set_cookie(flag_db_id,self.flag_id,self.cookie)
        _flag,_flag_id,_cookie = self.d.get_current_flag(self.tid,self.sid)
        self.assertEqual(flag, _flag)
        self.assertEqual(self.flag_id, _flag_id)
        self.assertEqual(self.cookie, _cookie)

    def test_push_result(self):
        pr = self.d.push_result(1,1,self.result,'test script output')
        self.assertEqual(pr['result'],'success')

    def test_get_script(self):

        sid,name,isb,src = self.d.get_script(self.script_id)

        self.assertIsNotNone(src)

    def test_update_status_db(self):
        r = self.d.set_service_state(self.tid, self.sid, 1, 'No reason')
        self.assertIsNotNone(r)
        self.assertEqual(r['result'],'success')

    def test_update_script_repo(self):
        self.S.load_game_state()
        if os.path.exists(TMP_SCRIPT_PATH):
            shutil.rmtree(TMP_SCRIPT_PATH)
        r = self.S.update_script_repo(self.script_id)
        self.assertTrue(os.path.exists(r))


    def test_update_script(self):
        self.S.load_game_state()
        if os.path.exists(TMP_SCRIPT_PATH):
            shutil.rmtree(TMP_SCRIPT_PATH)
        r = self.S.update_script_repo(self.script_id)
        r = self.S.update_script(self.tid,self.script_id,self.S.scripts[self.script_id]['is_bundle'])
        self.assertTrue(os.path.exists(r))


    def test_script_run(self):
        self.S.load_game_state()
        if os.path.exists(TMP_SCRIPT_PATH):
            shutil.rmtree(TMP_SCRIPT_PATH)

        slock = Event()
        team_id = self.tid
        sandbox_user = self.S.get_sandbox_user_name(self.tid)
        timeout = 300

        ip = '127.0.0.1'

        sp = self.run_script(slock,team_id,sandbox_user,self.setflag_script_id,timeout,'setflag',ip)
        self.assertEqual(sp.out_status[0].value,0)

        sp = self.run_script(slock,team_id,sandbox_user,self.getflag_script_id,timeout,'getflag',ip)
        self.assertEqual(sp.out_status[0].value,0)

        sp = self.run_script(slock,team_id,sandbox_user,self.exploit_script_id,timeout,'exploit',ip)
        self.assertEqual(sp.out_status[0].value,0)

        sp = self.run_script(slock,team_id,sandbox_user,self.benign_script_id,timeout,'benign',ip)
        self.assertEqual(sp.out_status[0].value,0)




    def run_script(self,slock,team_id,sandbox_user,script_id,timeout,script_type,ip,delay=0):

        r = self.S.update_script_repo(script_id)
        script = self.S.scripts[script_id]
        script_path = self.S.update_script(team_id,script_id,script['is_bundle'])
        service_id = script['service_id']
        service_name = self.S.services[service_id]['service_name']
        port = self.S.services[service_id]['port']

        sp = ScriptExecutor(slock, team_id, sandbox_user, script_id, service_id, service_name, timeout, script_type, script_path, ip, port, delay)
        sp.log.addHandler(self.handler)
        sp.log.setLevel(logging.INFO)
        sp.start()
        sp.join()
        return sp



if __name__ == '__main__':
    raw_input('WARNING: will alter game state! \n\nContinue?\n')
    unittest.main()
