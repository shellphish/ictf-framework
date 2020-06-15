data "aws_eip" "scoreboard_ip" {
  tags = {
    Name = "ictf-scoreboard-ip"
  }
}

resource "aws_eip_association" "scoreboard_ip" {
    instance_id = aws_instance.scoreboard.id
    allocation_id = data.aws_eip.scoreboard_ip.id
}

resource "aws_instance" "scoreboard" {
    ami = data.aws_ami.ictf_base.id
    instance_type = var.scoreboard_instance_type
    subnet_id = aws_subnet.master_and_db_range_subnet.id
    vpc_security_group_ids = [aws_security_group.master_subnet_secgrp.id]
    key_name = aws_key_pair.scoreboard-key.key_name

    tags = {
        Name = "scoreboard"
        Type = "Infrastructure"
    }

    root_block_device {
        volume_size = 100
    }

    volume_tags = {
        Name = "scoreboard-disk"
    }

    depends_on = [aws_ecr_repository.ictf_scoreboard]

    connection {
        user = local.ictf_user
        private_key = file("./sshkeys/scoreboard-key.key")
        host = self.public_ip
        agent = false
    }

    provisioner "file" {
        source = "../../scoreboard/provisioning/ares_provisioning/docker-compose.yml"
        destination = "~/docker-compose.yml"
    }

    provisioner "remote-exec" {
        inline = [
            local.scoreboard_provision_with_ansible,
            local.start_service_container
        ]
    }
}
