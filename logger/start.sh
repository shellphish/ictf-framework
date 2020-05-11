#!/bin/bash

update-rc.d elasticsearch defaults 95 10
service elasticsearch start 

/usr/share/kibana/bin/kibana --allow-root  
