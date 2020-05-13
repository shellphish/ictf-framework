provider "aws" {
  region = var.region
  access_key = var.access_key
  secret_key = var.secret_key
}

resource "aws_vpc" "ictf" {
  cidr_block = var.vpc_cdir_block
  enable_dns_hostnames = true
  enable_dns_support = true
}

resource "aws_internet_gateway" "ictf" {
    vpc_id = aws_vpc.ictf.id
}

resource "aws_route" "internet_access" {
    depends_on = [aws_internet_gateway.ictf]
    route_table_id = aws_vpc.ictf.main_route_table_id
    destination_cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.ictf.id
}
