output "config_rule_name" {
  value = aws_config_config_rule.rule.name
}

output "lambda_name" {
  value = aws_lambda_function.rule.function_name
}

output "remediation_role_arn" {
  value = aws_iam_role.remediator.arn
}
