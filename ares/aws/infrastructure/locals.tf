locals {

  ictf_user = "ubuntu"

  services_scripts = jsondecode(file(var.game_config_file)).services
  
  registry_id = length(aws_ecr_repository.service_scriptbot_image) == 0 ? "" : aws_ecr_repository.service_scriptbot_image[0].registry_id

  # This variables are used to understand if we have prepopulate the registry or all the images needs to be
  # uploaded diring the infrastructure deployment.
  #
  # Prepopulating the registry greatly reduce the deployment time of the whole infrastructure
  database_registry_repository_url = var.database_registry_repository_url != "" ? var.database_registry_repository_url : aws_ecr_repository.ictf_database[0].repository_url
  gamebot_registry_repository_url = var.gamebot_registry_repository_url != "" ? var.gamebot_registry_repository_url : aws_ecr_repository.ictf_gamebot[0].repository_url
  scoreboard_registry_repository_url = var.scoreboard_registry_repository_url != "" ? var.scoreboard_registry_repository_url : aws_ecr_repository.ictf_scoreboard[0].repository_url
  teaminterface_registry_repository_url = var.teaminterface_registry_repository_url != "" ? var.teaminterface_registry_repository_url : aws_ecr_repository.ictf_teaminterface[0].repository_url
  scriptbot_registry_repository_url = var.scriptbot_registry_repository_url != "" ? var.scriptbot_registry_repository_url : aws_ecr_repository.ictf_scriptbot[0].repository_url
  logger_registry_repository_url = var.logger_registry_repository_url != "" ? var.logger_registry_repository_url : aws_ecr_repository.ictf_logger[0].repository_url
  router_registry_repository_url = var.router_registry_repository_url != "" ? var.router_registry_repository_url : aws_ecr_repository.ictf_router[0].repository_url
  dispatcher_registry_repository_url = var.dispatcher_registry_repository_url != "" ? var.dispatcher_registry_repository_url : aws_ecr_repository.ictf_dispatcher[0].repository_url

  database_provision_with_ansible = <<EOF
  ansible-playbook ~/ares_provisioning_first_stage/ansible-provisioning.yml \
    --extra-vars AWS_ACCESS_KEY=${var.access_key} \
    --extra-vars AWS_SECRET_KEY=${var.secret_key} \
    --extra-vars AWS_REGION=${var.region} \
    --extra-vars AWS_REGISTRY_URL=${local.database_registry_repository_url} \
    --extra-vars COMPONENT_NAME=database
  EOF

  gamebot_provision_with_ansible = <<EOF
  ansible-playbook ~/ares_provisioning_first_stage/ansible-provisioning.yml \
    --extra-vars AWS_ACCESS_KEY=${var.access_key} \
    --extra-vars AWS_SECRET_KEY=${var.secret_key} \
    --extra-vars AWS_REGION=${var.region} \
    --extra-vars AWS_REGISTRY_URL=${local.gamebot_registry_repository_url} \
    --extra-vars COMPONENT_NAME=gamebot
  EOF

  scoreboard_provision_with_ansible = <<EOF
  ansible-playbook ~/ares_provisioning_first_stage/ansible-provisioning.yml \
    --extra-vars AWS_ACCESS_KEY=${var.access_key} \
    --extra-vars AWS_SECRET_KEY=${var.secret_key} \
    --extra-vars AWS_REGION=${var.region} \
    --extra-vars AWS_REGISTRY_URL=${local.scoreboard_registry_repository_url} \
    --extra-vars COMPONENT_NAME=scoreboard
  EOF

  teaminterface_provision_with_ansible = <<EOF
  ansible-playbook ~/ares_provisioning_first_stage/ansible-provisioning.yml \
    --extra-vars AWS_ACCESS_KEY=${var.access_key} \
    --extra-vars AWS_SECRET_KEY=${var.secret_key} \
    --extra-vars AWS_REGION=${var.region} \
    --extra-vars AWS_REGISTRY_URL=${local.teaminterface_registry_repository_url} \
    --extra-vars COMPONENT_NAME=teaminterface
  EOF

  scriptbot_common_provision_with_ansible = <<EOF
  ansible-playbook ~/ares_provisioning_first_stage/ansible-provisioning.yml \
    --extra-vars AWS_ACCESS_KEY=${var.access_key} \
    --extra-vars AWS_SECRET_KEY=${var.secret_key} \
    --extra-vars AWS_REGION=${var.region} \
    --extra-vars AWS_REGISTRY_URL=${local.scriptbot_registry_repository_url} \
    --extra-vars COMPONENT_NAME=scriptbot
  EOF

  logger_provision_with_ansible = <<EOF
  ansible-playbook ~/ares_provisioning_first_stage/ansible-provisioning.yml \
    --extra-vars AWS_ACCESS_KEY=${var.access_key} \
    --extra-vars AWS_SECRET_KEY=${var.secret_key} \
    --extra-vars AWS_REGION=${var.region} \
    --extra-vars AWS_REGISTRY_URL=${local.logger_registry_repository_url} \
    --extra-vars COMPONENT_NAME=logger
  EOF

  router_provision_with_ansible = <<EOF
  ansible-playbook ~/ares_provisioning_first_stage/ansible-provisioning.yml \
    --extra-vars AWS_ACCESS_KEY=${var.access_key} \
    --extra-vars AWS_SECRET_KEY=${var.secret_key} \
    --extra-vars AWS_REGION=${var.region} \
    --extra-vars AWS_REGISTRY_URL=${local.router_registry_repository_url} \
    --extra-vars COMPONENT_NAME=router
  EOF

  dispatcher_provision_with_ansible = <<EOF
  ansible-playbook ~/ares_provisioning_first_stage/ansible-provisioning.yml \
    --extra-vars AWS_ACCESS_KEY=${var.access_key} \
    --extra-vars AWS_SECRET_KEY=${var.secret_key} \
    --extra-vars AWS_REGION=${var.region} \
    --extra-vars AWS_REGISTRY_URL=${local.dispatcher_registry_repository_url} \
    --extra-vars COMPONENT_NAME=dispatcher
  EOF

  start_service_container = <<EOF
  docker-compose -f ~/docker-compose.yml up -d
  EOF

}
