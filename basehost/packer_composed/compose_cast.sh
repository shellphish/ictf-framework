#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ "$1" == "check" ]; then SCRIPT="$SCRIPT_DIR/check_templates_match.py"; else SCRIPT="$SCRIPT_DIR/compose_template.py"; fi
OUT_DIR=$2
BUILDER=$3
MACHINE=$4
shift 4

ARGS="$OUT_DIR/${BUILDER}_cast_$MACHINE.json"
ARGS="$ARGS -t"
ARGS="$ARGS $SCRIPT_DIR/components/variables/common.json"
if [ -f "$SCRIPT_DIR/components/variables/${BUILDER}.json" ]; then ARGS="$ARGS $SCRIPT_DIR/components/variables/${BUILDER}.json"; fi
if [ -f "$SCRIPT_DIR/components/variables/${MACHINE}.json" ]; then ARGS="$ARGS $SCRIPT_DIR/components/variables/${MACHINE}.json"; fi
ARGS="$ARGS $SCRIPT_DIR/components/builders/${BUILDER}_layered.json"
ARGS="$ARGS $SCRIPT_DIR/components/provisioners/cast.json"
ARGS="$ARGS $SCRIPT_DIR/components/provisioners/cast_${MACHINE}.json"
ARGS="$ARGS -o variables->IMAGE_NAME=${MACHINE} -o variables->BUILD_STAGE=cast"
ARGS="$ARGS $@"

python "$SCRIPT" $ARGS