data "aws_ami" "teamvm" {
  most_recent = true

  filter {
    name   = "name"
    values = ["primed_teamvm_18.04_*"]
  }

  owners = ["self"]
}

locals {
  teams_list = jsondecode(file(var.game_config_file)).teams
  teams_organizer_hosted_map = { for team in local.teams_list: team.id => team if team.organizer_hosted }
}


resource "aws_instance" "teamvm" {
    for_each = local.teams_organizer_hosted_map 
    ami = data.aws_ami.teamvm.id
    instance_type = var.teamvm_instance_type
    subnet_id = aws_subnet.war_range_subnet.id
    vpc_security_group_ids = [aws_security_group.teams_secgrp.id]
    # count = "${var.teams_num}"
    private_ip = "172.31.${129 + floor((each.value.id - 1) / 254)}.${(each.value.id) % 254}"
    key_name = aws_key_pair.teamvmmaster-key.key_name

    tags = {
        Name = "teamvm${each.value.id}"
        TeamIdx = each.value.id
        Type = "Teams"
    }

    root_block_device {
        volume_size = 100
    }

    volume_tags = {
        Name = "teamvm${each.value.id}-disk"
    }

    connection {
        user = "hacker"
        private_key = file("./sshkeys/teamvmmaster-key.key")
        host = self.public_ip
        agent = false
    }

    provisioner "local-exec" {
        command ="cat ./sshkeys/team${each.value.id}-key.pub >> ./sshkeys/authorized_keys_team${each.value.id}"
    }

    provisioner "file" {
        source = "./sshkeys/authorized_keys_team${each.value.id}"
        destination = "/home/hacker/authorized_keys"
    }

    provisioner "file" {
        source = "./vpnkeys/team${each.value.id}.ovpn"
        destination = "/opt/ictf/openvpn.conf.j2"
    }

    provisioner "local-exec" {
        command = "rm ./sshkeys/authorized_keys_team${each.value.id}"
    }

    provisioner "file" {
        source = "../../teamvms/provisioning/terraform_provisioning.yml"
        destination = "/home/hacker/terraform_provisioning.yml"
    }

    provisioner "file" {
        source = "../../teamvms/provisioning/start_services.yml"
        destination = "/opt/ictf/services/start_services.yml"
    }

    provisioner "remote-exec" {
        inline = [
            "ansible-playbook /home/hacker/terraform_provisioning.yml --extra-vars ROUTER_PRIVATE_IP=172.31.172.1 --extra-vars TEAM_ID=${each.value.id}" ,
            "cd /opt/ictf/services && ansible-playbook start_services.yml --extra-vars TEAM_ID=team${each.value.id}",
            "rm /opt/ictf/services/start_services.yml",
            "echo 'hacker' | sudo sed -i '/^#PasswordAuthentication[[:space:]]yes/c\\PasswordAuthentication no' /etc/ssh/sshd_config",
            "sudo service ssh restart"
        ]
    }
}


