import re
import sys
import os
import json
import subprocess
import tempfile
import logging
import argparse
import hashlib
import requests
import shutil
import base64


class ArgParser(object):
    def parse(self, argv):
        parser = argparse.ArgumentParser()
        parser.add_argument('--hash', dest='game_hash', action='store')
        parser.add_argument('--json', dest='game_json', action='store')
        parser.add_argument('-o', dest='output_path', action='store')
        parser.add_argument('--log', dest='log_path', action='store',
                            default='/tmp')
        args = parser.parse_args(argv)
        if not args.output_path:
            parser.error('Please specify a path where to store the bundle')
        if args.game_hash:
            args.remote = True
            assert re.match(r'[a-zA-Z0-9]+\Z', args.game_hash)
            req_str = "http://ictf.cs.ucsb.edu/framework/ctf/{}"
            game = requests.get(req_str.format(args.game_hash)).json()
            args.game = game
            sys.path.insert(0, "/var/www/framework")
            import secrets
        elif args.game_json:
            args.remote = False
            try:
                json_game = open(args.game_json, 'r')
                game = json.load(json_game)
                json_game.close()
                args.game_hash = hashlib.md5(game.get('name')).hexdigest()
                args.game = game
            except Exception, e:
                raise Exception(e)
        else:
            parser.error('Please specify either a hash (remote) or a json '
                         'descriptor (local)')
        return args


def status(game_hash, status_msg, remote=False):
    logging.info("Status: {}".format(status_msg))
    # Post status only if it remote
    if remote and status_msg in ['READY', 'CONFIRMED', 'PENDING', 'ERROR']:
        post = "http://ictf.cs.ucsb.edu/framework/ctf/status/{}/{}?secret={}"
        requests.post(post.format(game_hash, status_msg, secrets.API_SECRET))


def run_cmd(arglist, cmd_name):
    logging.debug("Running {} ({})".format(cmd_name, ' '.join(arglist)))
    try:
        out = subprocess.check_output(arglist, stderr=subprocess.STDOUT)
        logging.debug("\tOutput: {}".format(out))
    except subprocess.CalledProcessError as e:
        logging.error("")
        logging.error(" **** {} failed **** ".format(cmd_name))
        logging.error(" ** Command line: {}".format(e.cmd))
        logging.error(" ** Return code: {}".format(e.returncode))
        logging.error(" ** Output: {}".format(e.output))
        logging.error(" **************************************************")
        logging.error("")
        raise


def gamepath(output_path, game_hash, clean_up=False):
    path = os.path.join(output_path, game_hash)
    if os.path.exists(path):
        if clean_up:
            shutil.rmtree(path)
    else:
        try:
            os.makedirs(path)
        except OSError:
            if not os.path.isdir(path):
                raise
    return path


def mountdir_copyfile(mntdir, frompath, topath):
    run_cmd(['sudo', 'cp', '-f', frompath, '{}/{}'.format(mntdir, topath)],
            'cp file to mounted dir')


def mountdir_copydir(mntdir, frompath, topath):
    run_cmd(['sudo', 'cp', '-a', frompath, '{}/{}'.format(mntdir, topath)],
            'cp path to mounted dir')


def mountdir_writefile(mntdir, topath, content):
    tmpfd, tmpfilename = tempfile.mkstemp(prefix='formnt_')
    tmpfile = os.fdopen(tmpfd, 'w')
    tmpfile.write(content)
    tmpfile.close()
    mountdir_copyfile(mntdir, tmpfilename, topath)
    os.unlink(tmpfilename)


def mountdir_appendfile(mntdir, topath, content):
    orig_file = open(os.path.join(mntdir, topath), 'r')
    file_content = orig_file.read()
    orig_file.close()
    new_content = '{}{}'.format(file_content, content)
    mountdir_writefile(mntdir, topath, new_content)


def mountdir_bash(mntdir, bash_cmd):
    run_cmd(['sudo', 'chroot', mntdir, '/bin/bash', '-c', bash_cmd],
            "cmd in mounted dir")


