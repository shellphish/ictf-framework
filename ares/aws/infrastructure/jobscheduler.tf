# resource "aws_instance" "jobscheduler" {
#     ami = data.aws_ami.ictf_base.id
#     instance_type = var.jobscheduler_instance_type
#     subnet_id = aws_subnet.master_and_db_range_subnet.id
#     vpc_security_group_ids = [aws_security_group.master_subnet_secgrp.id]
#     key_name = aws_key_pair.jobscheduler-key.key_name

#     tags = {
#         Name = "jobscheduler"
#         Type = "Infrastructure"
#     }

#     root_block_device {
#         volume_size = 100
#     }

#     volume_tags = {
#         Name = "jobscheduler-disk"
#     }

#     connection {
#         user = "hacker"
#         private_key = file("./sshkeys/jobscheduler-key.key")
#         host = self.public_ip
#         agent = false
#     }

#     provisioner "remote-exec" {
#         inline = [
#             "sudo pip install -q ansible",
#             # "/usr/local/bin/ansible-playbook /opt/ictf/gamebot/provisioning/terraform_provisioning.yml --extra-vars ICTF_API_ADDRESS=${aws_instance.database.private_ip} --extra-vars ICTF_API_SECRET=${file("../../secrets/database-api/secret")}",
#             "echo 'hacker' | sudo sed -i '/^#PasswordAuthentication[[:space:]]yes/c\\PasswordAuthentication no' /etc/ssh/sshd_config",
#             "sudo service ssh restart"
#         ]
#     }
# }
