#!/usr/bin/env python2.7

import base64
import json
import logging
import os
import requests
import re
import shutil
import string
import subprocess
import sys
import tempfile
sys.path.insert(0,"/var/www/framework")
import secrets


LOG_DIR = "/tmp"
BUNDLE_OUTPUT_DIR = "/var/www/bundles"    # Make sure not listable!


#### General utilities ###################################################################

def status(game_hash, status_msg):
    logging.info("Status: %s", status_msg)
    print status_msg
    if status_msg in ['READY','CONFIRMED','PENDING','ERROR']:
        requests.post("http://ictf.cs.ucsb.edu/framework/ctf/status/"+game_hash+"/"+status_msg+"?secret="+secrets.API_SECRET)

def run_cmd(arglist, cmd_name):
    logging.debug("Running %s (%s)", cmd_name, ' '.join(arglist))
    try:
        out = subprocess.check_output(arglist, stderr=subprocess.STDOUT)
        logging.debug("        Output: %s", out)
    except subprocess.CalledProcessError as e:
        logging.error("")
        logging.error(" **** %s failed **** ", cmd_name)
        logging.error(" ** Command line: %s", e.cmd)
        logging.error(" ** Return code: %d", e.returncode)
        logging.error(" ** Output: %s", e.output)
        logging.error(" **************************************************")
        logging.error("")
        raise

def gamepath(game_hash):
    path = "/game/"+game_hash
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise
    return path

def create_ssh_key(secret_file_name):
    run_cmd(['ssh-keygen','-q','-N','','-C',os.path.basename(secret_file_name),'-f',secret_file_name], "ssh-keygen")
    with open(secret_file_name+'.pub') as public_key_file:
        return public_key_file.read()

def read_service_script(path):
    with open(path) as script_file:
        return base64.b64encode(script_file.read())

def bundle(game_hash, vm_name, key_name, team_hash):
    status(game_hash, "Creating the %s bundle" % vm_name)
    gamedir = gamepath(game_hash)
    os.chdir(gamedir)
    files = [
            vm_name+"/"+vm_name+".vbox",
            vm_name+"/"+vm_name+"-disk1.vdi",
            key_name,
            key_name+".pub"
            ]
    for bundle_file in files:
        assert os.path.isfile(bundle_file)
    bundle_filename = team_hash+".tar.gz"
    logging.info("Putting the %s bundle in %s", vm_name, bundle_filename)
    tar_cmdline = ['tar','caf',BUNDLE_OUTPUT_DIR+"/"+bundle_filename]
    tar_cmdline.extend(files)
    run_cmd(tar_cmdline, "bundle tar")
    status(game_hash, "Created the %s bundle" % vm_name)
    return bundle_filename




#### General VM interaction ##################################################################

def clone_vm(game_hash, base_vm, name):
    assert re.match(r'[a-zA-Z0-9_-]+\Z',name)
    status(game_hash, "Creating VM: {}".format(name))
    basepath = gamepath(game_hash)
    run_cmd(["VBoxManage","clonevm",base_vm,"--name",name,"--basefolder",basepath], "clonevm "+name)
    return basepath+'/'+name

def mountdir_copyfile(mntdir, frompath, topath):
    run_cmd(['sudo','cp','-f',frompath,mntdir+'/'+topath], 'cp file to mounted dir')
def mountdir_copydir(mntdir, frompath, topath):
    run_cmd(['sudo','cp','-r',frompath,mntdir+'/'+topath], 'cp path to mounted dir')

def mountdir_writefile(mntdir, topath, content):
    tmpfd, tmpfilename = tempfile.mkstemp(prefix='formnt_')
    tmpfile = os.fdopen(tmpfd,'w')
    tmpfile.write(content)
    tmpfile.close()
    mountdir_copyfile(mntdir, tmpfilename, topath)
    os.unlink(tmpfilename)

def mountdir_bash(mntdir, bash_cmd):
    run_cmd(['sudo','chroot',mntdir,'/bin/bash','-c',bash_cmd], "cmd in mounted dir")


