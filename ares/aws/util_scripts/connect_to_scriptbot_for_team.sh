#!/bin/bash

set -euo pipefail

NUM_SCRIPTBOTS="27"
SCRIPTBOT_ID=$(python -c "print((($1 - 1) % $NUM_SCRIPTBOTS) + 1)")
echo "Running on scriptbot $SCRIPTBOT_ID"
ssh -o StrictHostKeyChecking=no -F ssh_config "scriptbot$SCRIPTBOT_ID"
