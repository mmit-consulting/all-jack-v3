module "iam_generic_roles" {
  source   = "./modules/iam-generic-role"
  for_each = var.iam_generic_roles

  role_name                 = each.value.role_name
  trusted_services          = each.value.trusted_services
  trust_policy_conditions   = each.value.trust_policy_conditions
  custom_policy_paths       = each.value.custom_policy_paths
  aws_managed_policy_arns   = each.value.aws_managed_policy_arns
  create_inline_policy      = each.value.create_inline_policy
  custom_inline_policy_path = each.value.custom_inline_policy_path
  tags                      = each.value.tags
}