def mountdir_start_config(mntdir, ip, netmask, hostname, root_key, team_key, has_nat=False):
    # Network config
    interfaces ="""
auto lo
iface lo inet loopback
auto eth0
iface eth0 inet static
    address %s
    netmask %s
""" % (ip, netmask)
    if has_nat:
        interfaces += '\nauto eth1\niface eth1 inet dhcp\n'
    mountdir_writefile(mntdir,'/etc/network/interfaces', interfaces)
    mountdir_writefile(mntdir,'/etc/hostname', hostname)

    # Login config
    # Note: This does _not_ prevent console logins with the default password.
    #       If you give out the VM, players can always get root.
    mountdir_bash(mntdir,'mkdir -p /root/.ssh')
    mountdir_writefile(mntdir,'/root/.ssh/authorized_keys', root_key)
    mountdir_bash(mntdir,'mkdir -p /home/ictf/.ssh')
    mountdir_bash(mntdir,'chown ictf:ictf /home/ictf/.ssh')
    mountdir_bash(mntdir,'chmod go-rwx /home/ictf/.ssh')
    mountdir_writefile(mntdir,'/home/ictf/.ssh/authorized_keys', team_key)
    mountdir_bash(mntdir,'chown ictf:ictf /home/ictf/.ssh/authorized_keys')
    mountdir_bash(mntdir,'chmod go-rwx /home/ictf/.ssh/authorized_keys')
    mountdir_writefile(mntdir,'/etc/ssh/sshd_config', """
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
"""
    )

    # General reset
    mountdir_bash(mntdir, "rm -rf /var/cache/apt/*")
    mountdir_bash(mntdir, "rm -f /etc/ssh/ssh_host*")
    mountdir_writefile(mntdir, '/etc/rc.local', """#!/bin/sh -e
dpkg-reconfigure openssh-server
exit 0""")
    mountdir_bash(mntdir, "chmod a+x /etc/rc.local")

    # Set a DNS server that works when chrooted in
    #     (mountdir_end_config will set the real one)
    mountdir_bash(mntdir,'rm -f /etc/resolv.conf')
    mountdir_writefile(mntdir,'/etc/resolv.conf', 'nameserver 8.8.8.8')

def mountdir_end_config(mntdir):
    # No DNS server in this version, unless provided by dhcp
    mountdir_writefile(mntdir,'/etc/resolv.conf', '')

def mountdir_install_deb(mntdir, deb_path):
    deb_filename = os.path.basename(deb_path)
    mountdir_copyfile(mntdir, deb_path, '/'+deb_filename)
    mountdir_bash(mntdir, "gdebi -q -n /"+deb_filename)




#### VM creation ############################################################################

def create_team(game_hash, team_id, root_key, team_key, services):
    # XXX: see also create_org
    assert team_id < 200
    vmdir = clone_vm(game_hash, "iCTF-base", "Team%d"%team_id)
    status(game_hash, "Configuring the VM for Team %d" % team_id)
    os.chdir(vmdir)

    # VirtualBox internal network: teamXXX
    # Note: the VM *must* be configured to use the 'intnet' internal network
    with open("Team%d.vbox"%team_id) as vboxfile:
        assert vboxfile.read().count("intnet") == 1
    run_cmd(['sed','-i','s/intnet/ictf/g',"Team%d.vbox"%team_id], "sed replace intnet")

    mntdir = vmdir+"/mnt"
    os.mkdir(mntdir)
    run_cmd(['sudo','guestmount','-a','Team%d-disk1.vdi'%team_id,'-i',mntdir], "guestmount")
    try:
        run_cmd(['sudo','mount','--bind','/dev',mntdir+'/dev'], "dev bind")
        mountdir_start_config(mntdir,
                ip='10.7.%d.2'%team_id,
                netmask='255.255.0.0',
                hostname="team%d"%team_id,
                root_key=root_key,
                team_key=team_key
                )
        mountdir_bash(mntdir, "passwd --lock root")
        mountdir_bash(mntdir, "passwd --lock ictf")
        mountdir_writefile(mntdir, "/etc/sysctl.d/90-no-aslr.conf", "kernel.randomize_va_space = 0")

        status(game_hash, "Setting up the services for Team %d" % team_id)
        for service in services:
            assert re.match(r'[a-zA-Z0-9_-]+\Z',service)
            mountdir_install_deb(mntdir, '/services/%s.deb' % service)

        status(game_hash, "Finalizing the VM for Team %d" % team_id)
        mountdir_end_config(mntdir)
        subprocess.call(["sudo","umount",mntdir+'/dev'])
        run_cmd(['sudo','guestunmount',mntdir], "guestunmount")
    except:
        subprocess.call(["sudo","umount","-l",mntdir+'/dev'])
        subprocess.Popen(["sudo","guestunmount",mntdir]) # Do it in the background, in case it blocks
        raise


