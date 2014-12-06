# The Scorebot

The scorebot is responsible for checking the service status of all teams. It updates flags on the vulnerable services, and checks that these flags are accessible. Each service has at least one <i>setflag</i>, one <i>getflag</i>, and one <i>benign</i> script. The <i>setflag</i> and <i>getflag</i> scripts are used to check the status of the service by setting and getting the flags, while the <i>benign</i> script is used to create some benign traffic. Scorebot pulls these scripts and corresponding execution intervals from the database.

A json file 'team_list.json' needs to be updated with team and ip information in the following format.

```json
[
{"team_id":1,"ip":"127.0.1.2"},
{"team_id":2,"ip":"127.0.2.2"}
]
```
