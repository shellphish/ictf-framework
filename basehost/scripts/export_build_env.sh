#!/usr/bin/env bash

SCRIPT_DIR=$(cd "$( dirname "${BASH_SOURCE[0]:-${(%):-%x}}" )" && pwd )
. "${SCRIPT_DIR}/aws_vars_$1.env"
. "${SCRIPT_DIR}/ictf_vars.env"
# . "${SCRIPT_DIR}/export_env_git.sh"
