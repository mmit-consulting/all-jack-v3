variable "log_archive_account_id" {
  type = string
}

variable "management_account_id" {
  type = string
}

variable "log_bucket_name" {
  type = string
}

variable "org_trail_log_group" {
  type    = string
  default = "/aws-controltower/CloudTrailLogs"
}
