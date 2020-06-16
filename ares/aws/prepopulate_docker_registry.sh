#!/bin/bash

AWS_ACCESS_KEY="$1"
AWS_SECRET_KEY="$2"
AWS_REGION="$3"
AWS_REGISTRY_ID="$4"
AWS_REGISTRY_URL="$5"

python ./populate_docker_registry.py "$AWS_ACCESS_KEY" "$AWS_SECRET_KEY" "$AWS_REGION" "$AWS_REGISTRY_ID" "$AWS_REGISTRY_URL/ictf_database" ictf_database
python ./populate_docker_registry.py "$AWS_ACCESS_KEY" "$AWS_SECRET_KEY" "$AWS_REGION" "$AWS_REGISTRY_ID" "$AWS_REGISTRY_URL/ictf_gamebot" ictf_gamebot
python ./populate_docker_registry.py "$AWS_ACCESS_KEY" "$AWS_SECRET_KEY" "$AWS_REGION" "$AWS_REGISTRY_ID" "$AWS_REGISTRY_URL/ictf_scoreboard" ictf_scoreboard
python ./populate_docker_registry.py "$AWS_ACCESS_KEY" "$AWS_SECRET_KEY" "$AWS_REGION" "$AWS_REGISTRY_ID" "$AWS_REGISTRY_URL/ictf_scriptbot" ictf_scriptbot
python ./populate_docker_registry.py "$AWS_ACCESS_KEY" "$AWS_SECRET_KEY" "$AWS_REGION" "$AWS_REGISTRY_ID" "$AWS_REGISTRY_URL/ictf_teaminterface" ictf_teaminterface
python ./populate_docker_registry.py "$AWS_ACCESS_KEY" "$AWS_SECRET_KEY" "$AWS_REGION" "$AWS_REGISTRY_ID" "$AWS_REGISTRY_URL/ictf_logger" ictf_logger
python ./populate_docker_registry.py "$AWS_ACCESS_KEY" "$AWS_SECRET_KEY" "$AWS_REGION" "$AWS_REGISTRY_ID" "$AWS_REGISTRY_URL/ictf_dispatcher" ictf_dispatcher
python ./populate_docker_registry.py "$AWS_ACCESS_KEY" "$AWS_SECRET_KEY" "$AWS_REGION" "$AWS_REGISTRY_ID" "$AWS_REGISTRY_URL/ictf_router" ictf_router
