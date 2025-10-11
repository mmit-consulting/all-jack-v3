variable "bucket_name" {
  description = "Existing CT log bucket in Log Archive account."
  type        = string
}

variable "prefix" {
  description = "Limit to logs path."
  type        = string
}

variable "rule_id" {
  type = string
}

variable "intelligent_tiering_after_days" {
  type    = number
  default = 0
}

variable "expiration_days" {
  type    = number
  default = 1095
}
