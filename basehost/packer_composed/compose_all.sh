#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TO_CHECK_OR_TO_COMPOSE="$1"
OUT_DIR=$2
BUILDER=$3
shift 3

#$SCRIPT_DIR/compose_cast.sh "$OUT_DIR" "$BUILDER" "ami_heat_16_04.json"


echo "Running $TO_CHECK_OR_TO_COMPOSE on heat template!"
$SCRIPT_DIR/compose_heat.sh "$TO_CHECK_OR_TO_COMPOSE" "$OUT_DIR" "$BUILDER" || [ "$TO_CHECK_OR_TO_COMPOSE" == "check" ]
ICTF_UBUNTU_VERSION=16.04 $SCRIPT_DIR/compose_heat.sh "$TO_CHECK_OR_TO_COMPOSE" "$OUT_DIR" "$BUILDER" || [ "$TO_CHECK_OR_TO_COMPOSE" == "check" ]



echo "Running $TO_CHECK_OR_TO_COMPOSE on melt template!"
$SCRIPT_DIR/compose_melt.sh "$TO_CHECK_OR_TO_COMPOSE" "$OUT_DIR" "$BUILDER" || [ "$TO_CHECK_OR_TO_COMPOSE" == "check" ]

for MACHINE in database gamebot router scoreboard scriptbot teaminterface logger;
do
    echo "Running $TO_CHECK_OR_TO_COMPOSE on $MACHINE cast template!"
    $SCRIPT_DIR/compose_cast.sh "$TO_CHECK_OR_TO_COMPOSE" "$OUT_DIR" "$BUILDER" "$MACHINE" $@ || [ "$TO_CHECK_OR_TO_COMPOSE" == "check" ]
    #read -n 1 -p "Continue?" mainmenuinput
done

echo "Running $TO_CHECK_OR_TO_COMPOSE on harden template!"
$SCRIPT_DIR/compose_harden.sh "$TO_CHECK_OR_TO_COMPOSE" "$OUT_DIR" "$BUILDER" || [ "$TO_CHECK_OR_TO_COMPOSE" == "check" ]



echo "Running $TO_CHECK_OR_TO_COMPOSE on teamvm_base template!"
$SCRIPT_DIR/compose_teamvm_base.sh "$TO_CHECK_OR_TO_COMPOSE" "$OUT_DIR" "$BUILDER" || [ "$TO_CHECK_OR_TO_COMPOSE" == "check" ]

echo "Running $TO_CHECK_OR_TO_COMPOSE on teamvm_primed template!"
$SCRIPT_DIR/compose_teamvm_primed.sh "$TO_CHECK_OR_TO_COMPOSE" "$OUT_DIR" "$BUILDER" || [ "$TO_CHECK_OR_TO_COMPOSE" == "check" ]