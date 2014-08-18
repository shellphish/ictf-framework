# Game Router

The concentrator should have two interfaces:
- eth0 should be the public interface (reachable by your players, so that they can access the game network)
- eth1 should be the game network

If the VMs are hosted by you (the organizers), make sure that you have a
dedicated route to your VMs. For instance, if you can reach your vulnerable VMs
via eth0:
```
TEAMS="<a list of space separated teams you have>"
for TEAMID in ${TEAMS}; do
    route add 10.7.${TEAMID}.2 dev eth1
done
```
Otherwise the concentrator will try to reach them via the team's router, which
will fail if you host them. If you take the default configuration, this should
work out of the box.

If the teams host the vulnerable boxes themselves, you need to add the following
line to the ictf-in-a-box.conf (OpenVPN configuration file):
```
client-to-client
```
