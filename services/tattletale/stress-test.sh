#!/bin/bash

INFO_FP=$1
NUM=$2

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TESTER_FP=$DIR/tester.py

for f in `seq $NUM`; do ($TESTER_FP $INFO_FP &) ; done | grep SUCCESS | wc -l
