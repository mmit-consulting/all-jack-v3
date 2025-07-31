output "role_name" {
  value = aws_iam_role.this.name
}

output "role_arn" {
  value = aws_iam_role.this.arn
}

output "custom_managed_policy_arns" {
  value = [for p in aws_iam_policy.custom_managed : p.arn]
}

output "aws_managed_policy_arns" {
  value = var.aws_managed_policy_arns
}
