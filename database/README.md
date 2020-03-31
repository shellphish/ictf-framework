# The Database

The database is responsible for the storage of all the information in the iCTF. 
An HTTP REST-style interface sits between the actual database and the other components. 
This API allows all the other components to report on the state of the game or query the state of the game.

## Vagrant VM

For your convenience, you can use a Vagrant VM for the database that will be provisioned automatically through Ansible. 
By default, Vagrant creates a VirtualBox VM, but you can choose any other provider (SSH, EC2, libvirt) and use the vagrant-migrate plugin if necessary.

Simply run:
```
    vagrant up
```
Note that depending on your Vagrant version, you might run into a bug that you might need to fix:
<https://github.com/mitchellh/vagrant/commit/9dbdb9397a92d4fc489e9afcb022621df7f60d11>.
This requires modifying the file:
`installation-path/vagrant/embedded/gems/gems/vagrant-1.8.1/plugins/provisioners/ansible/provisioner/guest.rb`
in the Vagrant installation. 
If the installation failed, the existing image must be removed.

First determine the name of the the image by executing:
```
    vagrant box list
```
to determine the name of the image.

Then execute:
```
    vagrant box destroy <name of the image>
```
to remove the vagrant image.

Then a new image must be installed using:
```
    vagrant up
```
Once the VM is provisioned, it will show you the API key that you need to write down for the other components. 
One can ssh into the machine (for debugging purposes) using:
```
    vagrant ssh
```
At this point, you should be able to access the database at: <http://localhost:8080/teams/info?secret=_APISECRET_>

If you need to debug problems, these are possible places to look for problems, on the database host:

1. nginx logfile: /var/log/nginx/access.log
2. uwsgi logfile: /var/log/upstart/ictf-database-api.log

## Ansible Playbook

You can simply install and configure the database via the Ansible playbook `setup.yml`. 
The playbook assumes that the database directory is rsync'd to `/opt/ictf/database` and that it runs on Ubuntu 14.04 (otherwise, package names might not exist, requirements might not be installed correctly, or the nginx/mysql paths might be incorrect).

The playbook will install all requirements, configures nginx and MySQL, creates the virtual environment, and sets up the ictf-database-api daemon.

## Create your own Box

To create a reusable Vagrant box, you can run:
```
    vagrant up
    vagrant package --output ictf-database-api
```
Please see <https://www.vagrantup.com/docs/cli/package.html> for more details on packaging a Vagrant VM.

## MySQL Performance Options

In the default configuration, Ansible deploys a development MySQL configuration. 
If you are planning to run a competition with the iCTF framework, then it is strongly recommended to change to the *high performance* section instead by commenting out the *development* section and removing the comments of the *high performance* section in `support/mysql.conf`.

## Manual Setup (not necessary when running with Vagrant or Ansible)

### Requirements

Install the required Ubuntu packages:

- nginx
- uwsgi
- uwsgi-plugin-python
- mysql-server
- python-pip
- python-virtualenv
- python-mysqldb
- python-dev

Then, install the Python requirements to a virtual environment via pip:
```
    pip install -r requirements.txt
```
You also need to install mysql-connector-python, which is currently broken on PyPI. 
Therefore, you need to install it manually:
```
    pip install ./support/mysql-connector-python-2.1.3/
```
### nginx Configuration

After the installation, it is necessary to create the nginx endpoint under `/etc/nginx/sites-available` by copying (and renaming) `support/nginx.conf`.

### uwsgi Daemon

You also might want to use the upstart service definition `support/service.conf` to create a daemon that you can easily start/stop (you
need to copy it to `/etc/init/<name>.conf`), on Ubuntu it will log to `/var/log/upstart/<name>.conf`.

### MySQL Setup

You need to create:
- the ictf database user with a password
- the ictf database tables (via `support/schema.sql`)

## Files

- `api`: The HTTP REST-like API, based on Flask.
- `wsgi.py`: The WSGI application that provides access to the API. 
  It can be   invoked using: `python wsgi.py`
- `uwsgi.ini`: The configuration file for the uWSGI server. 
  To run the WSGI application through uWSGI execute: `uwsgi -c wusgi.ini`. 
  Note that uWSGI shall be invoked through nginx for scalability. 
  In this setup, an nginx instance can distribute the load to a number of uWSGI servers.
- `settings.py`: settings for the database API. 
  The environment variable `ICTF_DATABASE_SETTINGS` must point at this file so that the app can be initialized.
- `support/schema.sql`: The SQL file containing the databse schema. 
  It should be used to initialize the database or to erase an existing one.
- `support/service.conf`: The Database API upstart script.
