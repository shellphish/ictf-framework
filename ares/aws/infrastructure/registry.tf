locals {
  services_scripts = jsondecode(file(var.game_config_file)).services
}

resource "aws_ecr_repository" "service_scriptbot_image" {
  count = length(local.services_scripts)
  name = "${local.services_scripts[count.index].name}_scripts"
  image_tag_mutability = "MUTABLE"

  provisioner "local-exec" {
    command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ${local.services_scripts[count.index].name}_scripts"
  }
}
