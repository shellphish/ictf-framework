#!/bin/bash

set -euo pipefail
NUM_SCRIPTBOTS="$1"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

"$DIR/run_on_scriptbots.sh" "$NUM_SCRIPTBOTS" 'cd /opt/ictf/scriptbot; git pull; sudo service scriptbot restart; sudo service scriptbot status; echo $?'