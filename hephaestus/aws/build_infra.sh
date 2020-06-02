#!/bin/bash

packer validate ./0_ictf_base/packer.json
packer build --force ./0_ictf_base/packer.json