"""
Written by subwire and the iCTF team, 2019
# The TeamInterface game client

This client lets you interact with the game, including
getting the game status, obtaining a list of potential targets, and 
submitting flags.

To get started, you will have received a "flag token" with your game registration.
You may also need to know the URL of your game's "team interface".
Note that for some games (e.g., iCTF) this will be automatically discovered for you.
You will also need access to your team's virtual machine, on which you should run the client.

You are heavily encouraged to use this library to help you automate the exploitation of services
and the submission of flags.

You can now do the following:

>>> from teaminterface_client import Team
>>> t = Team("http://your.team.interface.hostname/", "your_flag_token_here")

With this team object, you can then get the info to login to your machine:

>>> t.get_vm()

Get game status information:

>>> t.get_game_status()

This includes information on scores, teams, services, and timing information regarding the game's "ticks".

Your first task will be to explore the game services which you must attack and defend, and find exploits
You will see them on your VM's filesystem, but to get a list of services with descriptions, you can run
>>> t.get_service_list()

This will produce a list of services, including the "service ID" of the service.

Once you have reverse-engineered a service, and developed your new leet exploit, you then need to
obtain a list of the other teams, which you can attack.
However, each service hosted by each team may contain multiple flags; in order to prove your 
control over the vulnerable service, you must find the _correct_ flag, which the game tells you to find.
Each flag is associated with a "flag ID", which gets cycled each game tick (see the game rules for
more details).  Your exploit needs to then obtain the flag associated with a given flag ID, hosted
hosted by a given opponent team.

With the service ID obtained above, you can then do the following:

>>> t.get_targets(service_id)

This will return a list of the teams' IP addresses, port numbers, and flag IDs.

Finally, you need to capture and submit some flags!
Once you've pwned the service, and captured the flag, all you need to do is:

>>> t.submit_flag("FLGxxxxxxxxxxxxx")

You can also submit a lot of flags at once:

>>> t.submit_flag(["FLGxxxxxxxxxxxxx", "FLGyyyyyyyyyyyyy", ...])

You'll get a status code (or a list of status codes) in return.

The client can provide a wealth of information on the game, which is discussed in the documentation.

Happy hacking!

- the iCTF team

"""
from builtins import input
import json
import requests
import base64
import random
from functools import wraps

def flag_token(func):
    @wraps(func)
    def decor(self, *args, **kwargs):
        if not self._flag_token:
            raise RuntimeError("You need a flag token for this")
        return func(self, *args, **kwargs)
    return decor

