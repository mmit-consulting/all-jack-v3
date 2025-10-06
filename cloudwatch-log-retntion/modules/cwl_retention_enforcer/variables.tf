# ---- Behavior ----
variable "rule_name" {
  description = "Custom AWS Config rule name."
  type        = string
  default     = "cloudwatch-log-group-retention-missing"
}

variable "maximum_execution_frequency" {
  description = "How often the rule runs periodically."
  type        = string
  default     = "TwentyFour_Hours" # One_Hour|Three_Hours|Six_Hours|Twelve_Hours|TwentyFour_Hours
}

variable "default_retention_days" {
  description = "Retention days that remediation will set on non-compliant log groups."
  type        = number
  default     = 90
}

# ---- IAM names ----
variable "lambda_function_name" {
  description = "Lambda function name for the custom rule."
  type        = string
  default     = "config-cwl-retention-missing"
}

variable "lambda_role_name" {
  description = "IAM role name for the Lambda."
  type        = string
  default     = "config-cwl-retention-rule"
}

variable "remediation_role_name" {
  description = "IAM role name that SSM Automation assumes to call PutRetentionPolicy."
  type        = string
  default     = "cw-retention-remediator"
}

# ---- Code packaging ----
variable "lambda_source_dir" {
  description = "Directory containing lambda_function.py (and optional deps)."
  type        = string
  default     = "${path.module}/lambda"
}


variable "notification_emails" {
  type = any
}
