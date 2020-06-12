output "start_game_url" {
    value = "http://${aws_instance.database.public_ip}/game/insert?secret=${urlencode(file("../../secrets/database-api/secret"))}"
}

output "stop_game_url" {
    value = "http://${aws_instance.database.public_ip}/game/delete?secret=${urlencode(file("../../secrets/database-api/secret"))}"
}

output "database_public_ip" {
    value = aws_instance.database.public_ip
}

output "gamebot_public_ip" {
    value = aws_instance.gamebot.public_ip
}

output "dispatcher_public_ip" {
    value = aws_instance.dispatcher.public_ip
}

output "logger_public_ip" {
     value = aws_instance.logger.public_ip
}

output "router_public_ip" {
    value = aws_eip_association.router_ip.public_ip
}

output "scoreboard_public_ip" {
    value = aws_eip_association.scoreboard_ip.public_ip
}

output "scriptbots_public_ip" {
    value = zipmap(aws_instance.scriptbot.*.tags.Name, aws_instance.scriptbot.*.public_ip)
}

output "teaminterface_public_ip" {
    value = aws_eip_association.teaminterface_ip.public_ip
}

output "teamvms_public_ip" {
    value = {for team_id, teamvm in aws_instance.teamvm: teamvm.tags.Name => teamvm.public_ip}
}

output "services_repository_urls" {
  value = zipmap(aws_ecr_repository.service_scriptbot_image.*.name, aws_ecr_repository.service_scriptbot_image.*.repository_url)
}


