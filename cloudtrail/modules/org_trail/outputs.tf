output "trail_arn" {
  value = aws_cloudtrail.org.arn
}

output "log_group_arn" {
  value = aws_cloudwatch_log_group.trail.arn
}

output "cw_role_arn" {
  value = aws_iam_role.trail_to_cw.arn
}
