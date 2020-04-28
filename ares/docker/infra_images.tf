resource "docker_image" "database" {
  name = "ictf_4_harden_database"
  keep_locally = true
}

resource "docker_image" "gamebot" {
  name = "ictf_4_harden_gamebot"
  keep_locally = true
}

