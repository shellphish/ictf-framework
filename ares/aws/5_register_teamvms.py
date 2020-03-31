#!/usr/bin/env python

import subprocess
import argparse
import os
import json
import requests


class TfOutputException(Exception):
    """
    Exception raised by terraform if the output command fails
    """

class NoSSHKeyFoundException(Exception):
    """
    Exception raised when the team's private key is not found
    """

class NoDatabaseSecretFoundException(Exception):
    """
    Exception raised when the database's secret is not found 
    """

class NoGameConfigFoundException(Exception):
    """
    Exception raised when the game config is not found 
    """
    
class RegistrationErrorException(Exception):
    """
    Exception raised when the registration of a team fails
    """

class NoInstancePublicIpFound(Exception):
    """
    Exception raised when the instance public ip is not found 
    """

SSHKEYS_FOLDER = "./sshkeys/"
SECRETS_FOLDER = '../../secrets/'

FAKE_IP = "0.0.0.0"

def _execute_terraform_output(args, terraform_path):
    tf_output_process = subprocess.run(
        "{} output {}".format(terraform_path, args), shell=True, check=True, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if tf_output_process.returncode != 0:
        raise TfOutputException

    return tf_output_process.stdout.decode('utf-8').strip()


def _get_teamvm_public_ip(instance_name, terraform_path):
    teamvms_ip = json.loads(_execute_terraform_output("-json teamvms_public_ip", terraform_path))
    if instance_name not in teamvms_ip:
        return FAKE_IP
        # raise NoInstancePublicIpFound(instance_name)
    return teamvms_ip[instance_name]
 
    
def _get_scriptbot_public_ip(instance_name, terraform_path):
    scriptbots_ip = json.loads(_execute_terraform_output("-json scriptbots_public_ip", terraform_path))
    if instance_name not in scriptbots_ip:
        raise NoInstancePublicIpFound(instance_name)
    return scriptbots_ip[instance_name]


def get_instance_public_ip(instance_name, terraform_path):
    if instance_name.startswith("teamvm"):
        return _get_teamvm_public_ip(instance_name, terraform_path)
    if instance_name.startswith("scriptbot"):
        return _get_scriptbot_public_ip(instance_name, terraform_path)
    return _execute_terraform_output("{}_public_ip".format(instance_name), terraform_path)


def register_team_vm(db_api, db_secret, team_id, team_ip, team_ssh_private_key_path):
    if not os.path.exists(team_ssh_private_key_path):
        raise NoSSHKeyFoundException

    with open(team_ssh_private_key_path, 'r') as priv_key_f:
        team_ssh_private_key = priv_key_f.read()

    register_team_vm_url = "http://{}/team/add/keys/{}".format(db_api, team_id)

    data = {"ctf_key": team_ssh_private_key, "root_key": '', "ip": team_ip, "port": 0 }

    result = requests.post(register_team_vm_url, data=data, params={'secret': db_secret})
    response = result.json()
    if response['result'] == "success":
        return response['team_id']
    else:
        raise RegistrationErrorException(response)


def bootstrap_game(game_config_path, terraform_path):
    if not os.path.exists(game_config_path):
        raise NoGameConfigFoundException

    with open(game_config_path, 'r') as game_config_f:
        game_config = json.load(game_config_f)

    print("\n[*] ---------------- STEP 4: Register teamvms into the database ----------------")
    database_api_secret_path = os.path.join(SECRETS_FOLDER, "database-api/secret")
    database_public_ip = get_instance_public_ip('database', terraform_path)

    if not os.path.exists(database_api_secret_path):
        raise NoDatabaseSecretFoundException 

    with open(database_api_secret_path, "r") as db_secret_f:
        database_api_secret = db_secret_f.read().rstrip()

    for team in game_config['teams']:
        print("[+] Registering Team {}".format(team["id"]))
        teamvm_public_ip = get_instance_public_ip('teamvm{}'.format(team['id']), terraform_path)
        team_ssh_private_key_path =  os.path.join(SSHKEYS_FOLDER, "team{}-key.key".format(team['id']))
        register_team_vm(database_public_ip, database_api_secret, team['id'], teamvm_public_ip, team_ssh_private_key_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--terraform_path', type=str, default="terraform",
                        help='Path to the terraform tool (default: terraform in your $PATH)')
    args = parser.parse_args()

    with open('ictf_game_vars.auto.tfvars.json', 'r') as f:
        ictf_vars = json.load(f)

    bootstrap_game(ictf_vars['game_config_file'], args.terraform_path)
