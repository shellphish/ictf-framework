from urllib import urlencode

from flask import Flask, g, jsonify, send_from_directory
from flask_restful import Resource, reqparse, Api, request
from flask.ext.httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from passlib.utils import generate_password
from itsdangerous import (TimedJSONWebSignatureSerializer
                 as Serializer, BadSignature, SignatureExpired)
from flask.ext.cache import Cache
import os
from functools import wraps
import pycountry
import pickle
import json
import requests
import datetime
from lib.file_checker import b64_tgz, b64_png, metadata_dict
from lib.redis_ratelimit import ratelimit
from lib.captcha import generate_captcha, set_captcha, get_captcha
from lib.mailer import send_password_msg, send_verify_msg, send_reset_msg, send_ticket
from config import config as conf
app = Flask(__name__)
auth = HTTPBasicAuth()
api = Api(app)
app.config.update(conf)
cache = Cache(config={'CACHE_TYPE': 'redis'})
cache.init_app(app)


@cache.cached(30, key_prefix='game_state')
def is_game_running():
    resp = _db_api_get_authenticated('/game/state')
    if resp and 'game_id' in resp:
        return True
    else:
        return False


def check_registration_open(func):
    def decor(a):
        if not app.config['registration_open']:
            return {'message':'Registration is closed!'}, 400
        return func(a)
    return decor


def check_submission_open(func):
    def decor(a):
        if not app.config['submission_open']:
            return {'message':'Submission is closed!'}, 400
        return func(a)
    return decor


def check_game_started(func):
    @wraps(func)
    def decor(*args, **kwargs):
        if not is_game_running() and not app.config['game_started']:
            return {'message': 'The game is not running!'}, 400
        return func(*args, **kwargs)
    return decor


def country_code(s):
    try:
        c = pycountry.countries.get(alpha2=s)
    except:
        raise TypeError("Not a valid country code")
    return c.alpha2


def academic_email(s):
    # type drop-in for reqparse for an "academic" email
    # TODO: do this
    return s

app.password_resets = {}

def _db_api_post_authenticated(endpoint, args=None, json=None):
    try:
        print("post_auth_request \n\t{}\n\t{}".format(app.config['DB_API_URL_BASE'] + endpoint + '?' + urlencode({'secret': app.config['DB_API_SECRET']}), args))

        ret = requests.post(app.config['DB_API_URL_BASE'] + endpoint,
                            data=args, json=json, params={'secret': app.config['DB_API_SECRET']})
        print(ret)
        if ret.status_code == 200:
            result_json = ret.json()
            return result_json
        else:
            raise RuntimeError(ret.text)
    except ValueError:
        return
    except:
        raise


def _db_api_get_authenticated(endpoint):
    try:
        ret = requests.get(app.config['DB_API_URL_BASE'] + endpoint, params={'secret': app.config['DB_API_SECRET']})
        if ret.status_code == 200:
            result_json = ret.json()
            return result_json
        else:
            raise RuntimeError(ret.text)
    except ValueError:
        return
    except:
        raise

def generate_auth_token(user_id, expiration=600):
    s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({'id': user_id})


def verify_auth_token(token):
    #print ("serializing {} with {}".format(token,app.config['SECRET_KEY']))
    result = _db_api_post_authenticated("/team/token/login", {"flag_token": token})

    if result is None:
        print("login failure no results from db")
        return None
    if "failure" in result['result']:
        print ("login failure, token probably not found")
        return None 

    try :
        return result['id']
    except Exception as exp:
        print("ERROR not ID in response!!!!\nERROR:{}\nRESULT:{}".format(exp, result))
        return result['result']

    # s = Serializer(app.config['SECRET_KEY'])
    # try:
    #
    #     print("loading token")
    #     data = s.loads(token)
    #     print("token loaded data={}".format(data))
    # except SignatureExpired as se:
    #     print se
    #     return None    # valid token, but expired
    # except BadSignature as bs:
    #     print bs
    #     return None    # invalid token
    # print ("out of try/except")
    # user = data['id']
    # print ("user={}",user)
    # return user