def mountdir_start_config(mntdir, ip, netmask, hostname, root_key, team_key,
                          has_nat=False):
    # Network config
    interfaces = """
auto lo
iface lo inet loopback
auto eth0
iface eth0 inet static
    address {}
    netmask {}
""".format(ip, netmask)
    if has_nat:
        interfaces += '\nauto eth1\niface eth1 inet dhcp\n'
    mountdir_writefile(mntdir, '/etc/network/interfaces', interfaces)
    mountdir_writefile(mntdir, '/etc/hostname', hostname)

    # Login config
    # Note: This does _not_ prevent console logins with the default password.
    #       If you give out the VM, players can always get root.
    mountdir_bash(mntdir, 'mkdir -p /root/.ssh')
    mountdir_writefile(mntdir, '/root/.ssh/authorized_keys', root_key)
    mountdir_bash(mntdir, 'mkdir -p /home/ictf/.ssh')
    mountdir_bash(mntdir, 'chown ictf:ictf /home/ictf/.ssh')
    mountdir_bash(mntdir, 'chmod go-rwx /home/ictf/.ssh')
    mountdir_writefile(mntdir, '/home/ictf/.ssh/authorized_keys', team_key)
    mountdir_bash(mntdir, 'chown ictf:ictf /home/ictf/.ssh/authorized_keys')
    mountdir_bash(mntdir, 'chmod go-rwx /home/ictf/.ssh/authorized_keys')
    mountdir_writefile(mntdir, '/etc/ssh/sshd_config', """
Port 22
Protocol 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_dsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key
UsePrivilegeSeparation yes
SyslogFacility AUTH
LogLevel INFO
LoginGraceTime 120
StrictModes yes
RSAAuthentication yes
PubkeyAuthentication yes
IgnoreRhosts yes
RhostsRSAAuthentication no
HostbasedAuthentication no
PermitEmptyPasswords no
TCPKeepAlive yes
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server
UsePAM yes
PermitRootLogin yes
ChallengeResponseAuthentication no
PasswordAuthentication no
UseDNS no
""")

    # General reset
    mountdir_bash(mntdir, "rm -rf /var/cache/apt/*")
    mountdir_bash(mntdir, "rm -f /etc/ssh/ssh_host*")
    mountdir_writefile(mntdir, '/etc/rc.local', """#!/bin/sh -e
dpkg-reconfigure openssh-server
exit 0""")
    mountdir_bash(mntdir, "chmod a+x /etc/rc.local")

    # Set a DNS server that works when chrooted in
    #     (mountdir_end_config will set the real one)
    mountdir_bash(mntdir, 'rm -f /etc/resolv.conf')
    mountdir_writefile(mntdir, '/etc/resolv.conf', 'nameserver 8.8.8.8')


def mountdir_end_config(mntdir):
    # No DNS server in this version, unless provided by dhcp
    mountdir_writefile(mntdir, '/etc/resolv.conf', '')


def mountdir_install_deb(mntdir, deb_path):
    deb_filename = os.path.basename(deb_path)
    mountdir_copyfile(mntdir, deb_path, '/'+deb_filename)
    mountdir_bash(mntdir, "gdebi -q -n /"+deb_filename)


def create_ssh_key(secret_file_name):
    run_cmd(['ssh-keygen', '-q', '-N', '', '-C',
             os.path.basename(secret_file_name), '-f', secret_file_name],
            "ssh-keygen")
    with open('{}.pub'.format(secret_file_name)) as public_key_file:
        return public_key_file.read()


def read_service_script(path):
    with open(path) as script_file:
        return base64.b64encode(script_file.read())


def bundle(game_hash, vm_name, key_name, team_hash, output_dir, remote):
    status(game_hash, "Creating the {} bundle".format(vm_name), remote)
    game_dir = gamepath(output_dir, game_hash)
    os.chdir(game_dir)
    files = [vm_name+"/"+vm_name+".vbox",
             vm_name+"/"+vm_name+"-disk1.vdi",
             key_name,
             key_name+".pub"]
    for bundle_file in files:
        assert os.path.isfile(bundle_file)
    bundle_filename = "{}.tar.gz".format(team_hash)
    logging.info("Putting the {} bundle in {}".format(vm_name,
                                                      bundle_filename))
    tar_cmdline = ['tar', 'caf', os.path.join(output_dir, bundle_filename)]
    tar_cmdline.extend(files)
    run_cmd(tar_cmdline, "bundle tar")
    status(game_hash, "Created the {} bundle".format(vm_name), remote)
    return bundle_filename
