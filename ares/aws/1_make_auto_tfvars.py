#!/usr/bin/env python
import math

import argparse
import os
import json

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('aws_access_key', type=str, help="Access key for AWS")
    argparser.add_argument('aws_secret_key', type=str, help="Secret key for AWS")
    argparser.add_argument('aws_region', type=str, help="AWS region where to spawn the game")
    argparser.add_argument('game_config_path', type=str, help="Path to the game configuration file")
    argparser.add_argument('-d', '--dev-mode', action='store_true', default=False, help="If set spawn the infrastructure in development mode")
    args = argparser.parse_args()

    with open(args.game_config_path, 'r') as f:
        game_config = json.load(f)

    vars = {
        'access_key':       args.aws_access_key,
        'secret_key':       args.aws_secret_key,
        'region':           args.aws_region,
        'game_config_file': args.game_config_path,
        'services_path':    game_config["service_metadata"]["host_dir"],
        'teams_num':        len(game_config["teams"]),
        'scriptbot_num':    int(math.ceil(len(game_config["teams"]) / 10.0))
    }

    if args.dev_mode:
        vars.update({
            "database_instance_type": 't2.small',
            "router_instance_type": "t2.small",
            "scriptbot_instance_type": "t2.small",
            "scoreboard_instance_type": "t2.small",
            "gamebot_instance_type": "t2.small",
            "teaminterface_instance_type": "t2.small",
            "teamvm_instance_type": "t2.small"
        })

    with open('ictf_game_vars.auto.tfvars.json', 'w') as f:
        json.dump(vars, f, indent=2)
