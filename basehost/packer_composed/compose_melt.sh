#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ "$1" == "check" ]; then SCRIPT="$SCRIPT_DIR/check_templates_match.py"; else SCRIPT="$SCRIPT_DIR/compose_template.py"; fi
OUT_DIR=$2
BUILDER=$3
shift 3

ARGS="$OUT_DIR/${BUILDER}_melt.json"
ARGS="$ARGS -t"
ARGS="$ARGS $SCRIPT_DIR/components/variables/common.json"
ARGS="$ARGS $SCRIPT_DIR/components/variables/melt.json"
if [ -f "$SCRIPT_DIR/components/variables/${BUILDER}.json" ]; then ARGS="$ARGS $SCRIPT_DIR/components/variables/${BUILDER}.json"; fi

ARGS="$ARGS $SCRIPT_DIR/components/builders/${BUILDER}_layered.json"
ARGS="$ARGS $SCRIPT_DIR/components/provisioners/melt.json"
ARGS="$ARGS -o variables->IMAGE_NAME=ubuntu_amd64 -o variables->BUILD_STAGE=melt"
ARGS="$ARGS $@"

python "$SCRIPT" $ARGS