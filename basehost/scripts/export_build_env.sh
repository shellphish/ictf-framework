#!/usr/bin/env bash

SCRIPT_DIR=$(cd "$( dirname "${BASH_SOURCE[0]:-${(%):-%x}}" )" && pwd )
. "${SCRIPT_DIR}/export_env_aws_$1.sh"
. "${SCRIPT_DIR}/export_env_ictf.sh"
# . "${SCRIPT_DIR}/export_env_git.sh"
