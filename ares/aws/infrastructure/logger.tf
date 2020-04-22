data "aws_ami" "logger" {
  most_recent = true

  filter {
    name   = "name"
    # TODO: CHANGE ME ONCE WE HAVE THE IMAGE FROM PACKER
    values = ["harden_gamebot_16.04_*"]
  }

  owners = ["self"]
}

resource "aws_instance" "logger" {
    ami = data.aws_ami.logger.id
    instance_type = var.logger_instance_type
    subnet_id = aws_subnet.master_and_db_range_subnet.id
    vpc_security_group_ids = [aws_security_group.master_subnet_secgrp.id]
    key_name = aws_key_pair.logger-key.key_name

    tags = {
        Name = "logger"
        Type = "Infrastructure"
    }

    root_block_device {
        volume_size = 100
    }

    volume_tags = {
        Name = "logger-disk"
    }

    connection {
        user = "hacker"
        private_key = file("./sshkeys/logger-key.key")
        host = self.public_ip
        agent = false
    }

    provisioner "remote-exec" {
        inline = [
            "mkdir -p /opt/ictf/logger/provisioning"
        ]
    }
    

    provisioner "file" {
        source = "../../logger/provisioning/prometheus.yml.j2"
        destination = "/opt/ictf/logger/provisioning/prometheus.yml.j2"
    }

    provisioner "file" {
        source = "../../logger/provisioning/terraform_provisioning.yml"
        destination = "/opt/ictf/logger/provisioning/terraform_provisioning.yml"
    }

    provisioner "remote-exec" {
        inline = [
            "sudo pip install -q ansible",
            #"/usr/local/bin/ansible-playbook /opt/ictf/logger/provisioning/terraform_provisioning.yml --extra-vars SOURCES='{}'", 
            "echo 'hacker' | sudo sed -i '/^#PasswordAuthentication[[:space:]]yes/c\\PasswordAuthentication no' /etc/ssh/sshd_config",
            "sudo service ssh restart"
        ]
    }
}
