#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$1" == "check" ]; then SCRIPT="$SCRIPT_DIR/check_templates_match.py"; else SCRIPT="$SCRIPT_DIR/compose_template.py"; fi

UBUNTU_VERSION="${ICTF_UBUNTU_VERSION:-18.04}"

OUT_DIR=$2
BUILDER=$3
shift 3

ARGS="$OUT_DIR/${BUILDER}_heat_$UBUNTU_VERSION.json"
ARGS="$ARGS -t"
ARGS="$ARGS $SCRIPT_DIR/components/variables/common.json"
ARGS="$ARGS $SCRIPT_DIR/components/variables/heat.json"
if [ -f "$SCRIPT_DIR/components/variables/${BUILDER}.json" ]; then ARGS="$ARGS $SCRIPT_DIR/components/variables/${BUILDER}.json"; fi
ARGS="$ARGS $SCRIPT_DIR/components/builders/${BUILDER}_ubuntu_$UBUNTU_VERSION.json"
ARGS="$ARGS $SCRIPT_DIR/components/provisioners/heat.json"

ARGS="$ARGS -o variables->IMAGE_NAME=ubuntu_amd64_${UBUNTU_VERSION}"
ARGS="$ARGS -o variables->BUILD_STAGE=heat"
ARGS="$ARGS -o variables->BASE_IMAGE_NAME=eval(None)"

ARGS="$ARGS $@"

python "$SCRIPT" $ARGS