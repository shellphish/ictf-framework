import os
import re
import sys
import logging
import shutil

from utils import ArgParser
from utils import status
from utils import gamepath
from utils import create_ssh_key
from utils import bundle

from vm import create_org
from vm import create_team

def main(argv):
    arg_parser = ArgParser()
    args = arg_parser.parse(argv)
    game_hash = args.game_hash
    # Set up logging
    logging.basicConfig(filename=os.path.join(args.log_path, 'game_{}_vms.log'.format(game_hash)),
                        level=logging.DEBUG, format='%(asctime)s %(message)s')

    try:
        game = args.game
        status(game_hash, "Started creating VMs", args.remote)

        assert re.match(r'[a-zA-Z0-9]+\Z', game_hash)
        status(game_hash, "PENDING", args.remote)

        game_name = game['name'];
        assert re.match(r'[a-zA-Z0-9 _-]+\Z', game_name)
        teams = game['teams']
        services = [s['name'] for s in game['services']]

        logging.info("Name: {}".format(game_name))
        logging.info("Teams: {}".format(teams))
        logging.info("Services: {}".format(services))
        assert game['num_services'] == len(game['services'])
        assert game['num_services'] == len(services)
        assert len(teams) < 200 # Avoid an IP conflict with the organization VM (10.7.254.10)

        game_dir = gamepath(args.output_path, game_hash, clean_up=True)
        root_key_path = os.path.join(game_dir, "root_key")
        root_public_key = create_ssh_key(root_key_path)

        create_org(args.output_path, game_hash, game_name, teams, services, root_key_path, args.remote)

        for team_id, team in enumerate(teams, start=1):
            team_public_key = create_ssh_key(game_dir+"/team{}_key".format(team_id))
            create_team(args.output_path, game_hash, team_id, root_public_key, team_public_key, team['password'], services, args.remote)

        bundle(game_hash, "Organization", "root_key", game_hash, args.output_path, args.remote)
        for team_id, team in enumerate(teams, start=1):
            team_hash = team['hash']
            bundle(game_hash, "Team{}".format(team_id), "team{}_key".format(team_id), team_hash, args.output_path, args.remote)

        status(game_hash, "Cleaning up the build")
        gamepath(args.output_path, game_hash, clean_up=True)

        status(game_hash, "READY")

    except:
        status(game_hash, "An error occurred. Contact us and report game {}".format(game_hash))
        status(game_hash, "ERROR")
        logging.exception("Exception")
        #os.system("echo 'Creation for {} failed, see the log in /tmp' | mail -s 'Error creating game {}' root".format(game_hash,game_hash))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
