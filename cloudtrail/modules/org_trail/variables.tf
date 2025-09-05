# Cloud Watch config
variable "cw_log_group_name" {
  type    = string
  default = "/aws/organization/cloudtrail"
}

variable "cw_retention_days" {
  type    = number
  default = 365
}

variable "region" {
  type = string
}

variable "trail_name" {
  type    = string
  default = "org-central-trail"
}

variable "s3_bucket_name" {
  # bucket in mwt-log
  type = string
}

variable "is_multi_region_trail" {
  # set to false if truly single-region
  type    = bool
  default = true
}

variable "include_global_events" {
  type    = bool
  default = true
}
