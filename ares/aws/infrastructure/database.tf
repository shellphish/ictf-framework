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

    connection {
        user = local.ictf_user
        private_key = file("./sshkeys/database-key.key")
        host = self.public_ip
        agent = false
    }

    # TODO: This ansible role shold be already inside the base ictf AMI
    #       Remove this once you have a base image
    provisioner "file" {
        source = "../../common/ares_provisioning"
        destination = "~/"
    }

    provisioner "file" {
        source = "../../database/provisioning/ares_provisioning/docker-compose.yml"
        destination = "~/docker-compose.yml"
    }

    provisioner "remote-exec" {
        inline = [
            local.database_provision_with_ansible,
        ]
    }
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

