import requests
from clint.textui import prompt, puts, colored, validators, columns
from config import config
import sys

univ_name_id=0
univ_url_id=1
prof_name_id=2
prof_email_id=3
prof_url_id=4


def _db_api_post_authenticated(endpoint, args):
    try:
        ret = requests.post(config['DB_API_URL_BASE'] + endpoint, data=args, params={'secret': config['DB_API_SECRET']})
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


def print_tickets_list(tickets):
    teams = _db_api_get_authenticated("/teams/info")['teams']

    puts(colored.blue(columns(["ID#", 4],
                 ["Team Name", 20],
                 ["Subject", 24],
                 ["Status", 7], bold=True)))
    for t in tickets:
        if t['done'] == 1:
            puts(colored.green(columns([str(t['id']), 4],
                                       [teams[str(t['team_id'])]['name'], 20],
                                       [t['subject'], 24],
                                       ['DONE' if t['done'] == 1 else 'OPEN', 7])))
        else:
            puts(colored.red(columns([str(t['id']), 4],
                                     [teams[str(t['team_id'])]['name'], 20],
                                     [t['subject'], 24],
                                     ['DONE' if t['done'] == 1 else 'OPEN', 7])))

def get_open_tickets():
    resp = _db_api_get_authenticated("/tickets/get/open")
    if resp.has_key('tickets'):
        print_tickets_list(resp['tickets'])


def get_all_tickets():
    resp = _db_api_get_authenticated("/tickets/get")
    if resp.has_key('tickets'):
        print_tickets_list(resp['tickets'])


def get_tickets_for_team():
    team_id = prompt.query("Enter the Team ID")
    resp = _db_api_get_authenticated("/tickets/get/" + str(team_id))
    if resp.has_key('tickets'):
        print_tickets_list(resp['tickets'])

def close_ticket():
    ticket_id = prompt.query("Enter the Ticket ID")
    resp = _db_api_post_authenticated("/tickets/close/" + str(ticket_id), {})
    puts(colored.cyan("DONE."))

def get_team_list():
    teams = []
    result = _db_api_get_authenticated("/teams/info")
    for team in result['teams'].keys():
        teams.append(result['teams'][team])
    for team in teams:
        team_email = team['email']
        team_name = team['name']
        meta = _db_api_get_authenticated("/teams/metadata/team/" + str(team['id']))['metadata']
        univ_name = meta[univ_name_id]['content']
        team_id = team['id']
        validated = team['validated']
        line = u"ID %s: %s <%s> (%s) Verified: %s" % (team_id, team_name, team_email, univ_name, validated)
        if validated == "1":
            puts(colored.yellow(line), bold=True)
        else:
            puts(colored.yellow(line), bold=False)


def get_team_info():
    team_id = prompt.query("Enter a team ID")
    try:
        team = _db_api_get_authenticated("/teams/info")['teams'][team_id]
    except:
        puts(colored.red("Couldn't get team info for that team!"))
        return
    print team
    puts(colored.cyan("#####TEAM %s#############" % team_id))
    puts("Name: " + team['name'])
    puts("E-Mail: " + team['email'])
    puts("URL: " + team['url'])
    puts("Country: " + team['country'])
    meta = _db_api_get_authenticated("/teams/metadata/team/" + str(team['id']))['metadata']
    univ_url = meta[univ_url_id]['content']
    if not univ_url.startswith("http"):
        univ_url = "http://" + univ_url
    poc_url = meta[prof_url_id]['content']
    poc_email = meta[prof_email_id]['content']
    poc_name = meta[prof_name_id]['content']
    univ_name = meta[univ_name_id]['content']
    team_id = team['id']
    validated = team['validated']
    puts("Metadata: ")
    puts("School: %s (%s)" % (univ_name, univ_url))
    puts("POC: %s <%s> (%s)" % (poc_name, poc_email, poc_url))


def respond_to_ticket():
    ticket_id = prompt.query("Enter the Ticket ID: ")
    response = prompt.query("Enter the response: ")
    resp = _db_api_post_authenticated("/tickets/response/" + str(ticket_id), {'response': response})
    print resp


def get_ticket_details():
    pass

if __name__ == '__main__':

    while True:
        # Shows a list of options to select from
        inst_options = [{'selector': 'O','prompt': 'Get All Open Tickets', 'return':get_all_tickets},
                        {'selector': 'T','prompt': 'Get Tickets for a Team', 'return':get_tickets_for_team},
                        {'selector': 'A', 'prompt': 'Get All Tickets', 'return': get_all_tickets},
                        {'selector': 'R', 'prompt': 'Respond to a Ticket', 'return': get_all_tickets},
                        {'selector': 'C', 'prompt': 'Close a ticket', 'return': close_ticket},
                        {'selector': 'L', 'prompt': 'Get the team list', 'return': get_team_list},
                        {'selector': 'I', 'prompt': 'Get all team info', 'return': get_team_info},
                        {'selector': "Q", 'prompt': 'Quit', 'return': sys.exit}]
        choice = prompt.options(colored.yellow("Chose an action"), inst_options)
        choice()