def create_org(game_hash, game_name, teams, services, root_keyfile):
    # XXX: see also create_team
    vmdir = clone_vm(game_hash, "Organization-base", "Organization")
    status(game_hash, "Configuring the organization VM")
    os.chdir(vmdir)

    with open(root_keyfile) as f: root_private_key = f.read()
    with open(root_keyfile+".pub") as f: root_public_key = f.read()

    # VirtualBox internal network: org
    # Note: the VM *must* be configured to use the 'intnet' internal network
    with open("Organization.vbox") as vboxfile:
        assert vboxfile.read().count("intnet") >= 1
    run_cmd(['sed','-i','s/intnet/ictf/g',"Organization.vbox"], "sed replace intnet")

    mntdir = vmdir+"/mnt"
    os.mkdir(mntdir)
    run_cmd(['sudo','guestmount','-a','Organization-disk1.vdi','-i',mntdir], "guestmount")
    try:
        run_cmd(['sudo','mount','--bind','/dev',mntdir+'/dev'], "dev bind")
        mountdir_start_config(mntdir,
                ip='10.7.254.10',
                netmask='255.255.0.0',
                hostname="org",
                root_key=root_public_key,
                team_key="(disabled)",
                has_nat=True
                )
        mountdir_bash(mntdir, "passwd --lock ictf")
        mountdir_bash(mntdir, "mkdir -p /root/.ssh")
        mountdir_writefile(mntdir, "/root/.ssh/id_rsa", root_private_key)
        mountdir_writefile(mntdir, "/root/.ssh/id_rsa.pub", root_public_key)


        status(game_hash, "Configuring the organization DB, dashboard, bots...")


        mountdir_copydir(mntdir, "/org/database/", "/opt/database")
        infos = []
        for service_name in services:
            os.chdir("/services/"+service_name)
            with open("info.json") as jsonfile:
                info = json.load(jsonfile)
                info['getflag'] = read_service_script(info['getflag'])
                info['setflag'] = read_service_script(info['setflag'])
                info['benign'] = [ read_service_script(b) for b in info['benign'] ]
                infos.append(info)
        combined_info_json = json.dumps(infos, ensure_ascii=False, indent=1)
        mountdir_writefile(mntdir, "/opt/database/combined_info.json", combined_info_json)

        mountdir_copydir(mntdir, "/org/dashboard/", "/opt/dashboard")
        website_config = """name: %s
api_base_url: http://127.0.0.1:5000
api_secret: YOUKNOWSOMETHINGYOUSUCK
teams:
""" % game_name
        for team_id in range(1,len(teams)):
            assert re.match(r'[a-zA-Z0-9 _-]+\Z',teams[team_id]['name'])
            assert re.match(r'[a-zA-Z0-9 _-]+\Z',teams[team_id]['password'])
            website_config += "  %d:\n" % team_id
            website_config += "    name: %s\n" % teams[team_id]['name']
            website_config += "    hashed_password: %s\n" % teams[team_id]['password']
        mountdir_writefile(mntdir, '/opt/dashboard/config.yml', website_config)

        mountdir_copydir(mntdir, "/org/scorebot/", "/opt/scorebot")
        team_ips = []
        for team_id in range(1,len(teams)):
            team_ips.append({'team_id': team_id, 'ip': '10.7.%d.2'%team_id})
        scorebot_config = json.dumps(team_ips, indent=1)
        mountdir_writefile(mntdir, '/opt/scorebot/team_list.json', scorebot_config)

        mountdir_writefile(mntdir, "/opt/first_setup.sh", """#!/bin/bash

echo "Doing the first-run setup of the organization services"

set -x
set -e

cd /opt/database
cp gamebot.conf /etc/init
echo "manual" > /etc/init/gamebot.override
python reset_db.py %d
cp ctf-database.conf /etc/init
start ctf-database

cd /opt/dashboard
./install.sh
cp dashboard.conf /etc/init
start dashboard

cd /opt/scorebot
cp scorebot.conf /etc/init
start scorebot

echo "Done with the first setup! Check that everything is working and start your CTF!"

""" % (len(teams)-1))


        mountdir_writefile(mntdir, "/etc/issue", """
Organization VM (root password: ictf)

1. Do the first configuration by running /opt/first_setup.sh
2. Configure the network of this VM to expose it to the Internet
4. To start the CTF run 'start gamebot'

Note: You can login to TeamX's VM via ssh root@10.7.X.2.

""")
        mountdir_bash(mntdir, "chmod a+x /opt/first_setup.sh")

        status(game_hash, "Finalizing the organization VM")
        mountdir_end_config(mntdir)
        subprocess.call(["sudo","umount","-l",mntdir+'/dev'])
        run_cmd(['sudo','guestunmount',mntdir], "guestunmount")
    except:
        subprocess.call(["sudo","umount","-l",mntdir+'/dev'])
        subprocess.Popen(["sudo","guestunmount",mntdir]) # Do it in the background, in case it blocks
        raise