class Team(object):
    """
    This object represents a logged-in iCTF team.
    This object can be used to perform actions on behalf of the team, such as submitting game artifacts
    """

    def __init__(self, game_url, flag_token=None):
        self._flag_token = flag_token
        self._login_token = None
        self.game_url = game_url if game_url[-1] == '/' else game_url + '/'

    def __str__(self):
        return "<Team %s>" % self._token

    def _post_json(self, endpoint, j, token):
        # EDG says: Why can't Ubuntu stock a recent version of Requests??? Ugh.
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        resp = requests.post(self.game_url + endpoint, auth=(token, ""), data=json.dumps(j), headers=headers)
        try:
            js = resp.json()
            return js, resp.status_code
        except Exception as e:
            return e, resp.status_code

    def _get_json(self, endpoint, token):
        assert (token is not None)
        resp = requests.get(self.game_url + endpoint, auth=(token, ""))
        try:
            js = resp.json()
        except Exception as e:
            return e, resp.status_code
        return resp.json(), resp.status_code

    def _get_large_file_authenticated(self, endpoint, save_to, token):
        r = requests.get(self.game_url + endpoint, auth=(self.token, ""), stream=True)
        if r.status_code != 200:
            raise RuntimeError("Error downloading file!")
        with open(save_to, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)

    def get_team_list(self):
        """
        Return the list of teams!
        """
        token = self._flag_token if self._flag_token else self._login_token
        resp, code = self._get_json("api/teams", token)
        if code == 200:
            return resp['teams']
        else:
            if isinstance(resp,dict):
                raise RuntimeError(resp['message'])
            else:
                raise RuntimeError("An unknown error occurred getting the team list")

    def get_vm(self):
        """
        Return the vm info about your team, ip address and ssh keys.
        """
        token = self._flag_token if self._flag_token else self._login_token
        resp, code = self._get_json("api/vm", token)
        if code == 200:
            return resp
        else:
            if isinstance(resp,dict):
                raise RuntimeError(resp['message'])
            else:
                raise RuntimeError("An unknown error occurred getting the VM information for the team")

    def get_tick_info(self):
        """
        Return information about the current game "tick".

        The iCTF game is divided into rounds, called "ticks".  Scoring is computed at the end of each tick.
        New flags are set only at the next tick.

        If you're writing scripts or frontends, you should use this to figure out when to
        run them.

        The format looks like:
        {u'approximate_seconds_left': <int seconds>,
        u'created_on': Timestamp, like u'2015-12-02 12:28:03',
        u'tick_id': <int tick ID>}
        """
        token = self._flag_token if self._flag_token else self._login_token
        resp, code = self._get_json("api/status/tick", token)
        if code == 200:
            return resp
        else:
            if isinstance(resp,dict):
                raise RuntimeError(resp['message'])
            else:
                raise RuntimeError("An unknown error occurred getting the tick info.")

    @flag_token
    def submit_flag(self, flags):
        """
        Submit a list of one or more flags
        note: Requires a flag token
        :param flags: A list of flags
        :return: List containing a response for each flag, either:
        	"correct" | "ownflag" (do you think this is defcon?)
                      | "incorrect"
                      | "alreadysubmitted"
                      | "notactive",
                      | "toomanyincorrect",

        """
        if not isinstance(flags,list):
            raise TypeError("Flags should be in a list!")
        resp, code = self._post_json("api/flag", {'flags': flags}, self._flag_token)
        if code == 200:
            return resp
        else:
            if isinstance(resp,dict):
                raise RuntimeError(resp['message'])
            else:
                raise RuntimeError("An unknown error occurred submitting flags.")

    def get_targets(self, service):
        """
        Get a list of teams, their hostnames, and the currently valid flag_ids.
        Your exploit should then try to exploit each team, and steal the flag with the given ID.

        You can/should use this to write scripts to run your exploits!

        :param service: The name or ID of a service (see get_service_list() for IDs and names)
        :return: A list of targets:
            [
                {
                    'team_name' : "Team name",
                    'hostname' : "hostname",
                    'port' : <int port number>,
                    'flag_id' : "Flag ID to steal"
                },
                ...
            ]
        """
        token = self._flag_token if self._flag_token else self._login_token
        service_id = None
        if isinstance(service,str):
            services = self.get_service_list()
            svc = filter(lambda x: x['service_name'] == service, services)
            if not svc:
                raise RuntimeError("Unknown service " + service)
            service_id = int(svc[0]['service_id'])
        else:
            service_id = service
        resp, code = self._get_json("api/targets/" + str(service_id), token)
        if code == 200:
            return resp['targets']
        else:
            if isinstance(resp,dict):
                raise RuntimeError(resp['message'])
            else:
                raise RuntimeError("Something went wrong getting targets.")

    def get_service_list(self):
        """
        Returns the list of services, and some useful information about them.

        The output will look like:

        [
            {
                'service_id' : <int service id>,
                'team_id' : <team_id which created that service>
                'service_name' : "string service_name",
                'description' : "Description of the service",
                'flag_id_description' : "Description of the 'flag_id' in this service, indicating which flag you should steal",
                'port' : <int port number>
            }
        ]
        """
        token = self._flag_token if self._flag_token else self._login_token
        resp, code = self._get_json("api/services", token)
        if code == 200:
            return resp['services']
        else:
            if isinstance(resp,dict):
                raise RuntimeError(resp['message'])
            else:
                raise RuntimeError(repr(resp))

    def get_game_status(self):
        """
        Return a dictionary containing game status information.
        This will include:
            - The scores of all teams
            - Game timing information
            - Information about services, including their status, number of exploitations, etc

        This API is suitable for use in the creation of frontends.

        The return value is a large dictionary, containing the following:
        - 'teams' : Basic team info, name, country, latitude, longitude, etc
        - 'service_states': For each team and service, provides its "state" (up/down/etc)
        - 'exploited_services': For each service that has been exploited, list who exploited it
        - 'first_bloods': For each service, which team scored on it first (they get extra points!)
        - 'scores': The scoring data for each team.
        - 'tick': Info about the game's current "tick" -- see get_tick_info()
        It will look something like:

        {
            'teams' :
                {
                    <team_id> :
                        {
                            'country' : "ISO 2 letter country code",
                            'logo' : <base64 logo>,
                            'name' : "1338-offbyone"
                            'url' : "http://teamurl.here"
                        }					}
                }
            'exploited_services' :
                {
                    <service_id> :
                        {
                            'service_name' : "string_service_name",
                            'teams' :
                                [
                                    {
                                        'team_id' : <team_id>,
                                        'team_name' : "string team name"
                                    },
                                    ...
                                ],
                            'total_stolen_flags' : <integer>
                        }
                }
            'service_states' :
                {
                    <team_id> :
                        {
                            <service_id> :
                                {
                                    'service_name' : "string_service_name"
                                    'service_state' : "untested" | "up" | "down"
                                }
                    }
                },
            'first_bloods' :
                {
                    <service_id> :
                        {
                            'created_on' : Timestamp eg. '2015-12-02 10:57:49',
                            'team_id' : <ID of exploiting team>
                        }
                },
            'scores' :
                {
                    <team_id> :
                        {
                            'attack_points' : <float number of points scored through exploitation>,
                            'service_points' : <float number of points for having a "cool" service, see rules for details>,
                            'sla' : <float SLA score>
                            'total_points' : <float normalized final score>
                        }
                },
            'tick' :
                {
                    'approximate_seconds_left': <int seconds>,
                    'created_on': Timestamp, like '2015-12-02 12:28:03',
                    'tick_id': <int tick ID>
                }
        }

        """
        token = self._flag_token if self._flag_token else self._login_token
        resp, code = self._get_json("api/status", token)
        if code == 200:
            return resp
        else:
            if isinstance(resp,dict) and 'message' in resp:
                raise RuntimeError(resp['message'])
            else:
                raise RuntimeError("An unknown error occurred contacting the game status! Perhaps try again?")

    def get_team_status(self):
        """
        Get your team's current status
        """
        token = self._flag_token if self._flag_token else self._login_token
        resp, code = self._get_json("api/team", token)
        if code == 200:
            return resp
