variable "iam_generic_role" {
  description = "Parameters to configure the generic IAM role module"
  type = object({
    role_name                 = string
    trusted_services          = list(string)
    custom_policy_paths       = list(string)
    aws_managed_policy_arns   = list(string)
    create_inline_policy      = bool
    custom_inline_policy_path = string
    tags                      = map(string)
  })
  default = {
    role_name                 = ""
    trusted_services          = []
    custom_policy_paths       = []
    aws_managed_policy_arns   = []
    create_inline_policy      = false
    custom_inline_policy_path = null
    tags                      = {}
  }
}
