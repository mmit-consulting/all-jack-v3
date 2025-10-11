resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = var.bucket_name

  rule {
    id     = var.rule_id
    status = "Enabled"

    filter { prefix = var.prefix } # usually "AWSLogs/"

    transition {
      days          = var.intelligent_tiering_after_days
      storage_class = "INTELLIGENT_TIERING"
    }

    expiration { days = var.expiration_days } # ~3 years = 1095
  }
}
