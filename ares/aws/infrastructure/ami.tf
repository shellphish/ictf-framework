data "aws_ami" "ictf_base" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ictf_base_4"]
  }

  owners = ["self"]
}