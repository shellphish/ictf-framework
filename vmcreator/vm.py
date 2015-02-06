import re
import os
import json
import subprocess
import logging
import time

from utils import status
from utils import gamepath
from utils import run_cmd
from utils import mountdir_start_config
from utils import mountdir_bash
from utils import mountdir_writefile
from utils import mountdir_copydir
from utils import mountdir_end_config
from utils import read_service_script
from utils import mountdir_install_deb


def clone_vm(output_path, game_hash, base_vm, name, remote):
    assert re.match(r'[a-zA-Z0-9_-]+\Z',name)
    status(game_hash, "Creating VM: {}".format(name), remote)
    basepath = gamepath(output_path, game_hash)
    run_cmd(['VBoxManage', 'clonevm', base_vm, '--name', name, '--basefolder', basepath], "clonevm{}".format(name))
    return os.path.join(basepath, name)

def create_team(output_path, game_hash, team_id, root_key, team_key, team_password, services, remote):
    # XXX: see also create_org
    assert team_id < 200
    vmdir = clone_vm(output_path, game_hash, "iCTF-base", "Team{}".format(team_id), remote)
    status(game_hash, "Configuring the VM for Team {}".format(team_id), remote)
    os.chdir(vmdir)

    # VirtualBox internal network: teamXXX
    # Note: the VM *must* be configured to use the 'intnet' internal network
    with open("Team{}.vbox".format(team_id)) as vboxfile:
        assert vboxfile.read().count("intnet") == 1
    run_cmd(['sed', '-i', 's/intnet/ictf/g', 'Team{}.vbox'.format(team_id)], "sed replace intnet")

    mntdir = vmdir+"/mnt"
    os.mkdir(mntdir)
    guestmount_pidfile = guestmount('Team{}-disk1.vdi'.format(team_id), mntdir)
    try:
        run_cmd(['sudo', 'mount', '--bind', '/dev', '{}/dev'.format(mntdir)], "dev bind")
        mountdir_start_config(mntdir,
                ip='10.7.{}.2'.format(team_id),
                netmask='255.255.0.0',
                hostname="team{}".format(team_id),
                root_key=root_key,
                team_key=team_key
                )
        mountdir_bash(mntdir, "passwd --lock root")
        mountdir_bash(mntdir, "echo 'ictf:{}' | chpasswd".format(team_password))
        mountdir_writefile(mntdir, "/etc/sysctl.d/90-no-aslr.conf", "kernel.randomize_va_space = 0")
        mountdir_writefile(mntdir, "/etc/issue", """
Team {id} VM

The team should connect via:
      ssh -i team{id}_key ictf@<external_IP_to_reach_this_machine>

One can also login via this console (user: ictf, password: on the team web page)

Organizers can also login from their VM (ssh root@10.7.{id}.2).

""".format(id=team_id))

        status(game_hash, "Setting up the services for Team {}".format(team_id), remote)
        for service in services:
            assert re.match(r'[a-zA-Z0-9_-]+\Z',service)
            mountdir_install_deb(mntdir, '/ictf/services/{}.deb'.format(service))

        status(game_hash, "Finalizing the VM for Team {}".format(team_id), remote)
        mountdir_end_config(mntdir)
        subprocess.call(["sudo","umount",mntdir+'/dev'])
        guestunmount(mntdir, guestmount_pidfile)
    except:
        subprocess.call(["sudo","umount","-l",mntdir+'/dev'])
        subprocess.Popen(["sudo","guestunmount",mntdir]) # Do it in the background, in case it blocks
        raise


