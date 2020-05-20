resource "aws_ecr_repository" "service_scriptbot_image" {
  count = length(local.services_scripts)
  name = "${local.services_scripts[count.index].name}_scripts"
  image_tag_mutability = "MUTABLE"

  provisioner "local-exec" {
    command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ${local.services_scripts[count.index].name}_scripts"
  }
}

# resource "aws_ecr_repository" "ictf_database" {
#   name = "ictf_database"
#   image_tag_mutability = "MUTABLE"
  
#   provisioner "local-exec" {
#     command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ictf_database" 
#   }
# }

# resource "aws_ecr_repository" "ictf_gamebot" {
#   name = "ictf_gamebot"
#   image_tag_mutability = "MUTABLE"
  
#   provisioner "local-exec" {
#     command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ictf_gamebot" 
#   }
# }

# resource "aws_ecr_repository" "ictf_scoreboard" {
#   name = "ictf_scoreboard"
#   image_tag_mutability = "MUTABLE"
  
#   provisioner "local-exec" {
#     command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ictf_scoreboard" 
#   }
# }

# resource "aws_ecr_repository" "ictf_scriptbot" {
#   name = "ictf_scriptbot"
#   image_tag_mutability = "MUTABLE"
  
#   provisioner "local-exec" {
#     command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ictf_scriptbot" 
#   }
# }

# resource "aws_ecr_repository" "ictf_teaminterface" {
#   name = "ictf_teaminterface"
#   image_tag_mutability = "MUTABLE"
  
#   provisioner "local-exec" {
#     command ="python ./populate_docker_registry.py ${var.access_key} ${var.secret_key} ${var.region} ${self.registry_id} ${self.repository_url} ictf_teaminterface" 
#   }
# }