output "config_rule_name" {
  value = aws_config_config_rule.cw_log_retention_check.name
}

output "remediation_role_arn" {
  value = aws_iam_role.remediator.arn
}
