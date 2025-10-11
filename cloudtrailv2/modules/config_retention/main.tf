resource "aws_config_retention_configuration" "this" {
  retention_period_in_days = var.retention_days # 30..2557
}
