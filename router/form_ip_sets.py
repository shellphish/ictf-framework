#!/usr/bin/env python3

import sys
from os.path import abspath, join as join_path, dirname, exists
from os import chmod
from shutil import chown
from subprocess import Popen, PIPE
from time import sleep

sys.path.append(abspath(join_path(dirname(__file__), '..')))
from common.db_client import DBClient, DBClientError

IP_SETS_SCRIPT = "/tmp/ipsets.dat"


# make sure all ipsets exist for teams,
#proc = Popen(['/opt/ictf/router/create_ip_sets.sh'], stdout=PIPE, stderr=PIPE)

proc = Popen(["sudo", "ipset", "restore", "-f", "/opt/ictf/router/create_ip_sets.dat"], stdout=PIPE, stderr=PIPE)
stdout, stderr = proc.communicate()
if stdout:
    print(stdout.decode('utf-8'))
if stderr:
    print(stderr.decode('utf-8'))

# hopefully this limits the number of times this runs
if not exists(IP_SETS_SCRIPT):

    proc = Popen(["sudo", "service", "iptables-persistent", "restart"], stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    if stdout:
        print(stdout.decode('utf-8'))
    if stderr:
        print(stderr.decode('utf-8'))


# loop until can make DB connection
while True:
    try:
        dbclient = DBClient()
        break
    except Exception as ex:
        print("ERROR with getting to DB {}".format(ex))
        if not exists("/opt/ictf/secrets/database-api/db_pub_ip"):
            print("Database file not found !!")
    sleep(20)

# get's teams and IPs
hosts = open("/etc/hosts","r").read().split("\n")
team_ips = dict()
for line in hosts:
    if line.find("team") > -1:
        ts = line.split()
        team_ips[ts[1]] = ts[0]

team_rank = ""
while True:
    try:
        new_team_rank = dbclient.get_scores()
    except DBClientError as dbce:
        print(dbce)
        sleep(30)
        continue

    # if team rankings are different then let's reconfigure b/c a tick has occured
    if new_team_rank != team_rank:
        team_rank = new_team_rank
        print("TEAMS ORDER is Different, reconfiguring")
        # Create a bash script to run all ipset commands
        # then call the script.
        inaccessible_teams = list()
        out = open(IP_SETS_SCRIPT , "w")
        out.write("create -exist tempset hash:ip\n")
        out.write("destroy tempset \n")
        #out.write("#!/usr/bin/env bash\n")

        print (team_rank)
        # teams are ranked in ascending order (by total_points), i.e., from last to first
        # the sets denote the packets to be DROPPED
        for t in team_rank:
            team_id = "team{}".format(t[0])
            if team_id == "team99999":
                continue
            out.write("######### Creating ipset for {} ######### \n".format(team_id))
            out.write("create tempset hash:ip\n")
            # out.write("ipset -exist create {} hash:ip\n".format(team_id))

            if len(inaccessible_teams) > 0:
                for inat in inaccessible_teams:
                    out.write("add tempset {}\n".format(inat))

            # does not ever drop packets for top 5 teams, they can freely attack one another.
            # if the total number of teams minus the number being ignored is more than CUT OFF
            # then the ip should be added to the inaccessible b/c too weak to be attacked by
            # badass teams.
            if len(inaccessible_teams) == 0 or (len(team_rank) - len(inaccessible_teams)) > 10:
                inaccessible_teams.append(team_ips[team_id])

            out.write("swap {} tempset \n".format(team_id))
            out.write("destroy tempset \n")

        out.close()

        chmod(IP_SETS_SCRIPT, 0o0774)
        chown(IP_SETS_SCRIPT, user="ubuntu", group="ubuntu")

        proc = Popen(["sudo","ipset","restore","-f",IP_SETS_SCRIPT], stdout=PIPE, stderr=PIPE)

        stdout, stderr = proc.communicate()

        if stdout:
            print(stdout.decode('utf-8'))
        if stderr:
            print(stderr.decode('utf-8'))

        print("PACKETS RECONFIGURED!")

    sleep(10)



