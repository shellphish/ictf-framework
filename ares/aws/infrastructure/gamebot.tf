resource "aws_instance" "gamebot" {
    ami = data.aws_ami.ictf_base.id
    instance_type = var.gamebot_instance_type
    subnet_id = aws_subnet.master_and_db_range_subnet.id
    vpc_security_group_ids = [aws_security_group.master_subnet_secgrp.id]
    key_name = aws_key_pair.gamebot-key.key_name

    tags = {
        Name = "gamebot"
        Type = "Infrastructure"
    }

    root_block_device {
        volume_size = 100
    }

    volume_tags = {
        Name = "gamebot-disk"
    }

    connection {
        user = local.ictf_user
        private_key = file("./sshkeys/gamebot-key.key")
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
        source = "../../gamebot/provisioning/ares_provisioning/docker-compose.yml"
        destination = "~/docker-compose.yml"
    }

    provisioner "remote-exec" {
        inline = [
            local.gamebot_provision_with_ansible,
            local.start_service_container
        ]
    }
}
