resource "aws_route53_zone" "private" {
  name = "ictf"

  vpc {
    vpc_id = aws_vpc.ictf.id
  }
}

resource "aws_route53_record" "database" {
  zone_id = aws_route53_zone.private.zone_id
  name    = "database.ictf"
  type    = "A"
  ttl     = "43200" // 12h
  records = [aws_instance.database.private_ip]
}

resource "aws_route53_record" "logger" {
  zone_id = aws_route53_zone.private.zone_id
  name    = "logger.ictf"
  type    = "A"
  ttl     = "43200" // 12h
  records = [aws_instance.logger.private_ip]
}

resource "aws_route53_record" "gamebot" {
  zone_id = aws_route53_zone.private.zone_id
  name    = "gamebot.ictf"
  type    = "A"
  ttl     = "43200" // 12h
  records = [aws_instance.gamebot.private_ip]
}

resource "aws_route53_record" "scoreboard" {
  zone_id = aws_route53_zone.private.zone_id
  name    = "scoreboard.ictf"
  type    = "A"
  ttl     = "43200" // 12h
  records = [aws_instance.scoreboard.private_ip]
}

resource "aws_route53_record" "teaminterface" {
  zone_id = aws_route53_zone.private.zone_id
  name    = "teaminterface.ictf"
  type    = "A"
  ttl     = "43200" // 12h
  records = [aws_instance.teaminterface.private_ip]
}

resource "aws_route53_record" "scriptbot" {
  zone_id = aws_route53_zone.private.zone_id
  count   = var.scriptbot_num
  name    = "scriptbot${count.index+1}.ictf"
  type    = "A"
  ttl     = "43200" // 12h
  records = [aws_instance.scriptbot[count.index].private_ip]
}

resource "aws_route53_record" "router" {
  zone_id = aws_route53_zone.private.zone_id
  name    = "router.ictf"
  type    = "A"
  ttl     = "43200" // 12h
  records = [aws_instance.router.public_ip]
}

resource "aws_route53_record" "dispatcher" {
  zone_id = aws_route53_zone.private.zone_id
  name    = "dispatcher.ictf"
  type    = "A"
  ttl     = "43200" // 12h
  records = [aws_instance.dispatcher.private_ip]
}