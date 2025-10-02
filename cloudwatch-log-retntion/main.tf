module "cwl_retention" {
  source                 = "../../../modules/cwl_retention"
  region                 = "us-east-1"
  default_retention_days = 90
  # rule_param_max_retention stays 3653 by default (only missing retention is non-compliant)
  # remediation_role_name can be left default or overridden per account
}
