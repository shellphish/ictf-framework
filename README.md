# The iCTF Framework 3.0

This is the framework that [Shellphish](http://www.shellphish.net) uses to host the [iCTF](http://ictf.cs.ucsb.edu).

The iCTF Framework is described in a [paper](https://www.usenix.org/conference/3gse14/summit-program/presentation/vigna) presented at the Usenix 3GSE workshop in 2014. 

We released this in the hope that it allows educators and trainers to host their own A/D CTFs. 
This framework is free for commercial use, but the support that we can provide is limited.

We are planning to release more technical documentation regarding each components in the future; as for now you can find instruction on how to create a game [here](https://github.com/shellphish/ictf-framework/wiki/running-a-class-ctf). 

If you have questions, please send an email to ctf-admin@lists.cs.ucsb.edu. 

**DISCLAIMER**: This framework is still a work in progress and this release have to be considered a **BETA** version. New pull requests and new issues are welcome :)

## TODOs and known issues

- The codebase needs to be cleaned from old pieces of unused code.
- Finish to port every component to python 3.
- Finish to document the various components.
- Extend the framework to support multiple cloud providers other than AWS.
- The CTF cannot be run for more than 12 hours because the credentials we use to login to the docker registry will expire after such time and we currently don't have a way to renew them when the game is running.

## Database

This is the central database that tracks the state of the game. 
It runs on the Database VM and exposes a RESTful API.  
Note that this database should not be directly accessed by the teams, which instead should go through the team services component.   

## Gamebot

The Gamebot is the component responsible for advancing the competition. 
The competition is divided into ticks. 
At the beginning of each tick, the gamebot decides which scripts need to be executed by the scriptbot (e.g., scripts to set flags, retrieve flags, or test services) and writes the schedule in the central database. 
Then, it extracts from the database the data about the previous tick (e.g., flag submitted and the status of service checks) and computes the points to be assigned to each team. 
The new scores are stored in the database, so that they can be displayed by the dashboard component. 

## Scriptbot

The scriptbot is responsible for the execution of the scripts scheduled by the gamebot. 
The scriptbot extracts the scripts scheduled for execution from the central database, and then runs them. 
For example, the scripts retrieve flags that have been set in the previous tick, or check if the services are up and functional. 

## Router

The router component is responsible for routing the traffic between the teams in the competition. 
The component implements an OpenVPN service. Each team is given a VM that acts as the router for the team.
The traffic among teams needs to be anonymized to prevent teams from distinguishing scriptbot-generate traffic from team traffic.

## Creating a CTF competition

For more information visit our wiki page about [running a class CTF](https://github.com/shellphish/ictf-framework/wiki/running-a-class-ctf)