@auth.verify_password
def check_authentication(token, password=None):
    print token
    user = verify_auth_token(token)
    if not user:
        return False
    g.user = user
    return True


class Service(Resource):

    #@check_registration_open
    @auth.login_required
    @check_submission_open
    def post(self):
        # HACK: TODO: FIXME
        #if int(g.user) > 3:
        #    return {'message': 'The service submission system is under construction! Sorry about that! Check back soon!'}, 400
        return {'message': 'Nope.'}, 400
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True, location='json', help='The service name must not be blank')
        parser.add_argument('payload', location='json', required=True, type=b64_tgz,
                            help="Service Bundle must be a Gzipped Tar archive.  When using the API without the python client, this must be base64-encoded.")
        args = parser.parse_args()
        assert (g.user is not None)
        args['team_id'] = g.user
        args['is_bundle'] = True
        args['upload_type'] = 'service'
        result = _db_api_post_authenticated('/upload/new', args)
        if not result:
            return {'message': 'An unknown error occurred contacting the DB.  Please contact the admins!'}, 500
        elif result['result'] != 'success':
            return {'message': 'failed to submit service!  Check your file format and try again'}, 400
        else:
            return {'upload_id': result['upload_id']}

    #@check_registration_open
    @auth.login_required
    def get(self):
        # HACK: TODO: FIXME
        #if int(g.user) > 3:
        #    return {'message': 'The service submission system is under construction! Sorry about that! Check back soon!'}, 400
        # Call the DB and get the user's service status        return {'message': 'Nope.'}, 400
        assert (g.user is not None)
        try:
            result = requests.get(app.config['DB_API_URL_BASE'] + "/upload/status/team/" + str(g.user),
                                  params={'secret': app.config['DB_API_SECRET']})
            result_json = result.json()
            if result_json:
                uploads = result_json['uploads']
                ret = []
                for up in uploads:
                    del up['payload']
                    del up['service_id']
                    del up['upload_type']
                    del up['team_id']
                return result_json
            else:
                return {'message': 'Unable to fetch service submission status.  Please try again!'}, 400
        except:
            return {'message': 'An unknown error occurred.  Please contact the admins!'}, 500

class SSH(Resource):

    @auth.login_required
    @check_game_started
    def get(self):
        try:
            resp = _db_api_get_authenticated("/team/key/get/" + str(g.user))
            if 'ctf_key' in resp:
                return resp, 200
        except:
            pass
        return {'message':'Could not find your SSH keys right now.  Please try again later, or contact the admins via support ticket'}


class VM(Resource):

    @auth.login_required
    @check_game_started
    def get(self):
        try:
            resp = _db_api_get_authenticated("/team/vm/get/" + str(g.user))
            if 'ctf_key' in resp:
                return resp, 200
        except:
            pass
        return {'message':'Could not find your VM information right now.  Please try again later, or contact the admins via support ticket'}


class Dashboard(Resource):

    @auth.login_required
    def post(self):
        return {'message': 'Nope.'}, 400
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True, location='json', help='The service name must not be blank')
        parser.add_argument('archive', location='json', required=True, type=b64_tgz,
                            help="Dashboard Bundle must be a Gzipped Tar archive.  When using the API without the python client, this must be base64-encoded.")
        args = parser.parse_args()
        assert (g.user is not None)
        args['team_id'] = g.user
        args['is_bundle'] = True
        args['upload_type'] = 'service'
        result = _db_api_post_authenticated('/team/dashboard/submit', args)
        if not result:
            return {'message': 'An unknown error occurred contacting the DB.  Please contact the admins!'}, 500
        elif result['result'] != 'success':
            print result
            return {'message': result['reason']}, 400
        else:
            return {'result':'success'}

    @auth.login_required
    def get(self):
        # Call the DB and get the user's service status
        return {'message': 'Nope.'}, 400
        assert (g.user is not None)
        try:
            result = requests.get(app.config['DB_API_URL_BASE'] + "/upload/status/team/" + str(g.user),
                                  params={'secret': app.config['DB_API_SECRET']})
            result_json = result.json()
            if result_json:
                uploads = result_json['uploads']
                ret = []
                for up in uploads:
                    del up['payload']
                    del up['service_id']
                    del up['upload_type']
                    del up['team_id']
                return result_json
            else:
                return {'message': 'Unable to fetch service submission status.  Please try again!'}, 400
        except:
            return {'message': 'An unknown error occurred.  Please contact the admins!'}, 500



