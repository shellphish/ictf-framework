#!/bin/bash

packer validate ./ictf_bastion/packer.json
packer build --force ./ictf_bastion/packer.json
