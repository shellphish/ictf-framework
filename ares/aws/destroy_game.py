#!/usr/bin/env python

import subprocess
import argparse
import os
import json

class TfDestroyException(Exception):
    """
    Exception raised by terrafor mif the init command fails
    """

class TfApplyException(Exception):
    """
    Exception raised by terraform if the init command fails
    """

def destroy_game(terraform_path):

    tf_destroy_process = subprocess.call(
        "{} destroy -parallelism=50 -var-file=ictf_game_vars.auto.tfvars.json ./infrastructure".format(terraform_path), shell=True)

    if tf_destroy_process != 0:
        raise TfApplyException

    try:
        os.remove("./ssh_config")
    except OSError as ex:
        print("Could not remove ssh_config: {}".format(repr(ex)))
    os.remove("./terraform.tfstate")
    os.remove("./terraform.tfstate.backup")

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-t', '--terraform_path', type=str, default="terraform",
                        help='Path to the terraform tool (default: terraform in your $PATH)')
    args = argparser.parse_args()

    destroy_game(args.terraform_path)
