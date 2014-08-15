#!/usr/bin/env python2.7

import glob
import logging
import os
import re
import subprocess
import sys
import tempfile


BASE_VM_NAME = "iCTF-base"
LOG_DIR = "/tmp"


#### General utilities ###################################################################

def status(status_msg):
    logging.info("Status: %s", status_msg)
    print status_msg

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

def create_gamepath(game_id):
    path = "/game/%d" % game_id
    try: 
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise
    return path




#### General VM interaction ##################################################################

def clone_vm(game_id, name):
    assert re.match(r'[a-zA-Z0-9_-]+\Z',name)
    status("Creating VM: {}".format(name))
    basepath = create_gamepath(game_id)
    run_cmd(["VBoxManage","clonevm",BASE_VM_NAME,"--name",name,"--basefolder",basepath], "clonevm "+name)
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


def mountdir_start_config(mntdir, ip, netmask, gw, hostname, root_key, team_key):
    # Network config
    mountdir_writefile(mntdir,'/etc/network/interfaces', """
auto lo
iface lo inet loopback
auto eth0
iface eth0 inet static
    address %s
    netmask %s
    gateway %s
""" % (ip, netmask, gw)
    )
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
    mountdir_writefile(mntdir, '/etc/rc.local', '#!/bin/sh -e\ndpkg-reconfigure openssh-server\nexit 0')
    mountdir_bash(mntdir, "chmod a+x /etc/rc.local")

    # Set a DNS server that works when chrooted in
    #     (mountdir_end_config will set the real one)
    mountdir_bash(mntdir,'rm -f /etc/resolv.conf')
    mountdir_writefile(mntdir,'/etc/resolv.conf', 'nameserver 8.8.8.8')

def mountdir_end_config(mntdir, nameserver):
    # Set the real DNS server
    mountdir_writefile(mntdir,'/etc/resolv.conf', 'nameserver '+nameserver)

def mountdir_install_deb(mntdir, deb_path):
    deb_filename = os.path.basename(deb_path)
    mountdir_copyfile(mntdir, deb_path, '/'+deb_filename)
    mountdir_bash(mntdir, "gdebi -q -n /"+deb_filename)




#### VM creation ############################################################################ 

def create_team(game_id, team_id, root_key, team_key, services):
    # XXX: see also create_org
    assert team_id < 200
    vmdir = clone_vm(game_id, "Team%d"%team_id)
    status("Configuring the VM for Team %d" % team_id)
    os.chdir(vmdir)

    # VirtualBox internal network: teamXXX
    # Note: the VM *must* be configured to use the 'intnet' internal network
    with open("Team%d.vbox"%team_id) as vboxfile:
        assert vboxfile.read().count("intnet") == 1
    run_cmd(['sed','-i','s/intnet/team%d/'%team_id,"Team%d.vbox"%team_id], "sed replace intnet")

    mntdir = vmdir+"/mnt"
    os.mkdir(mntdir)
    run_cmd(['sudo','guestmount','-a','Team%d-disk1.vdi'%team_id,'-i',mntdir], "guestmount")
    try:
        run_cmd(['sudo','mount','--bind','/dev',mntdir+'/dev'], "dev bind")
        mountdir_start_config(mntdir,
                ip='10.0.%d.2'%team_id,
                netmask='255.255.255.0',
                gw='10.0.%d.1'%team_id,
                hostname="team%d"%team_id,
                root_key=root_key,
                team_key=team_key
                )
        mountdir_bash(mntdir, "apt-get -qq install sl")

        status("Setting up the services for Team %d" % team_id)
        for service in services:
            assert re.match(r'[a-zA-Z0-9_-]+\Z',service)
            mountdir_install_deb(mntdir, '/services/%s.deb' % service)

        status("Finalizing the VM for Team %d" % team_id)
        mountdir_end_config(mntdir,
                nameserver='10.0.%d.1'%team_id
                )
        subprocess.call(["sudo","umount","-l",mntdir+'/dev'])
        run_cmd(['sudo','guestunmount',mntdir], "guestunmount")
    except:
        subprocess.call(["sudo","umount","-l",mntdir+'/dev'])
        subprocess.Popen(["sudo","guestunmount",mntdir]) # Do it in the background, in case it blocks
        raise
        

def create_org(game_id, root_key):
    # XXX: see also create_team
    vmdir = clone_vm(game_id, "Organization")
    status("Configuring the organization VM")
    os.chdir(vmdir)

    # VirtualBox internal network: org
    # Note: the VM *must* be configured to use the 'intnet' internal network
    with open("Organization.vbox") as vboxfile:
        assert vboxfile.read().count("intnet") == 1
    run_cmd(['sed','-i','s/intnet/org/',"Organization.vbox"], "sed replace intnet")

    mntdir = vmdir+"/mnt"
    os.mkdir(mntdir)
    run_cmd(['sudo','guestmount','-a','Organization-disk1.vdi','-i',mntdir], "guestmount")
    try:
        run_cmd(['sudo','mount','--bind','/dev',mntdir+'/dev'], "dev bind")
        mountdir_start_config(mntdir,
                ip='10.0.0.10',
                netmask='255.255.255.0',
                gw='10.0.0.1',
                hostname="org",
                root_key=root_key,
                team_key="(disabled)"
                )

        status("Setting up the organization DB, scorebot, etc.")
        mountdir_copydir(mntdir, "/org", "/org")
        for scriptpath in glob.glob("/org/*.sh"):
            scriptname = os.path.basename(scriptpath)
            mountdir_bash(mntdir, "bash /org/"+scriptname)

        status("Finalizing the organization VM")
        mountdir_end_config(mntdir,
                nameserver='10.0.0.1'
                )
        subprocess.call(["sudo","umount","-l",mntdir+'/dev'])
        run_cmd(['sudo','guestunmount',mntdir], "guestunmount")
    except:
        subprocess.call(["sudo","umount","-l",mntdir+'/dev'])
        subprocess.Popen(["sudo","guestunmount",mntdir]) # Do it in the background, in case it blocks
        raise



if __name__ == '__main__':
    assert len(sys.argv) >= 3
    game_id = int(sys.argv[1])
    try:
        logging.basicConfig(filename=LOG_DIR+'/game%d_vms.log' % game_id, level=logging.DEBUG, format='%(asctime)s %(message)s')
        
        if sys.argv[2] == 'team':
            assert len(sys.argv) >= 6
            team_id = int(sys.argv[3])
            with open(sys.argv[4]) as rootkeyfile:
                root_key = rootkeyfile.read()
            with open(sys.argv[5]) as teamkeyfile:
                team_key = teamkeyfile.read()
            services = sys.argv[6:]
            create_team(game_id, team_id, root_key, team_key, services)
        elif sys.argv[2] == 'org':
            assert len(sys.argv) == 4
            with open(sys.argv[3]) as rootkeyfile:
                root_key = rootkeyfile.read()
            create_org(game_id, root_key) 
        else:
            print "Usage: {} game_id (team|org) ...".format(sys.argv[0])
            sys.exit(1)

    except:
        status("An error occurred. Contact us and report game ID %d" % game_id)
        logging.exception("Exception")
        raise