class Reset(Resource):

    #@ratelimit(limit=1, per=60 * 1)
    def get(self):
        """
        The verify step in password resetting
        :return:
        """
        parser = reqparse.RequestParser()
        parser.add_argument('key', required=True, help='The key must not be empty')
        args = parser.parse_args()
        reset_args = get_captcha(args['key'])
        if reset_args:
            # Generate a new password
            reset_args['password'] = generate_password(16)
            result = _db_api_post_authenticated("/team/changepass", reset_args)
            if not result or result['result'] != 'success':
                # This one is to a human, don't send JSON
                return "Oops! An error occurred resetting your password.  Contact the admins!", 500
            else:
                print "bar"
                send_reset_msg(reset_args['team_email'], reset_args['team_email'], reset_args['password'])
                return "Your password has been reset.  Please check your email!", 200
        else:
            return "Your reset key is invalid! try reset_password() again to get a new one.", 403
    #@ratelimit(limit=1, per=60)
    def post(self):
        """
        The initial reset step.


        :return:
        """
        parser = reqparse.RequestParser()
        parser.add_argument('team_email', required=True, help='The team email must not be blank')
        args = parser.parse_args()

        # Check if an account actually exists, but don't tell the user!
        result = _db_api_get_authenticated("/team/info/email/" + args['team_email'])
        if not result:
            return jsonify({'message': 'Unable to find team with that email!'}), 400
        else:
            key = generate_password(16)
            reset_args = {}
            reset_args['team_id'] = result['id']
            reset_args['team_email'] = args['team_email']
            set_captcha(key,reset_args)
            url = app.config['MY_URL'] + "/api/reset?key=" + key
            # Send the PW email
            send_verify_msg(args['team_email'], url)
            return jsonify({'message': 'Success'})

class Team(Resource):
    @check_registration_open
    @ratelimit(limit=3, per=60)
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True, help='The team name must not be blank')
        parser.add_argument('team_email', required=True, help='The team email must be valid, and not be blank')
        parser.add_argument('url', required=False, help="A URL for your team's web page")
        parser.add_argument('country', type=country_code, required=True,
                            help='The 2-letter ISO country code must not be blank')
        parser.add_argument('logo', required=False, type=b64_png,
                            help='A logo, in PNG format, 256x256 must be provided')
        parser.add_argument('metadata', required=True, type=dict,
                            help="You must answer the metadata questions.  See /api/metadata")
        args = parser.parse_args()
        captcha, code = generate_captcha()
        # probably need to create pkl file and give the correct user access
        # with open('/tmp/cap.pkl', 'rb') as f:
        #     app.captchas = pickle.load(f)
        #     f.close()

        set_captcha(code, args)
        # with open('/tmp/cap.pkl', 'wb') as f:
        #     pickle.dump(app.captchas, f, pickle.HIGHEST_PROTOCOL)
        #     f.close()

        return {'captcha': captcha}

    @auth.login_required
    def get(self):
        """
        Return the team's status
        :return:
        """
        teams = get_teams_public()
        for team in teams:
            if team['id'] == g.user:
                return {'team': team}, 200
        return {'message': "Error getting team info!"}, 500

