//  This module defines all the settings needed by the team interface

data "aws_ami" "teaminterface" {
  most_recent = true

  filter {
    name   = "name"
    values = ["harden_teaminterface_16.04_*"]
  }

  owners = ["self"]
}

data "aws_eip" "teaminterface_ip" {
  tags = {
    Name = "ictf-teaminterface-ip"
  }
}

resource "aws_eip_association" "teaminterface_ip" {
    instance_id = aws_instance.teaminterface.id
    allocation_id = data.aws_eip.teaminterface_ip.id
}

resource "aws_instance" "teaminterface" {
    ami = data.aws_ami.teaminterface.id
    instance_type = var.teaminterface_instance_type
    subnet_id = aws_subnet.master_and_db_range_subnet.id
    vpc_security_group_ids = [aws_security_group.master_subnet_secgrp.id]
    key_name = aws_key_pair.teaminterface-key.key_name

    tags = {
        Name = "teaminterface"
        Type = "Infrastructure"
    }

    root_block_device {
        volume_size = 100
    }

    volume_tags = {
        Name = "teaminterface-disk"
    }

    connection {
        user = "hacker"
        private_key = file("./sshkeys/teaminterface-key.key")
        host = self.public_ip
        agent = false
    }

    provisioner "remote-exec" {
        inline = [
            "sudo pip install -q ansible",
            "/usr/local/bin/ansible-playbook /opt/ictf/teaminterface/provisioning/terraform_provisioning.yml --extra-vars ICTF_DB_API_ADDRESS=${aws_instance.database.private_ip} --extra-vars ICTF_DB_API_SECRET=${file("../../secrets/database-api/secret")}",
            "echo 'hacker' | sudo sed -i '/^#PasswordAuthentication[[:space:]]yes/c\\PasswordAuthentication no' /etc/ssh/sshd_config",
            "sudo service ssh restart"
        ]
    }
}
