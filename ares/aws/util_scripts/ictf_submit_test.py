# IPython log file
import sys
import time
import subprocess
from swpag_client import Team
from collections import Counter
import re
import json
from os.path import abspath, basename, dirname, join
from multiprocessing import Pool

NUM_TEAMS = 30

game_config_path = abspath(join(dirname(__file__), '..', '..', '..', 'game_config.json'))
with open(game_config_path, 'r') as f:
    game_config = json.load(f)

team_name = sys.argv[1] if len(sys.argv) > 1 else 'Shellphish'
team_tokens = {t['name']: t['flag_token'] for t in game_config['teams']}
team_token = team_tokens[team_name]
t = Team('http://52.53.64.114/', team_token)

SUBMITTED_FLAGS = {i: set() for i in range(NUM_TEAMS)}


def do_submit(team_id):
    with open('/tmp/flags_{}'.format(team_id), 'rb') as f:
        s = f.read()
    flags = re.findall(b'FLG.{13}', s)
    flags = [f.decode() for f in flags]
    flags = [f for f in flags if f not in SUBMITTED_FLAGS[team_id]]
    len_non_unique = len(flags)
    flags = list(set(flags))
    print("Unique: {}/{}".format(len(flags), len_non_unique))
    results = []
    for i in range(0, len(flags), 20):
        results.extend(t.submit_flag(flags[i:i+20]))
    SUBMITTED_FLAGS[team_id].update(flags)
    return results

def run_and_submit_team_flags(team_id):
    subprocess.check_call('ssh -F ssh_config teamvm%d "sudo grep -Eran \'FLG.{13}\' /opt/ictf/services/ > /tmp/flags"' % (i+1), shell=True)
    subprocess.check_call('scp -F ~/lukas/ctf/authoring/ictf-framework/ares/aws/ssh_config teamvm{}:/tmp/flags /tmp/flags_{}'.format(team_id+1, team_id), shell=True)
    result = Counter(do_submit(team_id))
    return team_id, result
    


pool = Pool(8)
while True:
    for i, r in pool.imap_unordered(run_and_submit_team_flags, range(NUM_TEAMS)):
        print("TEAM {}: {}".format(i, r))

    print("Sleeping ...")
    time.sleep(1)
    
