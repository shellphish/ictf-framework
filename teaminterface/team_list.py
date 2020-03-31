import requests
import sys
from config import config
from lib.mailer import *
from urlparse import urlparse
import netaddr
import socket
from lib.domain import get_domain
USER_AGENT = '''Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:36.0) Gecko/20100101 Firefox/36.0'''

# Which metadata ids have the needed info?
univ_name_id=0
univ_url_id=1
prof_name_id=2
prof_email_id=3
prof_url_id=4

def _db_api_get_authenticated(endpoint):
    try:
        ret = requests.get(config['DB_API_URL_BASE'] + endpoint, params={'secret': config['DB_API_SECRET']})
        if ret.status_code == 200:
            result_json = ret.json()
            return result_json
        else:
            raise RuntimeError(ret.text)
    except ValueError:
        return 
    except:
        raise


def _db_api_post_authenticated(endpoint, args):
    try:
        ret = requests.post(config['DB_API_URL_BASE'] + endpoint, params={'secret': config['DB_API_SECRET']}, data=args)
        if ret.status_code == 200:
            result_json = ret.json()
            return result_json
        else:
            raise RuntimeError(ret.text)
    except ValueError:
        return
    except:
        raise


def get_teams():
    teams = []
    result = _db_api_get_authenticated("/teams/info")
    for team in result['teams'].keys():
        teams.append(result['teams'][team])
    return teams

if __name__ == '__main__':
    teams = get_teams()
    for team in teams:
        team_email = team['email']
        team_name = team['name']
        meta = _db_api_get_authenticated("/teams/metadata/team/" + str(team['id']))['metadata']
        # Get the stuff, do the autovalidate
        univ_url = meta[univ_url_id]['content']
        if not univ_url.startswith("http"):
            univ_url = "http://" + univ_url
        poc_url = meta[prof_url_id]['content']
        poc_email = meta[prof_email_id]['content']
        poc_name = meta[prof_name_id]['content']
        univ_name = meta[univ_name_id]['content']
        team_id = team['id']
        validated = team['validated']
        print u"ID %s: %s <%s> (%s) Verified: %s" % (team_id, team_name, team_email, univ_name,validated)
        #print poc_name, poc_email
        #print team
