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
TF_SSHKEYS = "./aws_sshkeys.tf" # will contain the declaration of all the ssh keys
BACKUP_FOLDER = "./backup/"

# This will be written in a terraform config file.
AWS_KEY_TEMPLATE = Template('resource "aws_key_pair" "$keyname" { \n\
  key_name   = "$keyname" \n\
  public_key = "$${file("./sshkeys/$keyname.pub")}" \n\
}\n')

# Define the Vms
VM_NAMES = ['database', 'router', 'gamebot', 'scoreboard', 'teaminterface', 'scriptbot', 'teamvmmaster']

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


def make_ssh_keys(num_teams):
    if os.path.isfile(TF_SSHKEYS):
        os.remove(TF_SSHKEYS)
    
    if not os.path.exists(SSHKEYS_FOLDER):
        os.mkdir(SSHKEYS_FOLDER)

    teamvms = ["team{}".format(teamid) for teamid in range(1, num_teams + 1)]

    for vm_name in (VM_NAMES + teamvms):
        print("[+] Generating keys for VM {}...".format(vm_name))
        key = RSA.generate(2048)

        private_key_path = SSHKEYS_FOLDER + vm_name + "-key.key"
        public_key_path = SSHKEYS_FOLDER + vm_name + "-key.pub"

        with open(private_key_path, 'bw') as content_file:
            os.chmod(private_key_path, 0o0600)
            content_file.write(key.exportKey('PEM'))

        pubkey = key.publickey() # extracting public key

        with open(public_key_path, 'bw') as content_file:
            content_file.write(pubkey.exportKey('OpenSSH'))

        # now writing terraform config file
        aws_key_config = AWS_KEY_TEMPLATE.substitute({'keyname': vm_name+"-key"})

        with open(TF_SSHKEYS, "a+") as f:  
            f.write(aws_key_config)

    # creating an archive with the generated keys
    print("[+] Generating backup for current keys.")
    archive_name = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
    shutil.make_archive(BACKUP_FOLDER + archive_name + "-VMsshkeys", 'zip', SSHKEYS_FOLDER)
    print("[+] Backup done in " + BACKUP_FOLDER + "!")


