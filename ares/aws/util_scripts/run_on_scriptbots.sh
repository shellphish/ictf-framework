#!/bin/bash

set -euo pipefail

NUM_SCRIPTBOTS="$1"
((LAST_SCRIPTBOT=NUM_SCRIPTBOTS-1))
CMD="$2"

for i in $(seq 0 "$LAST_SCRIPTBOT");
do
  echo "Running on scriptbot $i"
  ssh -o StrictHostKeyChecking=no -F ssh_config "scriptbot$i" $CMD
done
