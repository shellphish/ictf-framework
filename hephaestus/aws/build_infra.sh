#!/bin/bash

printf "Building ictf_base...\n"
./build_ictf_base.sh

printf "\n\nBuilding teamvm base...\n"
./build_teamvm_base.sh

printf "\n\nBuilding teamvm primer...\n"
./build_teamvm_primer.sh

printf "\n\nBuilding ictf bastion...\n"
./build_ictf_bastion.sh