def make_vpn_keys(num_teams, num_routers):
    # https://gist.github.com/Soarez/9688998
    # https://superuser.com/questions/738612/openssl-ca-keyusage-extension
    EXT_TEMPLATE = """
[ my_vpn_ca ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always
basicConstraints       = critical, CA:TRUE, pathlen:0
keyUsage               = critical, cRLSign, digitalSignature, keyCertSign

[ my_vpn_server ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always
basicConstraints       = critical, CA:FALSE
keyUsage               = critical, nonRepudiation, digitalSignature, keyEncipherment, keyAgreement
extendedKeyUsage       = critical, serverAuth

[ my_vpn_client ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always
basicConstraints       = critical, CA:FALSE
keyUsage               = critical, nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage       = critical, clientAuth
"""

    VPN_SERVER_TEMPLATE = """
server 10.9.{num}.0 255.255.255.0
topology subnet

dev tun{num}
proto udp
port 110{num}

txqueuelen 10000
sndbuf 0
rcvbuf 0

cipher AES-256-GCM
key-direction 0

ccd-exclusive
client-config-dir /etc/openvpn/server{num}.ccd
explicit-exit-notify 1
keepalive 10 120

management /run/openvpn/server{num}.sock unix
management-client-user  root
management-client-group root

log-append /var/log/openvpn/server{num}.log
status     /run/openvpn/server{num}.status
verb 3
mute 20

<ca>\n{ca}</ca>\n
<cert>\n{cert}</cert>\n
<key>\n{key}</key>\n
<dh>\n{dh}</dh>\n
<tls-auth>\n{ta}</tls-auth>
"""

    VPN_CLIENT_TEMPLATE = """
client
topology subnet

dev tun0
proto udp
nobind

remote {{{{ ROUTER_PRIVATE_IP }}}} 110{num}
resolv-retry infinite

remote-cert-tls server
cipher AES-256-GCM
key-direction 1

log-append /var/log/openvpn/client.log
status     /run/openvpn/client.status
verb 3
mute 20

<ca>\n{ca}</ca>\n
<cert>\n{cert}</cert>\n
<key>\n{key}</key>\n
<tls-auth>\n{ta}</tls-auth>
"""
    def sign(base, mode, name):
        subprocess.run(["openssl", "genrsa",
            "-out",  base + ".key",
            "4096"
        ], check=True)

        subprocess.run(["openssl", "req", "-new",
            "-subj", "/O=iCTF/CN=" + name,
            "-key",  base + ".key",
            "-out",  base + ".csr"
        ], check=True)

        if mode == "ca":
            subprocess.run(["openssl", "x509", "-req",
                "-signkey",    VPNKEYS_FOLDER + "/ca.key",
                "-extfile",    VPNKEYS_FOLDER + "/ca.ext",
                "-extensions", "my_vpn_ca",
                "-in",         base + ".csr",
                "-out",        base + ".crt",
                "-sha384"
            ], check=True)
        else:
            subprocess.run(["openssl", "x509", "-req", "-CAcreateserial",
                "-CA",         VPNKEYS_FOLDER + "/ca.crt",
                "-CAkey",      VPNKEYS_FOLDER + "/ca.key",
                "-CAserial",   VPNKEYS_FOLDER + "/ca.srl",
                "-extfile",    VPNKEYS_FOLDER + "/ca.ext",
                "-extensions", "my_vpn_" + mode,
                "-in",         base + ".csr",
                "-out",        base + ".crt",
                "-sha384"
            ], check=True)

    def cat(filename):
        with open(filename) as f:
            return f.read()

    assert VPNKEYS_FOLDER.endswith("/")
    if not os.path.exists(VPNKEYS_FOLDER):
        os.mkdir(VPNKEYS_FOLDER)

    # diffie hellman parameters
    if not os.path.exists(VPNKEYS_FOLDER + "dh.pem"):
        subprocess.run(["openssl", "dhparam",
            "-out", VPNKEYS_FOLDER + "dh.pem",
            "2048"
        ], check=True)

    # ca certificates
    if not os.path.exists(VPNKEYS_FOLDER + "ca.ext"):
        with open(VPNKEYS_FOLDER + "ca.ext", "w") as f:
            f.write(EXT_TEMPLATE)

    if not os.path.exists(VPNKEYS_FOLDER + "ca.crt"):
        sign(VPNKEYS_FOLDER + "ca", "ca", "VPN Root CA")


    # server config files
    for n in range(num_routers):
        serv = "server%d" % (n + 1)

        if not os.path.exists(VPNKEYS_FOLDER + serv + ".tls"):
            with open(VPNKEYS_FOLDER + serv + ".tls", "w") as f:
                f.write("-----BEGIN OpenVPN Static key V1-----\n")
                for _ in range(16): f.write(os.urandom(16).hex() + "\n")
                f.write("-----END OpenVPN Static key V1-----\n")

        if not os.path.exists(VPNKEYS_FOLDER + serv + ".crt"):
            sign(VPNKEYS_FOLDER + serv, "server", serv)

        if not os.path.exists(VPNKEYS_FOLDER + serv + ".ovpn"):
            with open(VPNKEYS_FOLDER + serv + ".ovpn", "w") as f:
                f.write(VPN_SERVER_TEMPLATE.format(
                    ca   = cat(VPNKEYS_FOLDER + "ca.crt"),
                    cert = cat(VPNKEYS_FOLDER + serv + ".crt"),
                    key  = cat(VPNKEYS_FOLDER + serv + ".key"),
                    dh   = cat(VPNKEYS_FOLDER + "dh.pem"),
                    ta   = cat(VPNKEYS_FOLDER + serv + ".tls"),
                    num  = n + 1
                ))

    # client config files
    for n in range(num_teams):
        team = "team%d"   % (n + 1)
        serv = "server%d" % (n % num_routers + 1)

        if not os.path.exists(VPNKEYS_FOLDER + team + ".crt"):
            sign(VPNKEYS_FOLDER + team, "client", team)

        if not os.path.exists(VPNKEYS_FOLDER + team + ".ovpn"):
            with open(VPNKEYS_FOLDER + team + ".ovpn", "w") as f:
                f.write(VPN_CLIENT_TEMPLATE.format(
                    ca   = cat(VPNKEYS_FOLDER + "ca.crt"),
                    cert = cat(VPNKEYS_FOLDER + team + ".crt"),
                    key  = cat(VPNKEYS_FOLDER + team + ".key"),
                    ta   = cat(VPNKEYS_FOLDER + serv + ".tls"),
                    num  = n % num_routers + 1
                ))

    # server-side client config (static ips)
    with zipfile.ZipFile(VPNKEYS_FOLDER + "ccd.zip", "w") as z:
        for n in range(num_teams):
            team = "team%d"   % (n + 1)
            serv = "server%d" % (n % num_routers + 1)
            filename = "%s.ccd/%s" % (serv, team)
            template = "ifconfig-push 10.9.%d.%d 255.255.0.0\n"
            z.writestr(filename, template % (
                (n  % num_routers) + 1,
                (n // num_routers) + 3
            ))


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
        out_f.write('  User hacker\n')
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


def bootstrap_game(aws_access_key, aws_secret_key, game_config_path, terraform_path):

    if not os.path.exists(game_config_path):
        raise NoGameConfigFoundException

    with open(game_config_path, 'r') as game_config_f:
        game_config = json.load(game_config_f)

    services_path = game_config["service_metadata"]["host_dir"]

    teams_num = len(game_config['teams'])

    user_input = input("> Do you want to spawn a game with {} teams? [y/N] ".format(teams_num))

    if user_input.lower() != 'y':
        print("[!] Exiting...")
        sys.exit()

    print("\n[*] ---------------- STEP 1: Terraform init ----------------")
    tf_init_process = subprocess.call("{} init".format(terraform_path), shell=True)
    
    if tf_init_process != 0:
        raise TfInitException

    print("\n[*] ---------------- STEP 2: Make keys for infrastructure components and for the teams ----------------")

    make_ssh_keys(teams_num)
    make_vpn_keys(teams_num, 4)

    print("\n[*] ---------------- STEP 3: Spawn the infrastructure ----------------")
    tf_apply_process = subprocess.call(
        "{} apply -parallelism=25 -var 'access_key={}' -var 'secret_key={}' -var 'teams_num={}' -var 'services_path={}' -var 'game_config_file={}'".format(
            terraform_path, aws_access_key, aws_secret_key, teams_num, services_path, game_config_path),
            shell=True)

    if tf_apply_process != 0:
        raise TfApplyException

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

    print("\n[*] ---------------- STEP 5: Dump the SSH config file ----------------")
    generate_ssh_config(terraform_path)
    print("\n[!] DONE!!\n")
    print("you can find the generated ssh config in ./ssh_config")
    print()
    print("START GAME URL: {}".format(_execute_terraform_output("start_game_url", terraform_path)))
    print()
    print("STOP GAME URL: {}".format(_execute_terraform_output("stop_game_url", terraform_path)))
    print()
    

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('aws_access_key', type=str, help="Access key for AWS")
    argparser.add_argument('aws_secret_key', type=str, help="Secret key for AWS")
    argparser.add_argument('game_config_path', type=str, help="Path to the game configuration file")
    argparser.add_argument('-t', '--terraform_path', type=str, default=os.path.abspath("../terraform"), 
                            help='Path to the terraform tool (default to: <ICTF_ROOT>/ares/terraform)')
    args = argparser.parse_args()

    bootstrap_game(args.aws_access_key, args.aws_secret_key, args.game_config_path, args.terraform_path)
