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

SSHKEYS_FOLDER = "./sshkeys/"
VPNKEYS_FOLDER = "./vpnkeys/"
TF_SSHKEYS = "./infrastructure/aws_sshkeys.tf"  # will contain the declaration of all the ssh keys
BACKUP_FOLDER = "./backup/"

# This will be written in a terraform config file.
AWS_KEY_TEMPLATE = Template('resource "aws_key_pair" "$keyname" { \n\
  key_name   = "$keyname" \n\
  public_key = file("./sshkeys/$keyname.pub") \n\
}\n')

# Define the Vms
VM_NAMES = ['database', 'router', 'gamebot', 'scoreboard', 'teaminterface', 'scriptbot', 'teamvmmaster', 'dispatcher', 'logger']


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

        pubkey = key.publickey()  # extracting public key

        with open(public_key_path, 'bw') as content_file:
            content_file.write(pubkey.exportKey('OpenSSH'))

        # now writing terraform config file
        aws_key_config = AWS_KEY_TEMPLATE.substitute({'keyname': vm_name + "-key"})

        with open(TF_SSHKEYS, "a+") as f:
            f.write(aws_key_config)

    # creating an archive with the generated keys
    print("[+] Generating backup for current keys.")
    archive_name = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
    shutil.make_archive(BACKUP_FOLDER + archive_name + "-VMsshkeys", 'zip', SSHKEYS_FOLDER)
    print("[+] Backup done in " + BACKUP_FOLDER + "!")


def make_vpn_keys(num_teams, num_routers, router_public_ip):
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
port {port}

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

status /run/openvpn/server{num}.status
status-version 2

log-append /var/log/openvpn/server{num}.log
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

remote {router_public_ip} {port}
resolv-retry infinite

remote-cert-tls server
cipher AES-256-GCM
key-direction 1

status /run/openvpn/client.status
status-version 2

log-append /var/log/openvpn/client.log
verb 3
mute 20

<ca>\n{ca}</ca>\n
<cert>\n{cert}</cert>\n
<key>\n{key}</key>\n
<tls-auth>\n{ta}</tls-auth>
"""

    def sign(base, mode, name):
        subprocess.run(["openssl", "genrsa",
                        "-out", base + ".key",
                        "4096"
                        ], check=True)

        subprocess.run(["openssl", "req", "-new",
                        "-subj", "/O=iCTF/CN=" + name,
                        "-key", base + ".key",
                        "-out", base + ".csr"
                        ], check=True)

        if mode == "ca":
            subprocess.run(["openssl", "x509", "-req",
                            "-signkey", VPNKEYS_FOLDER + "/ca.key",
                            "-extfile", VPNKEYS_FOLDER + "/ca.ext",
                            "-extensions", "my_vpn_ca",
                            "-in", base + ".csr",
                            "-out", base + ".crt",
                            "-sha384"
                            ], check=True)
        else:
            subprocess.run(["openssl", "x509", "-req", "-CAcreateserial",
                            "-CA", VPNKEYS_FOLDER + "/ca.crt",
                            "-CAkey", VPNKEYS_FOLDER + "/ca.key",
                            "-CAserial", VPNKEYS_FOLDER + "/ca.srl",
                            "-extfile", VPNKEYS_FOLDER + "/ca.ext",
                            "-extensions", "my_vpn_" + mode,
                            "-in", base + ".csr",
                            "-out", base + ".crt",
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
        print("[+] Creating Openvpn keys for {}".format(serv))

        if not os.path.exists(VPNKEYS_FOLDER + serv + ".tls"):
            with open(VPNKEYS_FOLDER + serv + ".tls", "w") as f:
                f.write("-----BEGIN OpenVPN Static key V1-----\n")
                for _ in range(16): f.write(os.urandom(16).hex() + "\n")
                f.write("-----END OpenVPN Static key V1-----\n")

        if not os.path.exists(VPNKEYS_FOLDER + serv + ".crt"):
            sign(VPNKEYS_FOLDER + serv, "server", serv)

        with open(VPNKEYS_FOLDER + serv + ".conf", "w") as f:
            f.write(VPN_SERVER_TEMPLATE.format(
                ca=cat(VPNKEYS_FOLDER + "ca.crt"),
                cert=cat(VPNKEYS_FOLDER + serv + ".crt"),
                key=cat(VPNKEYS_FOLDER + serv + ".key"),
                dh=cat(VPNKEYS_FOLDER + "dh.pem"),
                ta=cat(VPNKEYS_FOLDER + serv + ".tls"),
                num=n + 1,
                router_public_ip=router_public_ip,
                port=1101 + n
            ))

    # client config files
    for n in range(num_teams):
        team = "team%d" % (n + 1)
        serv = "server%d" % (n % num_routers + 1)

        if not os.path.exists(VPNKEYS_FOLDER + team + ".crt"):
            sign(VPNKEYS_FOLDER + team, "client", team)

        with open(VPNKEYS_FOLDER + team + ".ovpn", "w") as f:
            f.write(VPN_CLIENT_TEMPLATE.format(
                ca=cat(VPNKEYS_FOLDER + "ca.crt"),
                cert=cat(VPNKEYS_FOLDER + team + ".crt"),
                key=cat(VPNKEYS_FOLDER + team + ".key"),
                ta=cat(VPNKEYS_FOLDER + serv + ".tls"),
                num=n % num_routers + 1,
                router_public_ip=router_public_ip,
                port=1101 + n % num_routers
            ))

    # server config zip
    with zipfile.ZipFile(VPNKEYS_FOLDER + "openvpn.zip", "w") as z:
        for n in range(num_routers):
            filename = "server%s.conf" % (n + 1)
            z.write(VPNKEYS_FOLDER + filename, filename)

        for n in range(num_teams):
            team = "team%d" % (n + 1)
            serv = "server%d" % (n % num_routers + 1)
            filename = "%s.ccd/%s" % (serv, team)
            template = "ifconfig-push 10.9.%d.%d 255.255.0.0\n"
            z.writestr(filename, template % (
                (n % num_routers) + 1,
                (n // num_routers) + 3
            ))


def create_credentials(num_teams, num_routers, router_public_ip):
    make_ssh_keys(num_teams)
    make_vpn_keys(num_teams, num_routers, router_public_ip)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('game_config_file', type=str, help='Path to the game config file')
    args = parser.parse_args()

    with open(args.game_config_file, 'r') as f:
        game_config = json.load(f)

    create_credentials(len(game_config['teams']), game_config['game_info']['num_routers'], game_config['game_info']['router_public_ip'])
