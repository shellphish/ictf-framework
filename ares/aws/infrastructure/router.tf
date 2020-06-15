//  This module defines all the settings needed by the database
# data "aws_ami" "router" {
#   most_recent = true

#   filter {
#     name   = "name"
#     values = ["harden_router_16.04_*"]
#   }

#   owners = ["self"]
# }

data "aws_eip" "router_ip" {
  tags = {
    Name = "ictf-router-ip"
  }
}

data "aws_s3_bucket" "router_bucket" {
  bucket = "ictf-router-bucket-${var.region}"
}

resource "aws_eip_association" "router_ip" {
    instance_id = aws_instance.router.id
    allocation_id = data.aws_eip.router_ip.id
}

resource "aws_route" "vpn" {
    route_table_id = aws_vpc.ictf.main_route_table_id
    destination_cidr_block = "10.9.0.0/16"
    instance_id = aws_instance.router.id
}

resource "aws_instance" "router" {
    ami = data.aws_ami.ictf_base.id
    instance_type = var.router_instance_type
    subnet_id = aws_subnet.war_range_subnet.id
    vpc_security_group_ids = [aws_security_group.router_secgrp.id]
    private_ip = "172.31.172.1"

    tags = {
        Name = "router"
        Type = "Infrastructure"
    }

    key_name = aws_key_pair.router-key.key_name
    source_dest_check = false

    root_block_device {
        volume_size = 15000
    }

    volume_tags = {
        Name = "router-disk"
    }

    depends_on = [aws_ecr_repository.ictf_router]

    connection {
        user = local.ictf_user
        private_key = file("./sshkeys/router-key.key")
        host = self.public_ip
        agent = false
    }

    provisioner "file" {
        source = "./vpnkeys/openvpn.zip"
        destination = "~/openvpn.zip"
    }

    provisioner "file" {
        source = "../../router/provisioning/ares_provisioning/docker-compose.yml"
        destination = "~/docker-compose.yml"
    }

    provisioner "remote-exec" {
        inline = [
            local.router_provision_with_ansible,
            local.start_service_container
        ]
    }

}