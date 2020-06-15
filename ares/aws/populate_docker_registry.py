#!/usr/bin/env python

import argparse
import time
import base64
import json
import textwrap
import docker
import boto3

class ECRLoginTokenNotFoundException(Exception):
    """
    Exception triggered if a login token can not be found for the specified registry Id
    """

class DockerPushException(Exception):
    pass

ECR_PASSWORD_FILE = "./ecr_password"

# TODO: Remove this step when the terraform mamtainers till decide to comment my issue
#       There is no way to get ECR login credential directly in terraform at the moment
def get_ecr_credentials(aws_access_key, aws_secret_key, aws_region, registry_id):
    ecr_client = boto3.client('ecr', 
        aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key, region_name=aws_region) 
    ecr_cred = ecr_client.get_authorization_token(registryIds=[registry_id])
    if "authorizationData" not in ecr_cred:
        raise ECRLoginTokenNotFoundException
    return ecr_cred["authorizationData"][0]

def dump_ecr_password(dest, password):
    with open(dest, 'w') as f:
        f.write(password)

def populate_registry(aws_access_key, aws_secret_key, aws_region, 
                      registry_id, repository_url, image_name):

    print("[+] Getting ECR credentials for registry {}.".format(registry_id))
    ecr_cred = get_ecr_credentials(aws_access_key, aws_secret_key, aws_region, registry_id)
    registry_username, registry_password = base64.b64decode(ecr_cred['authorizationToken']).decode("utf-8").split(":")
    registry_endpoint = ecr_cred['proxyEndpoint']

    # TODO: FIX THIS, FUCK THIS STUPID SHIT, WE CAN'T HAVE NICE THINGS WITH HTTPS OR HTTP IN THE BEGINNING
    registry_endpoint = ecr_cred['proxyEndpoint'].replace('https://', '').replace('http://', '')

    print("[+] Logging into the registry {}.".format(registry_id))
    # docker_client = docker.from_env()
    docker_client = docker.from_env(timeout=1200)
    docker_client.login(
        username=registry_username,
        password=registry_password,
        registry=registry_endpoint,
        reauth=True,
    )

    dump_ecr_password(ECR_PASSWORD_FILE, registry_password)

    print("[+] Tagging local image {} with tag {}".format(image_name, repository_url))
    docker_image = docker_client.images.get(image_name)
    docker_image.tag(repository_url)
    print("[+] Pushing image {} to registry {}".format(repository_url, registry_id))
    docker_client.images.push(repository_url)
    # docker_client.images.push(repository_url, stream=True, decode=True)
    # for status in docker_client.images.push(repository_url, stream=True, decode=True):
    #     # print("[+]      Result: {}".format(status))
    #     if 'error' in status and status['error'] == "toomanyrequests: Rate exceeded":
    #         time.sleep(1)
    #         continue
    #     elif 'error' in status:
    #         raise DockerPushException("Could not push image to remote: {}".format(json.dumps(status, indent=2)))

    # else:
    #     print("[+]      Result: {}".format(status))
    # Housekeeping
    print("[+] Removing local image {}".format(repository_url))
    docker_client.images.remove(repository_url)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "aws_access_key",
        help=textwrap.dedent('''
        Aws access key 
        '''),
    )

    parser.add_argument(
        "aws_secret_key",
        help=textwrap.dedent('''
        Aws secret key 
        '''),
    )

    parser.add_argument(
        "aws_region", 
        help=textwrap.dedent('''
        Aws region where the registry has been spawned
        '''),
    )

    parser.add_argument(
        "registry_id", 
        help=textwrap.dedent('''
        The registry ID where the repository was created
        '''),
    )

    parser.add_argument(
        "repository_url", 
        help=textwrap.dedent('''
        The repository url where the image need to be pushed 
        '''),
    )

    parser.add_argument(
        "image_name", 
        help=textwrap.dedent('''
        Local name of the image that needs to be pushed on the repository
        '''),
    )

    args = parser.parse_args()

    populate_registry(
        args.aws_access_key, args.aws_secret_key, args.aws_region, args.registry_id,
        args.repository_url, args.image_name)
