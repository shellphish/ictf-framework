# The iCTF Framework

This is the framework that the UC Santa Barbara [Seclab](http://seclab.cs.ucsb.edu) and [Shellphish](http://www.shellphish.net) use to host the [iCTF](http://ictf.cs.ucsb.edu).
The initial framework has been expanded by the Arizona State University [SEFCOM](http://sefcom.asu.edu/), to allow for cloud-based deployments.

This [framework](http://ictf.cs.ucsb.edu/framework) can be used to create Capture The Flag (CTF) competitions. 
In the following discussion, we assume that the reader has a precise understanding of how CTF competitions work.

The iCTF Framework is described in a [paper](https://www.usenix.org/conference/3gse14/summit-program/presentation/vigna) presented at the Usenix 3GSE workshop in 2014. 
That paper and presentation detail the history, philosophy, and design of the framework.

We released this framework in the hope that it allows educators and trainers to host their own CTFs. 
This framework is free for commercial use, but the support that we can provide is limited. 
If you have questions, please send an email to ctf-admin@lists.cs.ucsb.edu. 

Currently, attack-defense CTFs are the focus of the framework, but we are planning to develop support for other formats as well (e.g., Jeopardy-style competitions). 

Pull requests are always welcome!

The framework creates several virtual machines (VMs), a few for the organizers and one for every team. 
The components that run on each VM are described below.

## Central Database

This is the central database that tracks the state of the game. 
It runs on the Database VM and exposes a RESTful API.  
Note that this database should not be directly accessed by the teams, which instead should go through the team services component.   
Additional documentation is available [here](database/README.md).

## Gamebot

The Gamebot is the component responsible for advancing the competition. 
The competition is divided into ticks. 
At the beginning of each tick, the gamebot decides which scripts need to be executed by the scriptbot (e.g., scripts to set flags, retrieve flags, or test services) and writes the schedule in the central database. 
Then, it extracts from the database the data about the previous tick (e.g., flag submitted and the status of service checks) and computes the points to be assigned to each team. 
The new scores are stored in the database, so that they can be displayed by the dashboard component. 
Additional documentation is available [here](gamebot/README.md).

## Scriptbot

The scriptbot is responsible for the execution of the scripts scheduled by the gamebot. 
The scriptbot extracts the scripts scheduled for execution from the central database, and then runs them. 
For example, the scripts retrieve flags that have been set in the previous tick, or check if the services are up and functional. 
Additional documentation is available [here](scriptbot/README.md).

## Dashboard

The dashboard displays the teams' scores and the services' status. 
Additional documentation is available the [here](dashboard/README.md).

## Team Services

The team services component allows the teams to interact with the game. 
All team-specific functionality is handled by this component.
For example, this component is responsible for the registration of the teams, for the submission of flags during the competition, and so on.
The functionality of this component is accessed by each team through a Python module, called iCTF, which implements the client-side functionality of this module. 
Additional documentation is available [here](team_services/README.md). 

## Router

The router component is responsible for routing the traffic between the teams in the competition. 
The component implements an OpenVPN service. Each team is given a VM that acts as the router for the team.
The traffic among teams needs to be anonymized to prevent teams from distinguishing scriptbot-generate traffic from team traffic.
Additional documentation is available [here](router/README.md).

## Services

The iCTF Framework provides a standard format for services. 
For example, services must have scripts to set and retrieve the flag according to a specific format. 
A number of services are included in the framework, and other can be added to extend it. 
Services live in the `services` directory.

## VM Creator

The VM creator is responsible for generating the VMs necessary to run the competition. 
Additional documentation is available [here](vmcreator/README.md).

# Creating a CTF competition

In the following we detail the steps necessary to create and run a CTF competition.

## Selecting the services

The first task is to select the services that will be part of the vulnerable image.
The services can be chosen from the set provided with the distribution, under the directory `service_library`.
Otherwise, they can be developed using as a reference the services distributed in the `public_service_samples` directory.
Services are included in the vulnerable image by creating under the `services` directory a symbolic link to the chosen service directory.

## Starting the database

The database is the core component of the iCTF Framework.
To start the database, enter the database directory and follow the instructions in the corresponding README.

## Starting the team services

Once the database is up an running, it is necessary to set up the team services component, which allows the teams to register for the competition.

# Submitting your own iCTF service

See `service_submission_process.md`

