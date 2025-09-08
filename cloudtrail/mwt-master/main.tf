module "org_trail" {
  source                = "../modules/org_trail"
  region                = var.region
  s3_bucket_name        = var.s3_bucket_name
  trail_name            = "org-central-trail"
  cw_log_group_name     = "/aws/organization/cloudtrail"
  cw_retention_days     = 365
  is_multi_region_trail = true
}
