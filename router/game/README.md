# Game Router

The game router should have two interfaces:
- eth0 should be the public interface (reachable by the teams, so that they can access the game network)
- eth1 should be the game network

If the VMs are hosted by the organizers, the organizers must make sure that they have a dedicated route from the game router to their VMs. 
For instance, if one can reach the vulnerable VMs via eth0:
```
TEAMS="<a list of space separated teams you have>"
for TEAMID in ${TEAMS}; do
    route add 10.7.${TEAMID}.2 dev eth1
done
```

Otherwise the game router will try to reach them via the team's router, which will fail if the organizers host the vulnerable VM. 
If the organizers use the default configuration, this should work out of the box.

If the teams host the vulnerable boxes themselves, the organizers need to add the following line to the ictf-in-a-box.conf (OpenVPN configuration file):

```
client-to-client
```