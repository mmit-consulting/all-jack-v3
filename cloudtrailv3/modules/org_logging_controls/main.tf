############################
# 1) AWS Config retention
############################
resource "aws_config_retention_configuration" "this" {
  count                    = var.enable_config_retention ? 1 : 0
  retention_period_in_days = var.config_retention_days
}

############################
# 2) CloudWatch Logs retention (CloudTrail log group)
############################
# NOTE: If the log group already exists, import it once:
#   terraform import module.<name>.aws_cloudwatch_log_group.cloudtrail "<log group name>"
resource "aws_cloudwatch_log_group" "cloudtrail" {
  count             = var.enable_cw_retention ? 1 : 0
  name              = var.cloudtrail_log_group_name
  retention_in_days = var.cloudwatch_retention_days
  skip_destroy      = true
}

############################
# 3) S3 Lifecycle on EXISTING bucket (Control Tower log bucket)
############################
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  count  = var.enable_s3_lifecycle ? 1 : 0
  bucket = var.s3_bucket_name

  rule {
    id     = var.s3_lifecycle_rule_id
    status = "Enabled"

    # Keep lifecycle scoped only to the logs prefix
    filter {
      prefix = var.s3_prefix
    }

    transition {
      days          = var.intelligent_tiering_after_days
      storage_class = "INTELLIGENT_TIERING"
    }

    expiration {
      days = var.expiration_days
    }
  }
}
