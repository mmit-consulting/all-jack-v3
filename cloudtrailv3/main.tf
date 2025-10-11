######### mwt-master #########
module "org_logging_controls1" {
  source = "./modules/org_logging_controls"

  # CloudWatch retention
  enable_cw_retention       = true
  cloudtrail_log_group_name = "/aws/cloudtrail/ControlTower"
  cloudwatch_retention_days = 365

  # Config retention
  enable_config_retention = true
  config_retention_days   = 2557 # ~7 years
}


######### mwt-log #########
module "org_logging_controls2" {
  source = "./modules/org_logging_controls"

  # S3 lifecycle
  enable_s3_lifecycle            = true
  s3_bucket_name                 = "aws-controltower-logs-<org>-<region>"
  s3_prefix                      = "AWSLogs/"
  s3_lifecycle_rule_id           = "retain-3y-int-tiering"
  intelligent_tiering_after_days = 30
  expiration_days                = 1095 # ~3 years

  # Config retention
  enable_config_retention = true
  config_retention_days   = 2557 # ~7 years
}

######### mwt-<any account> #########
module "org_logging_controls3" {
  source = "./modules/org_logging_controls"

  # Config retention
  enable_config_retention = true
  config_retention_days   = 2557 # ~7 years
}
