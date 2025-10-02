# cwl_retention_enforcer

This Terraform module enforces a **CloudWatch Logs retention policy** across an AWS account.  

It uses **AWS Config + Lambda + SSM Automation** to detect CloudWatch log groups without a retention policy and automatically set them to a default (e.g., 90 days).

---

## Features
- **Detection**: AWS Config evaluates all `AWS::Logs::LogGroup` resources.
  - Marks as **NON_COMPLIANT** when no retention policy is set.
  - Marks as **COMPLIANT** when retention is set.
- **Evaluation engine**: 
  - Event-driven (on resource changes).
  - Periodic (sweeps all log groups at defined frequency).
- **Remediation**:
  - Automatic fix using an **SSM Automation runbook** (`CWL-SetLogGroupRetention`).
  - Sets the retention to a configurable number of days (default: `90`).
- **IAM least privilege**:
  - Lambda only needs `logs:DescribeLogGroups` + `config:PutEvaluations`.
  - SSM role only needs `logs:PutRetentionPolicy`.

---

## Module structure
- **Lambda function** (`lambda_function.py`)
  - Custom AWS Config rule evaluator.
  - Detects whether retention is set for each log group.
- **aws_config_config_rule**
  - Calls the Lambda on changes or periodically.
- **aws_ssm_document**
  - Custom remediation runbook that sets retention on non-compliant log groups.
- **aws_config_remediation_configuration**
  - Wires the Config rule to the SSM runbook.
- **IAM roles/policies**
  - Execution role for Lambda.
  - Remediation role for SSM Automation.

---

## 🔧 Usage

```hcl
module "cwl_retention_enforcer" {
  source = "../../../modules/ops/cwl_retention_enforcer"

  # Optional overrides
  rule_name                   = "cloudwatch-log-group-retention-missing"
  maximum_execution_frequency = "One_Hour"   # Re-check interval: One_Hour | Three_Hours | Six_Hours | Twelve_Hours | TwentyFour_Hours
  default_retention_days      = 90           # Retention days to enforce
  lambda_function_name        = "config-cwl-retention-missing"
  lambda_role_name            = "config-cwl-retention-rule"
  remediation_role_name       = "cw-retention-remediator"

  # Path to the Lambda source code
  lambda_source_dir           = "${path.module}/lambda"
}
