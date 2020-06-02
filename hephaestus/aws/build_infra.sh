#!/bin/bash

packer validate ./ami_ictf_base/packer.json
packer build --force ./ami_ictf_base/packer.json