@check_registration_open
@app.route('/api/team/verify', methods=['POST'])
@ratelimit(limit=10, per=60)
def verify_captcha():
        parser = reqparse.RequestParser()
        parser.add_argument('response', location='json', required=True, help='The 8-letter uppercase CAPTCHA response must not be blank')
        args = parser.parse_args()
        response = args['response'].strip()
        # with open('/tmp/cap.pkl', 'rb') as f:
        #     app.captchas = pickle.load(f)
        #     f.close()
        acct_args = get_captcha(response)
        if acct_args:
            # Generate a password.
            password = generate_password(16)
            acct_args['team_password'] = password
            result = _db_api_post_authenticated("/team/add", acct_args)
            if not result:
                return jsonify({'message': 'An unknown error occurred.  Try again!'}), 400
            if result['result'] != 'success':
                return jsonify({'message': "Account creation failed because: " + result['fail_reason']}), 400
            team_id = result['team_id']
            md = acct_args['metadata']
            try:
                resp = requests.post(app.config['DB_API_URL_BASE'] + "/team/metadata/add/" + str(team_id),
                                     data={'label_data_json':json.dumps(md)},
                                     params={'secret': app.config['DB_API_SECRET']})
                if resp.status_code != 200:
                    return jsonify({'message': "A weird error occurred on metadata submission.  Please contact the admins!"}),500
            except:
                return jsonify({'message': "A weird error occurred on metadata submission.  Please contact the admins!"}),500

            send_password_msg(acct_args['team_email'], acct_args['team_email'], password)
            #return '{"password": ' + password + '"}'
            return jsonify({'message': 'success'})
        else:
            return '{"message": "Incorrect CAPTCHA response!"}', 400

class SupportTicket(Resource):
    @auth.login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('subject', location='json', required=True,
                            help='The subject (email) must not be blank')
        parser.add_argument('message', location='json', required=True,
                            help='The message must not be blank')
        args = parser.parse_args()
        try:
            info = result = _db_api_get_authenticated("/team/info/id/" + str(g.user))
        except:
            return {'message' : 'An error occurred getting the team info for this ticket!'}, 500
        ts = str(datetime.datetime.now())
        db_resp = _db_api_post_authenticated("/tickets/add", {'team_id':g.user,'subject':args['subject'],'message':args['message'],'ts':ts})
        if not db_resp.has_key("ticket_id"):
            return {'message':"We couldn't store your ticket! Maybe the DB is down? Check IRC or send an email to ctf-admin@lists.cs.ucsb.edu"} ,500
        ticket_id = db_resp['ticket_id']
        send_ticket(ticket_id, info['name'], info['email'], g.user, args['subject'], ts, args['message'])
        return {'ticket_id':ticket_id}, 200

    @auth.login_required
    def get(self):
        resp = _db_api_get_authenticated("/tickets/get/" + str(g.user))
        return resp

class Token(Resource):
    @ratelimit(limit=10, per=60)
    def post(self):
        """
        This is basically a glorified front-end for the database's user/authenticate method.
        Given a username (email) and password, ask the DB whether or not it's valid.  If so, issue
        a token, which encodes their team_id, and is valid for 24 hours.
        """
        parser = reqparse.RequestParser()
        parser.add_argument('email', location='json', required=True,
                            help='The team username (email) must not be blank')
        parser.add_argument('password', location='json', required=True,
                            help='The team password must be valid, and not be blank')
        args = parser.parse_args()
        # I can just reuse args!
        result = _db_api_post_authenticated("/team/authenticate",args)
        if not result:
            return {'message': 'Error occurred at login.  Go bother the admins!'}, 400
        elif result['result'] != 'success':
            return {'message': 'Invalid username or password'},403
        #elif result['validated'] != 1:
        #    return {'message': 'Your account has not been verified.  Please wait.'}, 400
        else:
            team_id = result['id']
            token = generate_auth_token(team_id, expiration=86400)
            return {'token': token.decode('ascii'), 'duration': 86400}

class Metadata(Resource):

    @check_registration_open
    @ratelimit(limit=10, per=60)
    def get(self):
        result = _db_api_get_authenticated('/teams/metadata/labels')
        return jsonify({'labels': result['result']})
        #return {'label1': "What number am I thinking of?", 'label2': "What does the fox say?"}


class VPN(Resource):

    @auth.login_required
    def get(self):
        return {'message': 'Nope'}, 400
        try:
            result = _db_api_get_authenticated('/teams/vpnconfig/team/' + str(g.user))
            if not result or not result['result']:
                return {'message':'No VPN configuration found.'}, 404
            result = result['result'][0]
            return {'vpnconfig': result['vpn_config']}
        except:
            raise


@cache.cached(30,key_prefix='flag_ids')
def get_flag_ids(team_id):
    return _db_api_get_authenticated("/flag/latest")['flag_ids']

