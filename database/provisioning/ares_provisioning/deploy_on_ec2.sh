#!/bin/bash

AWS_REGION="$1"
AWS_REGISTRY_URL="$2"

aws ecr get-login-password --region "$1" | docker login --username AWS --password-stdin "$AWS_REGISTRY_URL"
docker pull "$AWS_REGISTRY_URL"
docker tag "$AWS_REGISTRY_URL" ictf_database