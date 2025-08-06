variable "iam_generic_roles" {
  description = "Map of IAM role definitions"
  type = map(object({
    role_name        = string
    trusted_services = list(string)
    trust_policy_conditions = list(object({
      test     = string
      variable = string
      values   = list(string)
    }))
    custom_policy_paths       = list(string)
    aws_managed_policy_arns   = list(string)
    create_inline_policy      = bool
    custom_inline_policy_path = string
    tags                      = map(string)
  }))
}
