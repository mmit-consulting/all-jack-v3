

module "s3_org_trail_bucket" {
  source          = "../../modules/s3_org_trail_bucket"
  region          = var.region
  bucket_name     = var.bucket_name
  org_id          = var.org_id
  mgmt_account_id = var.mgmt_account_id
  trail_arn       = var.trail_arn

  # lifecycle defaults are fine (30 -> INT, 1095 expire)
  use_kms = false # set true and pass kms_key_arn if you want SSE-KMS
}
