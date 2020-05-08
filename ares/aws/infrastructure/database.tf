#  This module defines all the settings needed by the database

# data "aws_ami" "database" {
#   most_recent = true

#   filter {
#     name   = "name"
#     values = ["harden_database_16.04_*"]
#   }

#   owners = ["self"]
# }

# data "aws_s3_bucket" "database_bucket" {
#   bucket = "ictf-database-bucket-${var.region}"
# }

data "aws_ami" "database" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-*"]
  }

  owners = ["099720109477"]
}


resource "aws_instance" "database" {
    ami = data.aws_ami.database.id
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
    #     user = "hacker"
    #     private_key = file("./sshkeys/database-key.key")
    #     host = self.public_ip
    #     agent = false
    # }

    # provisioner "remote-exec" {
    #     inline = [
    #         "sudo pip install -q ansible",
    #         "/usr/local/bin/ansible-playbook /opt/ictf/database/provisioning/terraform_provisioning.yml --extra-vars AWS_BUCKET_NAME=${data.aws_s3_bucket.database_bucket.id} --extra-vars AWS_REGION=${var.region} --extra-vars AWS_ACCESS_KEY=${var.access_key} --extra-vars AWS_SECRET_KEY=${var.secret_key} --extra-vars ICTF_API_SECRET=${file("../../secrets/database-api/secret")} --extra-vars ICTF_USER_PASSWORD_SALT=${file("../../secrets/database-api/salt")} --extra-vars ICTF_MYSQL_DATABASE_PASSWORD=${file("../../secrets/database-api/mysql")}",
    #         "echo 'hacker' | sudo sed -i '/^#PasswordAuthentication[[:space:]]yes/c\\PasswordAuthentication no' /etc/ssh/sshd_config",
    #         "sudo service ssh restart"
    #     ]
    # }

    # provisioner "remote-exec" {
    #     when = destroy
    #     inline = [
    #         "sudo pkill -9 mysql || echo '##### SPEEEEEEEEEEED gone: FAILED TO KILL mysql.'"
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

