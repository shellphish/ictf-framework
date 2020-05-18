data "local_file" "ecr_password" {
    filename = "./ecr_password"
    depends_on = [aws_ecr_repository.service_scriptbot_image]
}

resource "aws_instance" "scriptbot" {
    ami           = data.aws_ami.ictf_base.id
    instance_type = var.scriptbot_instance_type
    count         = var.scriptbot_num
    key_name      = aws_key_pair.scriptbot-key.key_name

    subnet_id = aws_subnet.master_and_db_range_subnet.id
    vpc_security_group_ids = [aws_security_group.master_subnet_secgrp.id]

    depends_on = [aws_ecr_repository.service_scriptbot_image]

    connection {
        user = local.ictf_user
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

    tags = {
        Name = "scriptbot${count.index+1}"
        Type = "Infrastructure"
    }

    # TODO: This ansible role shold be already inside the base ictf AMI
    #       Remove this once you have a base image
    provisioner "file" {
        source = "../../common/ares_provisioning"
        destination = "~/"
    }

    provisioner "file" {
        source = "../../scriptbot/ares_provisioning/"
        destination = "~/ares_provisioning_second_stage"
    }

    provisioner "remote-exec" {
        inline = [
            local.scriptbot_common_provision_with_ansible,
            "ansible-playbook ~/ares_provisioning_second_stage/ansible-provisioning.yml --extra-vars BOT_ID=${count.index + 1} --extra-vars ALL_BOTS=${var.scriptbot_num} --extra-vars API_SECRET=${file("../../secrets/database-api/secret")}"
        ]
    }
}
