variable "bucket_name" {
  type = string
}

variable "region" {
  type = string
}

variable "org_id" {
  # e.g. "oc3rtgmpo8" (WITHOUT the leading "o-")
  type = string
}

variable "mgmt_account_id" {
  # e.g. "271563910642"
  type = string
}

variable "trail_arn" {
  # arn:aws:cloudtrail:REGION:ACCT:trail/NAME
  type = string
}

# lifecycle controls
variable "transition_days" {
  type    = number
  default = 30
}

variable "expire_days" {
  type    = number
  default = 1095
}

# encryption
variable "use_kms" {
  type    = bool
  default = false
}

variable "kms_key_arn" {
  # required if use_kms = true
  type    = string
  default = ""
}


