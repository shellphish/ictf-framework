#!/usr/bin/python
# The super-duper-semi-automagic iCTF Academic Validator Professional Elite Edition 2.0!
# by Subwire, with some code borrowed from invernizzi
#
# Run this script to be prompted on how to respond to validation requests
# Say "y" to validate, and send emails
# Say "n" to not validate, and send emails
# Say "d" to fake-delete the team, and send no emails
# Say anything else to ignore and send no emails

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

deleted_list = "deleted.txt"

def delete_team(team_id):
    """ 
    Fake-delete
    """
    with open(deleted_list,"a") as f:
        f.write(str(team_id) + "\n")

def is_deleted(team_id):
    deleted = []
    with open(deleted_list,"r") as f:
        deleted = f.readlines()
        deleted = [int(x) for x in deleted]
    return team_id in deleted

def validate_url(url):
    try:
        parsed = urlparse(url)
    except:
        raise ValueError('Could not parse the URL')
    if parsed.scheme not in ['http', 'https']:
        raise ValueError('The URL scheme should be HTTP(S)')
    domain_or_ip = parsed.hostname
    if ':' in parsed.netloc:
        port = parsed.netloc.rsplit(':', 1)[0]
        if port != '80':
            raise ValueError('Only port 80 allowed.')

    ip = None
    try:
        ip = netaddr.IPAddress(domain_or_ip)
    except netaddr.core.AddrFormatError:
        pass
    if ip:
        raise ValueError('No IP addresses allowed.')
    try:
        ip = netaddr.IPAddress(socket.gethostbyaddr(domain_or_ip)[2][0])
    except:
        try:
            ip = netaddr.IPAddress(socket.gethostbyname(domain_or_ip))
        except:
            raise ValueError('Could not resolve this URL.')
    if ip.is_private() or ip.is_reserved() or ip.is_multicast():
        raise ValidationError(
            'Nice try. We are not that silly!')
    try:
        html = requests.get(
            url,
            timeout=20,
            headers={'User-Agent': USER_AGENT}).text
    except:
        raise
        raise ValueError('Could not fetch url')
    return html


def validate_poc_url(poc_url,poc_name):
    try:
       html = validate_url(poc_url)
    except:
        return False, "POC URL is invalid"
    for token in poc_name.lower().split(' '):
        if not token in html.lower():
            return False, "POC URL is valid, but does not contain the POC's name"
    return True, ""


def validate_univ_url(univ_url,univ_name):
    try:
        html = validate_url(univ_url)
    except:
        return False, "University URL is invalid!"
    for token in univ_name.lower().split(' '):
        if not token in html.lower():
            return False, "University URL is valid, but does not contain the University's name (This might be OK)"
            
    return True, ""


def validate_poc_email(poc_email, univ_url, poc_url):
    try:
        faculty_domain = get_domain(
            poc_email.rsplit('@', 1)[1].strip().lower())
        institution_domain = get_domain(urlparse(univ_url).hostname.lower())
    except Exception as e:
        return False, "POC email is invalid!!"

    if faculty_domain != institution_domain:
        return False, "The POC email does not have the same domain as the university!"
    return True, ""

def autovalidate(univ_name, univ_url, poc_name, poc_url, poc_email):
    print "Autovalidation results:"
    univ_url_good, reason = validate_univ_url(univ_url, univ_name)
    if not univ_url_good:
        print "Univ. URL: [FAIL] " + reason
    else:
        print "Univ. URL: [PASS]"
    poc_url_good, reason = validate_poc_url(poc_url, poc_name)
    if not poc_url_good:
        print "POC URL: [FAIL] " + reason
    else:
        print "POC URL: [PASS]"
    poc_email_good, reason = validate_poc_email(poc_email, univ_url, poc_url)
    if not poc_email_good:
        print "POC Email: [FAIL] " + reason
    else:
        print "POC Email: [PASS]"
    return poc_email_good and poc_url_good and univ_url_good

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


def validate(team_id):
        v_args = {}
        v_args['team_id'] = team_id
        v_args['validated'] = 1
        result2 = _db_api_post_authenticated("/team/update/" + str(v_args['team_id']), v_args)
	return result2

def get_unverified_teams():
    unverified = []
    result = _db_api_get_authenticated("/teams/info")
    for team in result['teams'].keys():
            if result['teams'][team]['validated'] == 0:
                unverified.append(result['teams'][team])
    return unverified

if __name__ == '__main__':
    teams = get_unverified_teams()
    for team in teams:
        if is_deleted(int(team['id'])):
            continue
        if team.has_key('logo') and team['logo']:
            team['logo'] = "[something]"
        for f in team:
            print f, ":", team[f]
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
        print "University name: %s, URL: %s" % (univ_name, univ_url)
        print "Academic POC: %s <%s> URL: %s" % (poc_name, poc_email, poc_url)
        res = autovalidate(univ_name, univ_url, poc_name, poc_url, poc_email)
        a = raw_input("Is this OK? (y/n/d): ").strip()
        if a == 'y':
            print "BOOM.  Approved."
            send_acct_verified_msg([team_email, poc_email], team_name)
            validate(int(team['id']))
        elif a == 'n':
            print "DEEENIED!!"
            send_acct_declined_msg(team_email, team_name)
            
        elif a == 'd':
            print "DELETED!!"
            delete_team(int(team['id']))
