#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$1" == "check" ]; then SCRIPT="$SCRIPT_DIR/check_templates_match.py"; else SCRIPT="$SCRIPT_DIR/compose_template.py"; fi

OUT_DIR=$2
BUILDER=$3
shift 3

ARGS="$OUT_DIR/${BUILDER}_harden.json"
ARGS="$ARGS -t"
ARGS="$ARGS $SCRIPT_DIR/components/variables/common.json"
if [ -f "$SCRIPT_DIR/components/variables/${BUILDER}.json" ]; then ARGS="$ARGS $SCRIPT_DIR/components/variables/${BUILDER}.json"; fi
ARGS="$ARGS $SCRIPT_DIR/components/builders/${BUILDER}_layered.json"
ARGS="$ARGS $SCRIPT_DIR/components/provisioners/harden.json"
ARGS="$ARGS -o variables->BUILD_STAGE=harden"
ARGS="$ARGS $@"

python "$SCRIPT" $ARGS