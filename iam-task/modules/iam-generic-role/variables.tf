variable "role_name" {
  description = "Name of the IAM role to create"
  type        = string
}

variable "trusted_services" {
  description = "List of services/entities allowed to assume this role"
  type        = list(string)
}

variable "trust_policy_conditions" {
  description = "Optional conditions to include in the trust policy"
  type = list(object({
    test     = string
    variable = string
    values   = list(string)
  }))
  default = []
}

variable "federated_principals" {
  description = "List of Federated principals (e.g., OIDC provider ARNs)."
  type        = list(string)
  default     = []
}

variable "federated_trust_policy_conditions" {
  description = "Optional conditions for the federated trust statement."
  type = list(object({
    test     = string
    variable = string
    values   = list(string)
  }))
  default = []
}

variable "tags" {
  description = "Tags to apply to the IAM role"
  type        = map(string)
  default     = {}
}

variable "custom_policy_paths" {
  description = "List of custom JSON policy file paths to create as customer-managed policies"
  type        = list(string)
  default     = []
}

variable "aws_managed_policy_arns" {
  description = "List of AWS managed policy ARNs to attach to the role"
  type        = list(string)
  default     = []
}

variable "create_inline_policy" {
  description = "Whether to also attach an inline policy"
  type        = bool
  default     = false
}

variable "custom_inline_policy_path" {
  description = "Path to the custom JSON policy for inline attachment"
  type        = string
  default     = null
}
