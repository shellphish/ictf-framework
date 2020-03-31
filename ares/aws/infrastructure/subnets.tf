// This module contains the configuration for all the subnets needed by the game
resource "aws_subnet" "war_range_subnet" {
    vpc_id = aws_vpc.ictf.id
    cidr_block = var.war_zone_subnet_cidr
    map_public_ip_on_launch = true
    availability_zone = "${var.region}a"

    tags = {
        Name = "War_Range_SN"
    }

    depends_on = [aws_route.internet_access]
}

resource "aws_subnet" "master_and_db_range_subnet" {
    vpc_id = aws_vpc.ictf.id
    cidr_block = var.master_and_db_zone_subnet_cidr
    map_public_ip_on_launch = true
    availability_zone = "${var.region}a"

    tags = {
        Name = "Master_SN"
    }

    depends_on = [aws_route.internet_access]
}
