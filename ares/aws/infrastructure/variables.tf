variable "region" {
    description = "AWS region where spawn the game"
    type = string
}

variable "vpc_cdir_block" {
    default = "172.31.0.0/16"
    description = "Ip addresses range for the VPC"
    type = string
}

variable "war_zone_subnet_cidr" {
    default = "172.31.128.0/17"
    description = "Ip addresses range for the warzone subnet"
    type = string
}

variable "master_and_db_zone_subnet_cidr" {
    default = "172.31.64.0/20"
    description = "Ip addresses range for the database and the game-master subnet"
    type = string
}

variable "router_cidr" {
    default = "172.31.172.0/24"
    description = "Router cidr block"
    type = string
}

variable "database_instance_type"  {
    default = "m5.2xlarge"
    description = "Database AWS instance type"
    type = string
}

variable "router_instance_type"  {
    default = "m5.8xlarge"
    description = "Router AWS instance type"
    type = string
}

variable "scriptbot_instance_type"  {
    default = "m5.2xlarge"
    description = "Script bot AWS instance type"
    type = string
}

variable "scoreboard_instance_type"  {
    default = "m5.2xlarge"
    description = "Scoreboard AWS instance type"
    type = string
}

variable "gamebot_instance_type"  {
    default = "m5.2xlarge"
    description = "Game bot AWS instance type"
    type = string
}

variable "dispatcher_instance_type"  {
    default = "m5.2xlarge"
    description = "Dispatcer AWS instance type"
    type = string
}

variable "logger_instance_type"  {
    default = "m5.2xlarge"
    description = "Logger AWS instance type"
    type = string
}

variable "teaminterface_instance_type"  {
    default = "m5.2xlarge"
    description = "Team interface AWS instance type"
    type = string
}

variable "teamvm_instance_type"  {
    default = "m5.2xlarge"
    description = "Team VM AWS instance type"
    type = string
}

variable "access_key"  {
    description = "AWS access key"
    type = string
}

variable "secret_key"  {
    description = "AWS secret key"
    type = string
}

variable "scriptbot_num"  {
    description = "Number of scriptbots to spawn for the game"
    type = number
}

variable "teams_num" {
    description = "Number of team to spawn for the game"
    type = number
}

variable "services_path" {
    description = "Path to the deployed services"
    type = string
}

variable "game_config_file" {
    description = "Path to the game cofiguration file"
    type = string
    
}

variable "database_registry_repository_url" {
    description = "Registry repository url pointing to the database docker image"
    type = string
    default = ""
}

variable "gamebot_registry_repository_url" {
    description = "Registry repository url pointing to the gamebot docker image"
    type = string
    default = ""
}

variable "scoreboard_registry_repository_url" {
    description = "Registry repository url pointing to the scoreboard docker image"
    type = string
    default = ""
}

variable "teaminterface_registry_repository_url" {
    description = "Registry repository url pointing to the teaminterface docker image"
    type = string
    default = ""
}

variable "scriptbot_registry_repository_url" {
    description = "Registry repository url pointing to the scriptbot docker image"
    type = string
    default = ""
}

variable "logger_registry_repository_url" {
    description = "Registry repository url pointing to the logger docker image"
    type = string
    default = ""
}

variable "router_registry_repository_url" {
    description = "Registry repository url pointing to the router docker image"
    type = string
    default = ""
}

variable "dispatcher_registry_repository_url" {
    description = "Registry repository url pointing to the dispatcher docker image"
    type = string
    default = ""
}