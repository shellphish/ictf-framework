resource "aws_security_group" "master_subnet_secgrp" {
    name = "master_subnet_secgrp"
    description = "This is the master subnet secgrp"
    vpc_id = aws_vpc.ictf.id

    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
    ingress {
        from_port = 80
        to_port = 443
        protocol = "tcp"
        cidr_blocks =  ["172.31.172.0/24"]
    }
    ingress {
        from_port = 61209
        to_port = 61209
        protocol = "tcp"
        cidr_blocks = [var.master_and_db_zone_subnet_cidr]
    }
    ingress {
        from_port = 80
        to_port = 80
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    # Kibana
    ingress {
        from_port = 5601
        to_port = 5601
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    # Grafana
    ingress {
        from_port = 3000
        to_port = 3000
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    # Elasticsearch
    ingress {
        from_port = 9200
        to_port = 9200
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    # Prometheus Metrics
    ingress { 
        from_port   = 9000
        to_port     = 9999
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        from_port   = 5672
        to_port     = 5672
        protocol    = "tcp"
        cidr_blocks = [var.master_and_db_zone_subnet_cidr]
    }

    ingress {
        from_port   = 15672
        to_port     = 15672
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    tags = {
        Name = "master_secgrp"
    }
}

resource "aws_security_group" "router_secgrp" {
    name = "router_secgrp"
    description = "This is the routers secgrp"
    vpc_id = aws_vpc.ictf.id

    ingress {
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        from_port   = 1000
        to_port     = 2000
        protocol    = "udp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = [var.master_and_db_zone_subnet_cidr]
    }

    ingress { # Prometheus Metrics
        from_port   = 9000
        to_port     = 9999
        protocol    = "tcp"
        cidr_blocks = ["192.35.222.0/24"]
    }

    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    tags = {
        Name = "router_secgrp"
    }
}

resource "aws_security_group" "teams_secgrp" {
    name = "teams_secgrp"
    description = "This is the teams secgrp"
    vpc_id = aws_vpc.ictf.id

    ingress {
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress { # Prometheus Metrics
        from_port   = 9000
        to_port     = 9999
        protocol    = "tcp"
        cidr_blocks = ["192.35.222.0/24"]
    }

    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    tags = {
        Name = "teams_secgrp"
    }
}