@cache.cached(120,key_prefix='services')
def get_services():
    return _db_api_get_authenticated("/services")

# This function separated for caching
@cache.cached(120,key_prefix='vteams')
def get_verified_teams():
    verified = []
    result = _db_api_get_authenticated("/teams/info")
    for team in result['teams'].keys():
            if result['teams'][team]['validated'] == 1:
                verified.append(result['teams'][team])
    return verified

# This function separated for caching
@cache.cached(120,key_prefix='vteamspublic')
def get_verified_teams_public():
    verified = []
    result = _db_api_get_authenticated("/teams/publicinfo")
    teamlist = result['teams'].values()
    for team in teamlist:
        if team['validated'] == 1:
            verified.append(team)
    return verified

# This function separated for caching
@cache.cached(120,key_prefix='teamspublic')
def get_teams_public():
    verified = []
    result = _db_api_get_authenticated("/teams/publicinfo")
    teamlist = result['teams'].values()
    return teamlist

class Teams(Resource):

    @cache.cached(120)
    @auth.login_required
    @check_game_started
    def get(self):
        return {'teams':get_teams_public()}

def get_enabled_services():
    svcs = get_services()['services'].values()
    enabled_svcs = filter(lambda x: x['state'] == 'enabled', svcs)
    return enabled_svcs


class Services(Resource):

    @auth.login_required
    @cache.cached(120)
    @check_game_started
    def get(self):
        #if not app.config['game_started']:
        #    return jsonify({'message':'Game not started!'}), 400
        enabled_svcs = get_enabled_services()
        return jsonify({'services': enabled_svcs})


class Targets(Resource):
    @auth.login_required
    @check_game_started
    def get(self, service_id):
        team_id = g.user
        flag_ids = get_flag_ids(team_id)
        teams = self._get_teams()
        svcs = get_enabled_services()
        port = 0
        try:
            port = filter(lambda x: x['service_id'] == service_id, svcs)[0]['port']
        except:
            return jsonify({'message': 'Unknown service'}), 404
        targets = []
        for team in teams:
            if str(team['id']) == str(g.user):
                continue
            target = {}
            target['team_name'] = team['name']
            target['hostname'] = "team%d" % team['id']
            target['port'] = port
            team_flag_ids = flag_ids[str(unicode(team['id']))]
            if not team_flag_ids.has_key(str(service_id)):
                continue
            target['flag_id'] = team_flag_ids[str(service_id)]
            targets.append(target)
        return jsonify({'targets':targets})

    def _get_teams(self):
        """
        Return a list of teams. Can be overriden by a subclass.
        """

        return get_teams_public()



class AttackUpTargets(Targets):
    """
    Targets class specilized for the attack-up game setting.
    """

    def _get_teams(self):
        """
        Return a list of teams. All the teams returned by this method are
        either the top N teams (when the current team is among them), or
        all teams ahead of the current team.
        """
        # TODO
        return get_teams_public()


class Tick(Resource):

    @check_game_started
    @auth.login_required
    def get(self):
        try:
            res = _db_api_get_authenticated("/game/tick")
            return jsonify(res)
        except Exception as exp:
            return jsonify(exp)

# Please don't take this out.
if app.config['SECRET_KEY'] == "dont tell anyone" or app.config['SECRET_KEY'] == "{{ ICTF_TI_SECRET_KEY }}":
    raise RuntimeError("You might want to check Step 2 under Manual Installation in the README.md. Your teaminterface will be insecure otherwise!")

class TestVMBundle(Resource):

    @auth.login_required
    def get(self):
        return {'message': 'Nope.'}, 400
        fname = "team_" + str(g.user) + ".tar"
        dir = app.config['test_vm_bundles_dir']
        return send_from_directory(dir, fname, as_attachment=True)


class VMBundle(Resource):

    @auth.login_required
    def get(self):
        return {'message': 'Nope.'}, 400
        fname = "team_" + str(g.user) + ".tar.7z"
        dir = app.config['real_vm_bundles_dir']
        return send_from_directory(dir, fname, as_attachment=True)


