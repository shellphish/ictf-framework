//  This module defines all the settings needed by the scriptbot

data "aws_ami" "scriptbot" {
  most_recent = true

  filter {
    name   = "name"
    values = ["harden_scriptbot_16.04_*"]
  }

  owners = ["self"]
}

data "local_file" "ecr_password" {
    filename = "./ecr_password"
    depends_on = [aws_ecr_repository.service_scriptbot_image]
}


locals {
  registry_id = length(aws_ecr_repository.service_scriptbot_image) == 0 ? "" : aws_ecr_repository.service_scriptbot_image[0].registry_id
}

resource "aws_instance" "scriptbot" {
    ami           = data.aws_ami.scriptbot.id
    instance_type = var.scriptbot_instance_type
    count         = var.scriptbot_num
    key_name      = aws_key_pair.scriptbot-key.key_name

    subnet_id = aws_subnet.master_and_db_range_subnet.id
    vpc_security_group_ids = [aws_security_group.master_subnet_secgrp.id]

    depends_on = [aws_ecr_repository.service_scriptbot_image]

    connection {
        user = "hacker"
        private_key = file("./sshkeys/scriptbot-key.key")
        host = self.public_ip
        agent = false
    }

    root_block_device {
        volume_size = 100
    }

    volume_tags = {
        Name = "scriptbot${count.index+1}-disk"
    }

    provisioner "remote-exec" {
        inline = [
            "sudo pip install -q ansible",
            "/usr/local/bin/ansible-playbook /opt/ictf/scriptbot/provisioning/terraform_provisioning.yml --extra-vars DOCKER_REGISTRY_USERNAME=AWS --extra-vars DOCKER_REGISTRY_PASSWORD=${data.local_file.ecr_password.content} --extra-vars DOCKER_REGISTRY_ENDPOINT=${local.registry_id}.dkr.ecr.${var.region}.amazonaws.com --extra-vars BOT_ID=${count.index + 1} --extra-vars ALL_BOTS=${var.scriptbot_num} --extra-vars ICTF_API_ADDRESS=${aws_instance.database.private_ip} --extra-vars ICTF_API_SECRET=${file("../../secrets/database-api/secret")} --extra-vars ROUTER_PRIVATE_IP=172.31.172.1 --extra-vars TEAM_COUNT=${var.teams_num}",
            "echo 'hacker' | sudo sed -i '/^#PasswordAuthentication[[:space:]]yes/c\\PasswordAuthentication no' /etc/ssh/sshd_config",
            "sudo service ssh restart"
        ]
    }

    tags = {
        Name = "scriptbot${count.index+1}"
        Type = "Infrastructure"
    }
}
