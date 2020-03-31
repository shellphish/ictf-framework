import unittest
from random import random
from funkload.FunkLoadTestCase import FunkLoadTestCase
from webunit.utility import Upload
from funkload.utils import Data

class Stress_Test(FunkLoadTestCase):
    def setUp(self):
        self.server_url = self.conf_get('main', 'url')
        self.setBasicAuth('team@shellphish.net', 'testing!')
        pass

    def test_simple(self):
        # The description should be set in the configuration file
        server_url = self.server_url
        # begin test ---------------------------------------------
        nb_time = self.conf_getInt('test_simple', 'nb_time')
        ap_list = self.conf_get('test_simple', 'ap_list').split(",")
        #print "aplist,", ap_list
        for i in range(nb_time):
            for ap in ap_list:
                self.get('https://'+server_url+ap, description='Get URL')
        # end test ------------
