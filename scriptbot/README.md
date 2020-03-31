# The Scriptbot

The scriptbot is responsible for checking the service status of all teams. 
It updates flags on the vulnerable services, and checks that these flags are accessible. 
Each service has at least one setflag, one getflag, and one benign script. 

The setflag and getflag scripts are used to check the status of the service by setting and getting the flags, while the benign script is used to create some benign background traffic. 
The scriptbot pulls these scripts and corresponding execution intervals from the database.

A json file 'team_list.json' needs to be updated with team and IP address
information in the following format:

```json
[
{"team_id":1,"ip":"127.0.1.2"},
{"team_id":2,"ip":"127.0.2.2"}
]
```