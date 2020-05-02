#!/usr/bin/env python

import argparse
import os
import json
import shutil

SERVICE_DEST_DIR = '../teamvms/bundled_services'

if not os.path.exists(SERVICE_DEST_DIR):
    os.mkdir(SERVICE_DEST_DIR)
else:
    shutil.rmtree(SERVICE_DEST_DIR)
    os.mkdir(SERVICE_DEST_DIR)

def build_teamvm(game_config_path):
    if not os.path.exists(game_config_path):
        print("The specified game_config path does not exist")
        return

    with open(game_config_path, 'r') as f:
        game_config = json.load(f)

    services_dir = game_config['service_metadata']['host_dir']
    active_services = []

    for service in game_config['services']:
        if service['state'] == 'enabled':
            # Package the service and build the scripts container
            print("\nBuilding {}....\n\n".format(service['name']))
            os.system('make -C {} clean'.format(os.path.join(services_dir, service['name'])))
            print("\n")
            os.system('make -C {} bundle'.format(os.path.join(services_dir, service['name'])))
            print("\n")
            os.system('make -C {} scriptbot_scripts SERVICE_NAME={}'.format(os.path.join(services_dir, service['name']), service['name']))
            shutil.copytree(os.path.join(services_dir, service['name'], "service"), os.path.join(SERVICE_DEST_DIR, service['name']))
            active_services.append(service['name'])

    os.system("docker-compose -f ./docker-compose-teamvm.yml build --build-arg SERVICES={}".format(json.dumps({ 'SERVICES': active_services })))
    # print("docker-compose -f ./docker-compose-teamvm.yml build --build-arg SERVICES='{}'".format(json.dumps({ 'SERVICES': active_services })))


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('game_config', type=str, help="Path to game_config.json file")
    args = argparser.parse_args()

    build_teamvm(args.game_config)
