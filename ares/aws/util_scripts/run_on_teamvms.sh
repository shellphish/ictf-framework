#!/bin/bash

set -euo pipefail

NUM_TEAMS="$1"
CMD="$2"

for i in $(seq 1 "$NUM_TEAMS");
do
  echo "Running on teamvm $i"
  ssh -o StrictHostKeyChecking=no -F ssh_config "teamvm$i" $CMD
done
