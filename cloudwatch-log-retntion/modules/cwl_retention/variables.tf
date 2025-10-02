variable "default_retention_days" {
  description = "Retention that remediation will set on non-compliant (missing-retention) log groups."
  type        = number
  default     = 90
}

variable "rule_param_max_retention" {
  description = "Config rule parameter; set to 3653 (10 years) so only 'no retention' is non-compliant."
  type        = number
  default     = 3653
}

variable "remediation_role_name" {
  description = "IAM role name for SSM Automation to run PutRetentionPolicy."
  type        = string
  default     = "cw-retention-remediator"
}
