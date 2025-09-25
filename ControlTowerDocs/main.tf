############################################
# 1) CloudTrail S3 lifecycle (Log Archive)
############################################
module "ct_s3_lifecycle" {
  source = "../../../modules/ops/cloudformation_stackset"

  stack_set_name = "CloudTrail-S3-Lifecycle-3y"
  description    = "CloudTrail logs: 30d -> INT, expire @ 3y"
  template_body  = file("${path.module}/cloudformation/s3-cloudtrail-lifecycle.yaml")

  stack_instances = [
    {
      account_id = var.log_archive_account_id
      region     = "us-east-1"
      parameters = {
        BucketName     = var.log_bucket_name
        TransitionDays = "30"
        ExpireDays     = "1095"
      }
    }
  ]

  operation_preferences = {
    max_concurrent_percentage    = 100
    failure_tolerance_percentage = 0
    region_concurrency_type      = "SEQUENTIAL"
  }
}

############################################
# 2) AWS Config S3 lifecycle (Log Archive)
############################################
module "config_s3_lifecycle" {
  source = "../../../modules/ops/cloudformation_stackset"

  stack_set_name = "Config-S3-Lifecycle-3y"
  description    = "AWS Config logs: 30d -> INT, expire @ 3y"
  template_body  = file("${path.module}/cloudformation/s3-config-lifecycle.yaml")

  stack_instances = [
    {
      account_id = var.log_archive_account_id
      region     = "us-east-1"
      parameters = {
        BucketName     = var.log_bucket_name
        TransitionDays = "30"
        ExpireDays     = "1095"
      }
    }
  ]

  operation_preferences = {
    max_concurrent_percentage    = 100
    failure_tolerance_percentage = 0
    region_concurrency_type      = "SEQUENTIAL"
  }
}

########################################################
# 3) CloudWatch Logs retention for org trail (Management)
########################################################
module "cw_retention_org_trail" {
  source = "../../../modules/ops/cloudformation_stackset"

  stack_set_name = "CloudTrail-CW-Retention-365d"
  description    = "Set CW Logs retention for org trail to 365 days"
  template_body  = file("${path.module}/cloudformation/cwlogs-retention-custom.yaml")

  stack_instances = [
    {
      account_id = var.management_account_id
      region     = "us-east-1"
      parameters = {
        LogGroupName    = var.org_trail_log_group
        RetentionInDays = "365"
      }
    }
  ]

  operation_preferences = {
    max_concurrent_percentage    = 100
    failure_tolerance_percentage = 0
    region_concurrency_type      = "SEQUENTIAL"
  }
}

########################################################
# 4) AWS Config service retention (optional, safe)
########################################################
module "config_service_retention" {
  source = "../../../modules/ops/cloudformation_stackset"

  stack_set_name = "AWSConfig-Service-Retention-3y"
  description    = "Set AWS Config retention to 1095 days via custom resource"
  template_body  = file("${path.module}/cloudformation/config-retention-custom.yaml")

  stack_instances = [
    FOR LOOP HERE
  ]

  operation_preferences = {
    max_concurrent_percentage    = 100
    failure_tolerance_percentage = 0
    region_concurrency_type      = "SEQUENTIAL"
  }
}
