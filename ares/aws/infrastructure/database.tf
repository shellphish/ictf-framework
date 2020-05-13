#  This module defines all the settings needed by the database



data "aws_s3_bucket" "database_bucket" {
  bucket = "ictf-database-bucket-${var.region}"
}

resource "aws_instance" "database" {
    ami = data.aws_ami.ictf_base.id
    instance_type = var.database_instance_type
    subnet_id = aws_subnet.master_and_db_range_subnet.id
    vpc_security_group_ids = [aws_security_group.master_subnet_secgrp.id]
    key_name = aws_key_pair.database-key.key_name

    root_block_device {
        volume_size = 100
    }

    volume_tags = {
        Name = "database-disk"
    }

    tags = {
        Name = "database"
        Type = "Infrastructure"
    }

    # connection {
    #     user = "ubuntu"
    #     private_key = file("./sshkeys/database-key.key")
    #     host = self.public_ip
    #     agent = false
    # }

    # provisioner "file" {
    #     source = "../../database/provisioning/ares_provisioning"
    #     destination = "~/"
    # }

    # provisioner "remote-exec" {
    #     inline = [
    #         "ansible-playbook ~/ares_provisioning/ansible-provisioning.yml --extra-vars AWS_ACCESS_KEY=${var.access_key} --extra-vars AWS_SECRET_KEY=${var.secret_key} --extra-vars AWS_REGION=${var.region} --extra-vars AWS_REGISTRY_URL=527285246025.dkr.ecr.us-west-1.amazonaws.com/ictf_database",
    #     ]
    # }
}

# resource "null_resource" "upload_team_info" {
#     triggers = {
#         teamvm_ids = "aws_instance.database.id"
#     }

#     connection {
#         user = "hacker"
#         private_key = file("./sshkeys/database-key.key")
#         host = aws_instance.database.public_ip
#     }

#     provisioner "local-exec" {
#         command = "python ../../database/provisioning/create_teams.py ${aws_instance.database.public_ip} ${var.game_config_file}"
#     }

#     provisioner "local-exec" {
#         command = "python ../../database/provisioning/create_services.py ${aws_instance.database.public_ip} ${var.game_config_file}"
#     }
# }

