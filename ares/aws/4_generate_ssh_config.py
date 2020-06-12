#!/usr/bin/env python

import subprocess
import argparse
import os
import json
import sys
import datetime
import shutil
import time
import requests
import zipfile

from Crypto.PublicKey import RSA
from string import Template

class TfInitException(Exception):
    """
    Exception raised by terraform if the init command fails
    """

class TfApplyException(Exception):
    """
    Exception raised by terraform if the apply command fails
    """

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

OUTPUT_FILE = "ssh_config"
SSHKEYS_FOLDER = "./sshkeys/"
VPNKEYS_FOLDER = "./vpnkeys/"
SECRETS_FOLDER = '../../secrets/'
TF_SSHKEYS = "./infrastructure/aws_sshkeys.tf" # will contain the declaration of all the ssh keys
BACKUP_FOLDER = "./backup/"

# This will be written in a terraform config file.
AWS_KEY_TEMPLATE = Template('resource "aws_key_pair" "$keyname" { \n\
  key_name   = "$keyname" \n\
  public_key = "$${file("./sshkeys/$keyname.pub")}" \n\
}\n')

# Define the Vms
VM_NAMES = ['database', 'router', 'gamebot', 'scoreboard', 'teaminterface', 'scriptbot', 'teamvmmaster', 'dispatcher', 'logger']

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
        raise NoInstancePublicIpFound(instance_name)
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


def generate_ssh_config(terraform_path):
    terraform_outputs = subprocess.check_output("{} output -json".format(terraform_path), shell=True)
    parsed_outputs    = json.loads(terraform_outputs.decode('utf-8'))
    with open(OUTPUT_FILE, 'w') as out_f:
        def write_host_entry(name, ip, key):
            out_f.write('Host %s\n' % name)
            out_f.write('  Hostname %s\n' % ip)
            out_f.write('  IdentityFile "%s/%s-key.key"\n\n' % (SSHKEYS_FOLDER, key))

        out_f.write('Host *\n')
        out_f.write('  Port 22\n')
        out_f.write('  User ubuntu\n')
        out_f.write('  UserKnownHostsFile "%s/known_hosts"\n' % SSHKEYS_FOLDER)
        out_f.write('  IdentitiesOnly yes\n\n')

        for instance_name, instance_values in parsed_outputs.items():
            instance_name = instance_name.replace('_public_ip', '')
            if instance_name == 'scriptbots':
                for scriptbot_num, scriptbot_ip in instance_values["value"].items():
                    write_host_entry(scriptbot_num, scriptbot_ip, "scriptbot")
            elif instance_name == 'teamvms':
                for teamvm_num, teamvm_ip in instance_values["value"].items():
                    write_host_entry(teamvm_num, teamvm_ip, "teamvmmaster")
            elif instance_name in VM_NAMES:
                write_host_entry(instance_name, instance_values["value"], instance_name)
            else:
                print("Skipping {}...".format(instance_name))


def create_ssh_config(terraform_path):
    print("\n[*] ---------------- STEP 5: Dump the SSH config file ----------------")
    generate_ssh_config(terraform_path)
    print("\n[!] DONE!!\n")
    print("you can find the generated ssh config in ./ssh_config")
    print()
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--terraform_path', type=str, default="terraform",
                        help='Path to the terraform tool (default: terraform in your $PATH)')
    args = parser.parse_args()

    with open('ictf_game_vars.auto.tfvars.json', 'r') as f:
        ictf_vars = json.load(f)

    create_ssh_config(args.terraform_path)

