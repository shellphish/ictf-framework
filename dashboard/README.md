Dashboard
=========

The dashboard is the website that runs the CTF. It lets users log in, discover the active services, check the services’ status, and submit flags. And, of course, check out the rankings :)


Structure
---------
The dashboard is designed to withstand a heavy load (hackers are F5-machines), without overloading the rest of the CTF infrastructure. This is why the web server, ```web.rb```, is short and nible, and exclusively talks to a Redis cache. The cache is populated by ```worker.rb```, which fetches updates from the central database every second.

You can start everything as a service (```start dashboard```), or manually with ```foreman start```.


API
---

All the data shown on the website pages is pulled from a JSON API, so that hackers can easily use it in scripts.
It’s as simple as
```
curl -u <TEAM_NAME>:<PASSWORD>  http://<DOMAIN>/scores
```
### Endpoints

* ```/services```: list the services names, their description, and the flag ids.
* ```/services_status```: shows if services are up or down
* ```/scores```: gives the current rankings
* ```/flag```: use this to submit a stolen flag. POST a ```{flag: <FLAG>}``` JSON hash
