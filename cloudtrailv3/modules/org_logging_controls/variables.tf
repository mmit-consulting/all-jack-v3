############################
# Flags (all default to false)
############################
variable "enable_config_retention" {
  description = "If true, manage AWS Config retention in this account."
  type        = bool
  default     = false
}

variable "enable_cw_retention" {
  description = "If true, manage CloudWatch retention for the CloudTrail log group."
  type        = bool
  default     = false
}

variable "enable_s3_lifecycle" {
  description = "If true, manage lifecycle configuration on the existing S3 bucket."
  type        = bool
  default     = false
}

############################
# 1) AWS Config retention
############################
variable "config_retention_days" {
  description = "AWS Config retention in days (30..2557). Use 2557 for ~7 years."
  type        = number
  default     = 2557
}

############################
# 2) CloudWatch log group retention (CloudTrail)
############################
variable "cloudtrail_log_group_name" {
  description = "Existing CloudTrail log group name (e.g., /aws/cloudtrail/ControlTower)."
  type        = string
  default     = "/aws/cloudtrail/ControlTower"
}

variable "cloudwatch_retention_days" {
  description = "CloudWatch retention in days (e.g., 365 for one year)."
  type        = number
  default     = 365
}

############################
# 3) S3 lifecycle (existing bucket)
############################
variable "s3_bucket_name" {
  description = "Existing Control Tower log bucket name (lives in Log Archive account). Required if enable_s3_lifecycle=true."
  type        = string
  default     = null
}

variable "s3_prefix" {
  description = "Prefix to scope lifecycle to logs only."
  type        = string
  default     = "AWSLogs/"
}

variable "s3_lifecycle_rule_id" {
  description = "Lifecycle rule identifier."
  type        = string
  default     = "retain-3y-int-tiering"
}

variable "intelligent_tiering_after_days" {
  description = "Days before transitioning to Intelligent-Tiering (0 = immediately)."
  type        = number
  default     = 30
}

variable "expiration_days" {
  description = "Expire objects after N days (e.g., 1095 for ~3 years)."
  type        = number
  default     = 1095
}
