variable "log_group_name" {
  type    = string
  default = "/aws/cloudtrail/ControlTower"
}

variable "retention_days" {
  type    = number
  default = 365
}

