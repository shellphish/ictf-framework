resource "aws_ecr_repository" "service_scriptbot_image" {
  count = length(local.services_scripts)
  name = "${local.services_scripts[count.index].name}_scripts"
  image_tag_mutability = "MUTABLE"

  provisioner "local-exec" {
    command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ${local.services_scripts[count.index].name}_scripts"
  }
}

resource "aws_ecr_repository" "ictf_database" {
  name = "ictf_database"
  image_tag_mutability = "MUTABLE"
  # We create the repository only if we didn't pre populate the registry before 
  count = var.database_registry_repository_url != "" ? 0 : 1
  
  provisioner "local-exec" {
    command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ictf_database" 
  }
  
}

resource "aws_ecr_repository" "ictf_gamebot" {
  name = "ictf_gamebot"
  image_tag_mutability = "MUTABLE"
  # We create the repository only if we didn't pre populate the registry before 
  count = var.gamebot_registry_repository_url != "" ? 0 : 1
  
  provisioner "local-exec" {
    command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ictf_gamebot" 
  }
}

resource "aws_ecr_repository" "ictf_scoreboard" {
  name = "ictf_scoreboard"
  image_tag_mutability = "MUTABLE"
  # We create the repository only if we didn't pre populate the registry before 
  count = var.scoreboard_registry_repository_url != "" ? 0 : 1
  
  provisioner "local-exec" {
    command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ictf_scoreboard" 
  }
}

resource "aws_ecr_repository" "ictf_scriptbot" {
  name = "ictf_scriptbot"
  image_tag_mutability = "MUTABLE"
  # We create the repository only if we didn't pre populate the registry before 
  count = var.scriptbot_registry_repository_url != "" ? 0 : 1
  
  provisioner "local-exec" {
    command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ictf_scriptbot" 
  }
}

resource "aws_ecr_repository" "ictf_teaminterface" {
  name = "ictf_teaminterface"
  image_tag_mutability = "MUTABLE"
  # We create the repository only if we didn't pre populate the registry before 
  count = var.teaminterface_registry_repository_url != "" ? 0 : 1
  
  provisioner "local-exec" {
    command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ictf_teaminterface" 
  }
}

resource "aws_ecr_repository" "ictf_logger" {
  name = "ictf_logger"
  image_tag_mutability = "MUTABLE"
  # We create the repository only if we didn't pre populate the registry before 
  count = var.logger_registry_repository_url != "" ? 0 : 1
  
  provisioner "local-exec" {
    command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ictf_logger" 
  }
}

resource "aws_ecr_repository" "ictf_dispatcher" {
  name = "ictf_dispatcher"
  image_tag_mutability = "MUTABLE"
  # We create the repository only if we didn't pre populate the registry before 
  count = var.dispatcher_registry_repository_url != "" ? 0 : 1
  
  provisioner "local-exec" {
    command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ictf_dispatcher" 
  }
}

resource "aws_ecr_repository" "ictf_router" {
  name = "ictf_router"
  image_tag_mutability = "MUTABLE"
  # We create the repository only if we didn't pre populate the registry before 
  count = var.router_registry_repository_url != "" ? 0 : 1
  
  provisioner "local-exec" {
    command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ictf_router" 
  }
}
