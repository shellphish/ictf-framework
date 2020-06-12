#!/bin/bash

packer validate ./1_teamvm_primer/packer.json
packer build --force ./1_teamvm_primer/packer.json
