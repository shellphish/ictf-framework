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

#     connection {
#         user = "ubuntu"
#         private_key = file("./sshkeys/gamebot-key.key")
#         host = self.public_ip
#         agent = false
#     }

#     provisioner "file" {
#         source = "../../gamebot/provisioning/ares_provisioning"
#         destination = "~/"
#     }

#     provisioner "remote-exec" {
#         inline = [
#             "ansible-playbook ~/ares_provisioning/ansible-provisioning.yml --extra-vars AWS_ACCESS_KEY=${var.access_key} --extra-vars AWS_SECRET_KEY=${var.secret_key} --extra-vars AWS_REGION=${var.region} --extra-vars AWS_REGISTRY_URL=527285246025.dkr.ecr.us-west-1.amazonaws.com/ictf_database",
#         ]
#     }
}
