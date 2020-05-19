locals {

  ictf_user = "ubuntu"

  services_scripts = jsondecode(file(var.game_config_file)).services
  
  registry_id = length(aws_ecr_repository.service_scriptbot_image) == 0 ? "" : aws_ecr_repository.service_scriptbot_image[0].registry_id

  database_provision_with_ansible = <<EOF
  ansible-playbook ~/ares_provisioning/ansible-provisioning.yml \
    --extra-vars AWS_ACCESS_KEY=${var.access_key} \
    --extra-vars AWS_SECRET_KEY=${var.secret_key} \
    --extra-vars AWS_REGION=${var.region} \
    --extra-vars AWS_REGISTRY_URL=527285246025.dkr.ecr.us-west-1.amazonaws.com/ictf_database \
    --extra-vars COMPONENT_NAME=database
  EOF

  gamebot_provision_with_ansible = <<EOF
  ansible-playbook ~/ares_provisioning/ansible-provisioning.yml \
    --extra-vars AWS_ACCESS_KEY=${var.access_key} \
    --extra-vars AWS_SECRET_KEY=${var.secret_key} \
    --extra-vars AWS_REGION=${var.region} \
    --extra-vars AWS_REGISTRY_URL=527285246025.dkr.ecr.us-west-1.amazonaws.com/ictf_gamebot \
    --extra-vars COMPONENT_NAME=gamebot
  EOF

  scoreboard_provision_with_ansible = <<EOF
  ansible-playbook ~/ares_provisioning/ansible-provisioning.yml \
    --extra-vars AWS_ACCESS_KEY=${var.access_key} \
    --extra-vars AWS_SECRET_KEY=${var.secret_key} \
    --extra-vars AWS_REGION=${var.region} \
    --extra-vars AWS_REGISTRY_URL=527285246025.dkr.ecr.us-west-1.amazonaws.com/ictf_scoreboard \
    --extra-vars COMPONENT_NAME=scoreboard
  EOF

  teaminterface_provision_with_ansible = <<EOF
  ansible-playbook ~/ares_provisioning/ansible-provisioning.yml \
    --extra-vars AWS_ACCESS_KEY=${var.access_key} \
    --extra-vars AWS_SECRET_KEY=${var.secret_key} \
    --extra-vars AWS_REGION=${var.region} \
    --extra-vars AWS_REGISTRY_URL=527285246025.dkr.ecr.us-west-1.amazonaws.com/ictf_teaminterface \
    --extra-vars COMPONENT_NAME=teaminterface
  EOF

  scriptbot_common_provision_with_ansible = <<EOF
  ansible-playbook ~/ares_provisioning/ansible-provisioning.yml \
    --extra-vars AWS_ACCESS_KEY=${var.access_key} \
    --extra-vars AWS_SECRET_KEY=${var.secret_key} \
    --extra-vars AWS_REGION=${var.region} \
    --extra-vars AWS_REGISTRY_URL=527285246025.dkr.ecr.us-west-1.amazonaws.com/ictf_scriptbot \
    --extra-vars COMPONENT_NAME=scriptbot
  EOF

  start_service_container = <<EOF
  docker-compose -f ~/docker-compose.yml up -d
  EOF

}
