module "iam_generic_role" {
  source = "./modules/iam-generic-role"

  role_name        = var.iam_generic_role.role_name
  trusted_services = var.iam_generic_role.trusted_services

  custom_policy_paths = var.iam_generic_role.custom_policy_paths

  aws_managed_policy_arns = var.iam_generic_role.aws_managed_policy_arns

  create_inline_policy      = var.iam_generic_role.create_inline_policy
  custom_inline_policy_path = var.iam_generic_role.custom_inline_policy_path

  tags = var.iam_generic_role.tags
}
