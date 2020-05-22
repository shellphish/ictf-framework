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
