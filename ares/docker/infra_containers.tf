provider "docker" {
  host = "unix:///var/run/docker.sock"
}

resource "docker_container" "database" {
  image = docker_image.database.latest
  name  = "database"
  hostname = "database"
  domainname = "database"
  start = true

  # ports {
  #   internal = 80
  #   external = 80
  # }
}

resource "docker_container" "gamebot" {
  image = docker_image.gamebot.latest
  name  = "gamebot"
  hostname = "gamebot"
  domainname = "gamebot"
  start = true

  entrypoint = ["while 1; do echo 'hhi'; done"]
  depends_on = [docker_container.database]
}