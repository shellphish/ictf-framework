#!/bin/bash

packer validate ./ictf_base/packer.json
packer build --force ./ictf_base/packer.json
