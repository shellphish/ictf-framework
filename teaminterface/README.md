# The iCTF Team Interface

The iCTF Team Interface implements the public API which teams, players, and their clients can use to interact with the game.
This includes the official iCTF Python Client (available through pip)

Through this API server, players can:
  - Create accounts
  - Submit scripts/services/exploits (depending on the game mode)
  - Get targets and Flag IDs
  - Submit flags
  - Check scores and other game data

The Team Interface is a Flask/uwsgi application.
The Team Interface is effectively a thin authentication, sanitization, and caching layer around the central iCTF DB API.


## Installation with Vagrant

Using Vagrant makes installation easy!

0. Set up the iCTF Database API (see "../database") and make a note of its URL and API secret generated during installation

1. Edit `config.py`, changing all options to match your envrionment (see `config.py.example`).

2. `vagrant up`


## Manual Installation

0. The Team Interface relies upon, and will not function without, the iCTF Database.
Set that up first, create an API key, and edit config.py, changing DB_API_URL_BASE and DB_API_SECRET to match your configuration.

1. You'll also need to get access to a mailserver, so that the Team Interface can send out account information.  Edit the mail templates and SMTP server information in lib/mailer.py to your liking.

2. Ensure that you set the 'SECRET_KEY' parameter in config.py.  This is used to create and verify login tokens.  NOTE: Changing it will log everyone out!

3. See reqs.txt for a list of Python dependencies you'll need.  These include the python modules to support the app's functionality (Flask, etc), as well as the application server it runs on, usually uwsgi.
You'll likely want to set this up in a python virtualenv environment.
Assuming Ubuntu 14.04 with the 'virtualenvwrapper' package installed, you can do:

`$ mkvirtualenv ictf`

`$ workon ictf`

`$ pip install -r reqs.txt`

4. Install redis. (e.g. `apt-get install redis-server redis-tools`)  The default configuration for most distributions is fine.

5. Install nginx.  See your distribution's configuration and the nginx documentation for details on how to configure nginx to communicate with a Flask/uwsgi application.


## Running

You can run the server using uwsgi with:

```
uwsgi --http 8080 --chmod-socket --module team_interface --die-on-term
```

For debugging and development:

```
python start.py
```


## Usage with the ictf client

Once running, clients can interact with the Team Interface using its RESTful JSON API.
The fastest way to do this is to leverage the `ictf` python client.  You can find it on pip:
`pip install ictf`

With it installed, you can do the following to, for example, register a team:

`$ python`

`>>> from ictf import iCTF`

`>>> i = iCTF("http://your.hostname.here/")`

`>>> i.register_wizard()`

If this succeeds, your Team Interface and DB are working, and you should be good to go!


## Information for Players

The easiest way for players to access your game is to direct them to use the iCTF Python module.
On a normal *nix system with Python and pip installed, they can just execute `pip install ictf` to install it.

You will need to distribute the URL to your Team Interface for teams to register and login.

Teams can then refer to the instructions provided with the iCTF client, making sure to use the provided Team Interface URL when
creating the iCTF object,

See the `ictf` module's documentation for more information on its usage.


## Information for Organizers

### Tools and Scripts
As the game administrator, there are a few useful tools included to help make your life easier.
The team registration process includes an optional questionnaire, which is answered through the Team Interface.
You can edit the "metadata_questions" file, and run meta_add.py to push them into the DB.
Additionally, team_list.py will dump some useful metadata about registered teams.

### Game switches
There are three switches in config.py which control the various phases of the game life-cycle.
Setting registration_open to False will close team registration, but still allows teams to submit game artifacts, reset passwords, and so on.
Setting submission_open to False closes off artifact submissions only.
Setting game_started to True will enable all game-time functions, such as getting Flag IDs, setting Flags, and so on.

### Verification
When teams register, they must be "validated" in order to play.  You can do this using `validate.py` -- Just run it alongside the running Team Interface, and it will present you with a list of teams with metadata information, and prompt for your validation decision.

### Distributing VM Bundles
In an attack-defense game type, teams will host VM bundles containing the vulnerable services.
These can be distributed through the iCTF Team Interface and the iCTF Client.
The client distributes two types of bundles: "test" and "real".  Test bundles are used by teams to check whether they can successfully host a VM in their environment, without spoiling the game's content, where as "real" bundles contain all game services.
Once you've generated VM Bundles using VM Creator, configure the two options in config.py to set the paths where the bundles will be served from.  Team bundles will be named <team_id>.tgz
See VM Creator's documentation for more details.


## Usage with the REST Interface

You can also query the REST interface directly.
All queries are made in the usual JSON/REST way -- the "Parameters" below describe the keys to the JSON object to be submitted as POSTDATA
All queries, other than `/api/login`, `/api/reset`, and `/api/team` require authentication.  The Team Interface uses HTTP Basic Authentication; supply the token obtained from `/api/login` as the username, and an empty string for the password.

|*API Endpoint*|*Method*|*Parameters*|*Returns*|*Description*|
| ------------ | ------ | ---------- | ------- | ----------- |
| `/api/login`| POST   | emaeil, password (strings) | token (string) | Log into iCTF |
| `/api/team` | POST   | name (string), team_email (string email), url (string), country (2-letter country code string, logo (256x256 PNG, base64-encoded), metadata (list of string answers to metadata questions) | ASCII-art captcha | Basic team info | Registers a team |
| `/api/team/verify` | POST | response (string, captcha solution) | result (success, fail) | Verify a team registration |
| '/api/metadata' | GET | None | metadata (list of strings) | Get the list of organizer-defined metadata questions |

TODO: Finish this


## Known issues and TODOs

- User authentication tokens aren't revocable.  They do have a shelf-life though, and if you're worried, you can shorten it.
- We'd like to make the three flags mentioned above actually on real timers based on the DB.
- There have been scattered reports of issues submitting flags, where the submitted flags appears as "None" on the server.  We suspect, due to the limited scope of the problem, that this is a client environment issue.  In response, we have implemented the "notaflag" return value for `/api/flag` to signal when something like this has happened.

### Version
2015-1

### Tech
The Team Interface uses a few interesting packages internally:

* Flask - Nice web app framework
* Flask-RESTFul - Fancy shortcuts for building API servers
* Flask-Cache - Redis integration for caching of big DB queries
* passlib - Generation of auth tokens
* requests - web request library
* sendgrid - delivers emails effortlessly
