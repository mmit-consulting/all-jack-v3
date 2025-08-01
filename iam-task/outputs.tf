output "iam_generic_role_arns" {
  value = {
    for k, mod in module.iam_generic_roles :
    k => mod.role_arn
  }
}
