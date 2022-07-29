#!/usr/bin/env python3

import argparse
import os
import json
import shutil
import shlex
import subprocess

SERVICE_DEST_DIR = '../../teamvms/bundled_services'

if not os.path.exists(SERVICE_DEST_DIR):
    os.mkdir(SERVICE_DEST_DIR)
else:
    shutil.rmtree(SERVICE_DEST_DIR)
    os.mkdir(SERVICE_DEST_DIR)

def build_teamvm(game_config_path):
    if not os.path.exists(game_config_path):
        print("The specified game_config path does not exist")
        return
    # If game_config is a symlink, then Docker will not be able to load it in the context.
    # Save some time and fail early.
    if os.path.islink(game_config_path):
        print(f"\033[31mThe game config {os.path.abspath(game_config_path)} is a link. This is not supported by docker.")
        print("Please make it a regular file.\033[0m")
        exit(1)

    with open(game_config_path, 'r') as f:
        game_config = json.load(f)

    services_dir = game_config['service_metadata']['host_dir']
    active_services = []

    for service in game_config['services']:
        if service['state'] == 'enabled':
            # Package the service and build the scripts container
            print("\nBuilding {}....\n\n".format(service['name']))
            service_dir = os.path.join(services_dir, service['name'])
            subprocess.check_call(['make', '-C', service_dir, 'clean'])
            print("\n")
            subprocess.check_call(['make', '-C', service_dir, 'bundle'])
            print("\n")
            subprocess.check_call(['make', '-C', service_dir, 'scriptbot_scripts', f"SERVICE_NAME={service['name']}"])
            print("\n")
            subprocess.check_call(['docker', 'build', '-t', service['name'], os.path.join(service_dir, 'service')])
            shutil.copytree(os.path.join(services_dir, service['name'], "service"), os.path.join(SERVICE_DEST_DIR, service['name']))
            active_services.append(service['name'])

    subprocess.check_call(
        [
            'docker-compose',
            '-f', './docker-compose-teamvm.yml',
            'build',
            '--build-arg', "services={}".format(json.dumps({'SERVICES': active_services})),
        ]
    )


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('game_config', type=str, help="Path to game_config.json file")
    args = argparser.parse_args()

    build_teamvm(args.game_config)
