module "cwl_retention_enforcer" {
  source = "../../../modules/ops/cwl_retention_enforcer"

  # Optional overrides:
  rule_name                   = "cloudwatch-log-group-retention-missing"
  maximum_execution_frequency = "One_Hour"
  default_retention_days      = 90
  lambda_function_name        = "config-cwl-retention-missing"
  lambda_role_name            = "config-cwl-retention-rule"
  remediation_role_name       = "cw-retention-remediator"
  lambda_source_dir           = "${path.module}/../../../modules/ops/cwl_retention_enforcer/lambda" # only if you move the py file outside the module
}
