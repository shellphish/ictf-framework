#!/bin/bash

set -euo pipefail
# set -x

AWS_ACCESS_KEY="$1"
AWS_SECRET_KEY="$2"
AWS_REGION="$3"
GAME_CONFIG_PATH="$4"

IS_DEVELOP_MODE=${5:-""}

REGISTRY_URL="none"

case $IS_DEVELOP_MODE in
  -d | --dev-mode) IS_DEVELOP_MODE="-d" ;;
  * ) IS_DEVELOP_MODE="" ;;
esac

VAR_FILE_PATH="ictf_game_vars.auto.tfvars.json"
printf '\n[*] -----------------STEP -2: Sanity check game_config.json ----------------\n'
python configlint.py "$GAME_CONFIG_PATH"

printf '\n[*] -----------------STEP -1: Building services scripts images ----------------\n'
SERVICES_PATH=`cat $GAME_CONFIG_PATH | jq -r .service_metadata.host_dir`
ACTIVE_SERVICES=`cat $GAME_CONFIG_PATH | jq -r '.services | to_entries[] | select(.value.state == "enabled") | .value.name'`

for a in $ACTIVE_SERVICES; do
    f=$SERVICES_PATH/$a/info.yaml
    echo $f
    CHALLNAME=$(basename $(dirname "$f"))
    cd "$SERVICES_PATH/$CHALLNAME"
    echo "Building scripts for ${CHALLNAME}"
    SERVICE_NAME="${CHALLNAME}" make scriptbot_scripts
    cd -
done

printf '\n[*] ---------------- STEP 0: Generate SSH & OpenVPN credentials ----------------\n'
./0_make_credentials.py "$GAME_CONFIG_PATH"

printf "\n"
read -p "Did you prepopulate the docker registry? (yes) " choice
case "$choice" in
  yes ) 
    read -p "Insert registry URL " REGISTRY_URL
    ;;
  * ) 
    printf "The images will be uploaded during the infrastructure deployment"
    ;;
esac

printf '\n[*] ---------------- STEP 1: Create terraform variables file ----------------\n'
./1_make_auto_tfvars.py "$AWS_ACCESS_KEY" "$AWS_SECRET_KEY" "$AWS_REGION" "$GAME_CONFIG_PATH" "$REGISTRY_URL" $IS_DEVELOP_MODE 

printf '\n[*] ---------------- STEP 2: terraform init ----------------'
terraform init ./infrastructure

printf '\n[*] ---------------- STEP 3: terraform apply - spawn infrastructure ----------------\n'
echo "$VAR_FILE_PATH"
cat "$VAR_FILE_PATH"
echo
printf "\n"
if [ "$IS_DEVELOP_MODE" = "-d" ]
then
  echo "Mode: DEVELOPMENT";
else
  echo "Mode: PRODUCTION";
fi
printf "\n"
read -p "Are you sure you want to spin up a game with these infrastructure settings? (yes) " choice
case "$choice" in
  yes ) ;;
  no ) exit 1;;
  * ) echo "invalid choice : $choice"; exit 1;;
esac

terraform apply --parallelism=50 -var-file "$VAR_FILE_PATH" ./infrastructure

printf '\n[*] ---------------- STEP 4: Generate SSH config ----------------\n'
./4_generate_ssh_config.py

printf '\n[*] ---------------- STEP 5: Register teamvms into the database ----------------\n'
./5_register_teamvms.py