def create_org(output_path, game_hash, game_name, teams, services, root_keyfile, remote):
    # XXX: see also create_team
    vmdir = clone_vm(output_path, game_hash, "Organization-base", "Organization", remote)
    status(game_hash, "Configuring the organization VM", remote)
    os.chdir(vmdir)

    with open(root_keyfile) as f: root_private_key = f.read()
    with open(root_keyfile+".pub") as f: root_public_key = f.read()

    # VirtualBox internal network: org
    # Note: the VM *must* be configured to use the 'intnet' internal network
    with open("Organization.vbox") as vboxfile:
        assert vboxfile.read().count("intnet") >= 1
    run_cmd(['sed', '-i', 's/intnet/ictf/g', 'Organization.vbox'], "sed replace intnet")

    mntdir = vmdir+"/mnt"
    os.mkdir(mntdir)
    guestmount_pidfile = guestmount('Organization-disk1.vdi', mntdir)
    try:
        run_cmd(['sudo', 'mount', '--bind', '/dev', '{}/dev'.format(mntdir)], "dev bind")
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


        status(game_hash, "Configuring the organization DB, dashboard, bots...", remote)


        mountdir_copydir(mntdir, "/ictf/database/", "/opt/database")
        infos = []
        for service_name in services:
            os.chdir("/ictf/services/"+service_name)
            with open("info.json") as jsonfile:
                info = json.load(jsonfile)
                info['getflag'] = read_service_script(info['getflag'])
                info['setflag'] = read_service_script(info['setflag'])
                info['benign'] = [ read_service_script(b) for b in info['benign'] ]
                infos.append(info)
        combined_info_json = json.dumps(infos, ensure_ascii=False, indent=1)
        mountdir_writefile(mntdir, "/opt/database/combined_info.json", combined_info_json)

        mountdir_copydir(mntdir, "/ictf/dashboard/", "/opt/dashboard")
        website_config = """name: {}
api_base_url: http://127.0.0.1:5000
api_secret: YOUKNOWSOMETHINGYOUSUCK
teams:
""".format(game_name)
        for team_id, team in enumerate(teams, start=1):
            assert re.match(r'[a-zA-Z0-9 _-]+\Z',team['name'])
            assert re.match(r'[a-zA-Z0-9 _-]+\Z',team['password'])
            website_config += "  {}:\n".format(team_id)
            website_config += "    name: {}\n".format(team['name'])
            website_config += "    hashed_password: {}\n".format(team['password'])
        mountdir_writefile(mntdir, '/opt/dashboard/config.yml', website_config)

        mountdir_copydir(mntdir, "/ictf/scorebot/", "/opt/scorebot")
        team_ips = []
        for team_id, team in enumerate(teams, start=1):
            team_ips.append({'team_id': team_id, 'ip': '10.7.{}.2'.format(team_id)})
        scorebot_config = json.dumps(team_ips, indent=1)
        mountdir_writefile(mntdir, '/opt/scorebot/team_list.json', scorebot_config)

        mountdir_writefile(mntdir, "/opt/first_setup.sh", """#!/bin/bash

echo "Doing the first-run setup of the organization services"

set -x
set -e

cd /opt/database
cp gamebot.conf /etc/init
echo "manual" > /etc/init/gamebot.override
python reset_db.py {}
cp ctf-database.conf /etc/init
start ctf-database

cd /opt/dashboard
./install.sh
cp dashboard.conf /etc/init
start dashboard

cd /opt/scorebot
cp scorebot.conf /etc/init
start scorebot

echo
echo
echo "Done with the first setup! Check that everything is working and start your CTF! (run 'start gamebot')"

""".format((len(teams))))


        mountdir_writefile(mntdir, "/etc/issue", """
Organization VM (root password: ictf)

1. Do the first configuration by running /opt/first_setup.sh
2. Configure the network of this VM to expose it to the Internet
4. To start the CTF run 'start gamebot'

Note: You can login to TeamX's VM via ssh root@10.7.X.2.

Also, the VMs may not have all security updates installed.

""")
        mountdir_bash(mntdir, "chmod a+x /opt/first_setup.sh")

        status(game_hash, "Finalizing the organization VM", remote)
        mountdir_end_config(mntdir)
        subprocess.call(["sudo","umount","-l",mntdir+'/dev'])
        guestunmount(mntdir, guestmount_pidfile)
    except:
        subprocess.call(["sudo","umount","-l",mntdir+'/dev'])
        subprocess.Popen(["sudo","guestunmount",mntdir]) # Do it in the background, in case it blocks
        raise

def guestmount(what, where):
    pidfile = os.tempnam(None, 'guestmountpid')
    run_cmd(['sudo','guestmount','--pid-file',pidfile,'-a',what,'-i',where], "guestmount")
    assert os.path.isfile(pidfile)
    logging.info('guestmount pid file %s', pidfile)
    return pidfile

def guestunmount(mntdir, guestmount_pidfile):
    run_cmd(['sudo','guestunmount',mntdir], "guestunmount")
    logging.info('Waiting for guestmount (pidfile %s) to exit...', guestmount_pidfile)
    sleepcount = 0
    while sleepcount < 100:
        if subprocess.call(['pgrep','-F',guestmount_pidfile]) != 0:
            break
        sleepcount += 1
        if sleepcount % 10 == 0:
            logging.info('    still sleeping (count=%d)...', sleepcount)
        time.sleep(1)
    if sleepcount > 100:
        raise "guestmount seems stuck, exiting (pidfile: {})".format(guestmount_pidfile)
    logging.info('  All right, guestmount exited')
