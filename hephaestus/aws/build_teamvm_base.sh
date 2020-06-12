#!/bin/bash

packer validate ./0_teamvm_base/packer.json
packer build --force ./0_teamvm_base/packer.json
