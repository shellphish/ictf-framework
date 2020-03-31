# Dashboard

The dashboard is the website that displays the status of the iCTF.
=======
The scoreboard is the website that shows the iCTF statistics, such as: team info,
list of services, team scores and so forth.  By default, it will start a website at
http://<hostmachines IP>:9090/

## Overview

The iCTF scoreboard is composed of several scripts.
It is assumed that the central database containing all the game data is deployed somewhere and can be accessed through an API.  The API location and API secret are stored in  ../secrets/


```
+----------------Scoreboard Server------------------------+
|                                                         |               +---------------+
|    +-------------+                    +-------------+   |               |               |
|    |             |                    |             |   |               |               |
|    |   Redis     | <------------------+  Poller.py  | <-----------------+    iCTF DB    |
|    |   Server    |                    |             |   |               |               |
|    |             |                    |             |   |               +---------------+
|    +------+------+                    +-------------+   |
|           |                                             |
|           |                                             |
|           +                                             |
|    +-------------+                  +--------------+    |
|    |             |                  |              |    |               +--------------+
|    |  Flask API  |                  |    nginx     |    |               |              |
|    |   (app.py)  | +--------------> |              | <------------------+    Teams     |
|    |             |                  |              |    |               |              |
|    +-------------+                  +--------------+    |               |              |
|                                                         |               +--------------+
+---------------------------------------------------------+
```
### Poller & Pusher
A python script called poller.py retrieves data from the central database once per game tick. When new data is retrieved, the poller stores it in a redis cache.
The Poller application is run via the upstart file /etc/init/ictf-poller.conf.  The service runs the python application under the userid 'deploy'.

Pusher, is a flask-based web app (i.e., app.py), serves the client requests by fetching  data from the redis cache.


#### Configuration file
Both python applications take a configuration file as an argument.  A configuration file is provided to make this scoreboard implementation independent of the central database implementation. The default is config.json and is located in the /opt/ictf/scoreboard directory.

The db_host and db_port fields are populated as a part of the Ansible script from the files in the /opt/ictf/secrets directory.

The configuration file is used by both the poller and by the flask app.
It contains the definition of the following keys:
* db_host: IP address of the central database
* db_port: port to access the central database
* secret: secret passhprase to access the central database
* redis_host: IP address of the machine hosting the redis server
* redis_port: port to access the redis database
* redis_db_id: id of the redis database instance
* polling_sleep_time: number of seconds the poller has to wait before checking whether the tick changed
* setup_sleep_time: the number of seconds the poller has to wait after a tick change to be sure all fluctuations are over
* dynamic_endpoints (list): list of endpoints the poller has to query every tick
* static__endpoints(list): list of endpoints the poller has to query only once
* tick_endpoint: endpoint to retrieve the current tick
### Gunicorn
Python WSGI HTTP Server for UNIX. It’s a pre-fork worker model ported from Ruby’s Unicorn project.  The master never knows anything about individual clients. All requests and responses are handled completely by worker processes.

gUnicorn is run as an upstart service.  The service configuration file is located at
/etc/init/ictf-gunicorn.conf

### Web

The http requests are serviced by nginx.  The nginx website configuration file is located at /etc/nginx/sites-available/ictf-team_interface.conf The configuration links to
/opt/ictf/scoreboard/_static

### Static frontend information

The frontend is compiled via nodejs. Compiled HTML, JS and CSS files can be
copied on any web server and don't require nodejs to run.

Compilation relies on:

* Node.js >= 6
* npm >= 2.14.7

#### Setup nodejs dev environment

    curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.0/install.sh | bash # install NVM
    nvm install 6 # install nodejs v6
    nvm alias default 6
    npm install

#### Development of nodejs application

    npm start

To start local server on http://127.0.0.1:5000/ (with livereload)

#### Build for production

    npm run build

## Installation
Scoreboard is now using Vagrant/Ansible to perform the creation and configuration of a VM for the scoreboard.
The VagrantFile is located in the same directory as this README.

## Troubleshooting
* The webpage is not coming up in your web browser on the defualt port of 9090.
	This is likely because the webserver hasn't started for some reason.  Check the webserver log files.  The log files are located at /var/log/nginx/

* The information is not getting updated.
	1) Make sure both services are running
		$ sudo service ictf-poller status
		$ sudo service ictf-gunicorn status
	2) check the redis server to see if it's getting inputs and outputs
		$ redis-cli monitor
