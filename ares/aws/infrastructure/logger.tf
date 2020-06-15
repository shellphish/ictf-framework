resource "aws_instance" "logger" {
    ami = data.aws_ami.ictf_base.id
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

    depends_on = [aws_ecr_repository.ictf_logger]

    connection {
        user = local.ictf_user
        private_key = file("./sshkeys/logger-key.key")
        host = self.public_ip
        agent = false
    }
    
    provisioner "file" {
        source = "../../logger/provisioning/ares_provisioning/docker-compose.yml"
        destination = "~/docker-compose.yml"
    }

    provisioner "remote-exec" {
        inline = [
            local.logger_provision_with_ansible,
            "sudo sysctl vm.max_map_count=262144",
            local.start_service_container
        ]
    }
}
