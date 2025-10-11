resource "aws_cloudwatch_log_group" "cloudtrail" {
  name              = var.log_group_name
  retention_in_days = var.retention_days
  skip_destroy      = true # never destroy CT logs via TF
}
