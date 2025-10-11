module "s3_lifecycle" {
  source = "../modules/s3_lifecycle_existing"

  bucket_name                    = "aws-controltower-logs-<org>-<region>"
  prefix                         = "AWSLogs/"
  rule_id                        = "retain-3y-int-tiering"
  intelligent_tiering_after_days = 30
  expiration_days                = 1095 # ~3 years
}