if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: {} <game_hash>".format(sys.argv[0])
        sys.exit(1)
    game_hash = sys.argv[1]
    try:
        logging.basicConfig(filename=LOG_DIR+'/game%s_vms.log' % game_hash, level=logging.DEBUG, format='%(asctime)s %(message)s')
        status(game_hash, "Started creating VMs")

        assert re.match(r'[a-zA-Z0-9]+\Z',game_hash)
        game = requests.get("http://ictf.cs.ucsb.edu/framework/ctf/"+game_hash).json()
        status(game_hash, "PENDING")

        game_name = game['name'];
        assert re.match(r'[a-zA-Z0-9 _-]+\Z',game_name)
        teams = game['teams']
        teams.insert(0,None) # Make it 1-based
        services = [ s['name'] for s in game['services'] ]

        logging.info("Name: %s", game_name)
        logging.info("Teams: %s", repr(teams))
        logging.info("Services: %s", repr(services))
        assert game['num_teams'] == len(teams)-1         # 1-based now
        assert game['num_services'] == len(game['services'])
        assert game['num_services'] == len(services)
        assert len(teams) < 200 # Avoid an IP conflict with the organization VM (10.7.254.10)

        gamedir = gamepath(game_hash)
        root_public_key = create_ssh_key(gamedir+"/root_key")

        create_org(game_hash, game_name, teams, services, gamedir+"/root_key")

        for team_id in range(1,len(teams)):
            team_public_key = create_ssh_key(gamedir+"/team%d_key"%team_id)
            create_team(game_hash, team_id, root_public_key, team_public_key, services)

        bundle(game_hash, "Organization", "root_key", game_hash)
        for team_id in range(1,len(teams)):
            team_hash = teams[team_id]['hash']
            bundle(game_hash, "Team%d"%team_id, "team%d_key"%team_id, team_hash)

        status(game_hash, "Cleaning up the build")
        shutil.rmtree(gamedir)

        status(game_hash, "READY")

    except:
        status(game_hash, "An error occurred. Contact us and report game ID %s" % game_hash)
        status(game_hash, "ERROR")
        logging.exception("Exception")
        raise
