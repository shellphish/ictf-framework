# The Scriptbot

The scriptbot is responsible for checking the service status of all teams. It updates flags on the vulnerable services and checks that those flags are accessible. Each service has at least one setflag, one getflag, and one benign script.

## Scripts

Each script is one of the following:

- setflag : registers a new flag with the team's service.
- getflag : verifies that the team's service is up and functioning.
- benign  : masks the getflag and setflag routines by hiding it in traffic.


Note that there may be several executions of benign and getflag in the same
tick against the same team service, but only one execution of setflag.
Also, getflag cannot execute until setflag has run.

## Tasks per Tick

Each tick, the Gamebot pushes a set of scripts to be run into the RabbitMQ dispatcher.
The dispatcher distributes the tasks to each running instance of ScriptBot. The scriptbot
instance receives a list of teams and the corresponding scripts to run against them. Before executing the scripts, however, the Scriptbot first pulls the latest version of the scripts from the Docker registry.

A task received from the dispatcher is a JSON file with two parts: 'teams' and 'services'.
'teams' is a dict of teams that scriptbot needs to interact with.
Each team contains a dictionary of services.
Each service contains a list of scripts to be run against that service.

The "script_id" indicates what type of script this is (eg: getflag on service X).
The "script_type" and "script_name" indicate the name of the script (eg: getflag).
The "execution_id" is a database ID for the results of this tick's script execution
against the given team.


```json
{
    'teams' : {
        team_id : {
            service_id : {
                [
                    {
                        'execution_id' : execution_id,
                        'script_name' : script_name,
                        'script_type' : script_type,
                        'script_id' : script_id,
                    }
                ]
            }
    },
    'services' : {
        service_id : {
            'service_name' : service_name,
            'port' : service_port
        }
    }
}
```
