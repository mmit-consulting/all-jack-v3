module "cwl_retention_stackset" {
  source         = "../../../modules/ops/cloudformation_stackset"
  stack_set_name = "CloudWatchRetentionEnforcement"
  description    = "Config rule + SSM remediation to enforce retention when missing"

  template_body = file("${path.module}/cloudformation/cwl_retention_enforcement.yaml")

  #   stack_instances = [
  #     for account in var.accounts : {
  #       account_id = account.parameters.AccountId
  #       region     = "us-east-1"
  #       parameters = {
  #         MaxRetentionDays        = "3653" # rule param: only missing retention is non-compliant
  #         DefaultRetentionToApply = "90"
  #       }
  #     }
  #   ]

  stack_instances = [
    {
      account_id = "xxxxxx"
      region     = "us-east-1"
      parameters = {
        MaxRetentionDays        = "3653"                          # rule param: only missing retention is non-compliant
        DefaultRetentionToApply = tostring(var.default_retention) # remediation will set this (e.g., 90)
      }
    }
  ]

  operation_preferences = {
    max_concurrent_percentage    = 80
    failure_tolerance_percentage = 10
    region_concurrency_type      = "SEQUENTIAL"
  }

}