class Flag(Resource):

    @check_game_started
    @auth.login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('flags', location='json', type=list, required=True, help='The flags must not be empty')
        args = parser.parse_args()
        print "TIARGS={}".format(repr(args))
        results = {}
        valid_flags = []
        for flag in args['flags']:
            if not (isinstance(flag,str) or isinstance(flag,unicode)):
                print "Type of flag is ", type(flag), repr(flag)
                results[flag] = 'notaflag'
                continue
            if len(valid_flags) >= 100:
                print("Team {} tried to submit more than 100 flags!".format(request.authorization))
                results[flag] = 'too_many_flags'
                continue

            valid_flags.append(flag)

        json_data = {}
        json_data['team_id'] = g.user
        json_data['submitted_flags'] = valid_flags
        json_data['attack_up'] = "true" if 'attack_up' in app.config and app.config['attack_up'] else "false"
        submission_results = _db_api_post_authenticated("/flag/submit_many", json=json_data)
        for i in range(len(valid_flags)):
            results[valid_flags[i]] = submission_results[i]['result']

        results = [results[f] for f in args['flags']]

        return results


class Game(Resource):

    @check_game_started
    @auth.login_required
    #@ratelimit(300)
    @cache.cached(timeout=50)
    def get(self):
        """
        Frontend for the /api/status route

        Gets a ton of info from the DB, bundles it up, and returns it

        WARNING: MUST BE CACHED, VERY HEAVY ON THE DB

        """
        ret = {}
        try:
            result1 = _db_api_get_authenticated('/services/exploited')
            ret.update(result1)
            result2 = _db_api_get_authenticated('/scores')
            ret.update(result2)
            result3 = _db_api_get_authenticated('/scores/firstbloods')
            ret.update(result3)
            result4 = _db_api_get_authenticated('/services/states')
            ret.update(result4)
            result5 = get_verified_teams_public()
            ret.update({'teams':result5})
            result6 = _db_api_get_authenticated('/game/tick')
            ret.update({'tick':result6})
            return ret
        except:
            raise
            return {'message':"Error getting data!"}, 400


class Vote(Resource):
    @auth.login_required
    #@check_game_started
    def post(self):
        """
        Handles service voting.
        """
        return {'message': 'Nope.'}, 400
        parser = reqparse.RequestParser()
        parser.add_argument('service_1', required=True, location='json', help='The service name must not be blank')
        parser.add_argument('service_2', required=True, location='json', help='The service name must not be blank')
        parser.add_argument('service_3', required=True, location='json', help='The service name must not be blank')
        args = parser.parse_args()
        assert (g.user is not None)
        args['team_id'] = g.user
        result = _db_api_post_authenticated("/team/vote/services", args)
        if result['result'] == 'failure':
            print result
            return {'message':'An error occurred casting your vote.  Please contact the admins!'}, 500



@app.route('/')
def indexpage():
    """
    Display the main index page
    :return:
    """
    return """
    <html>
    <head>
        <title>Welcome to iCTF!</title>
    </head>
    </body>
        <h1>API server for the ictf</h1>

        </body>
    </html>
    """


api.add_resource(Token, '/api/login')
api.add_resource(Team, '/api/team')
api.add_resource(Reset, '/api/reset')
api.add_resource(Service, '/api/service')
api.add_resource(Metadata, '/api/metadata')
api.add_resource(VPN, "/api/vpnconfig")
api.add_resource(Vote, "/api/vote")
api.add_resource(Dashboard,"/api/dashboard")
api.add_resource(Game,"/api/status")
api.add_resource(Flag,"/api/flag")
api.add_resource(VMBundle,"/api/vmbundle")
api.add_resource(TestVMBundle,"/api/testvmbundle")
api.add_resource(Targets,'/api/targets/<int:service_id>')
api.add_resource(Services,"/api/services")
api.add_resource(Tick,'/api/status/tick')
api.add_resource(SupportTicket,"/api/ticket")
api.add_resource(Teams,'/api/teams')
api.add_resource(SSH, '/api/ssh')
api.add_resource(VM, '/api/vm')


if __name__ == '__main__':
    app.run(debug=True)
