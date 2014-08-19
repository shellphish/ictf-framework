# The iCTF Framework

This is the framework that the UC Santa Barbara Seclab uses to host the iCTF, and that can be used to create your own CTFs at http://ictf.cs.ucsb.edu/framework. The framework creates several VMs: one for the organizers and one for every team. The components that run on each are described below.

We released this framework in the hope that it creates a focal point for hosting CTFs. Currently, attack-defense CTFs are the focus, but we are interested in other formats as well. Pull requests are always welcome!

The CTF Framework contains several components, described below.

## Central Database

This is the central database that tracks the game state. It runs on the Organizer VM and exposes a REST API.

## Scorebot

The scorebot runs on the central database, updates flags on the vulnerable services, and checks that these flags are accessible.

## Router

This directory contains routing configuration for the central organizer/scorebot VM.

## Dashboard

This is the CTF dashboard, showing the scoreboard and allowing players to submit flags. Read the [docs](dashboard/README.md)

## VM Creator

This is the VM creater that is used by http://ictf.cs.ucsb.edu/framework to create organizer and team VMs.

## Services

The iCTF Framework includes a standard format for creating services. Services live in the services/ directory.

## Further Information

The iCTF Framework is described in a paper presented at Usenix 3GSE 2014 (https://www.usenix.org/conference/3gse14/summit-program/presentation/vigna). That paper and presentation detail the history, philosophy, and design of the framework.
