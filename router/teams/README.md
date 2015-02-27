# Team Router

The following IPs are reserved by the infrastructure:
- Your VPN IP: 10.7.YOUR_TEAM_ID.1
- Your vulnerable box: 10.7.YOUR_TEAM_ID.2
- Your team router (reachable from your players): 10.7.YOUR_TEAM_ID.3
- Your VPN point-to-point (you might need this to configure your team router): 10.7.YOUR_TEAM_ID.254

Generally, the route to the game network is (should be pushed automatically)
```
route add -net 10.7.0.0/16 gw 10.7.TEAM.254
```

If the vulnerable box is hosted by the organizers, you need to add:
```
route add 10.7.YOUR_TEAM_ID.2 gw 10.7.YOUR_TEAM_ID.254
```
If it is hosted by you, you don't need to do anything.

Your clients/players should add a route to 10.7.0.0/16 through gateway
10.7.YOUR_TEAM_ID.3 to reach the game network:
```
route add -net 10.7.0.0/16 gw 10.7.YOUR_TEAM_ID.3
```
