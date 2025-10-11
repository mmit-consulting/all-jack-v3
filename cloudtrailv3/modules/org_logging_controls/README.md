# org_logging_controls

A single, toggleable Terraform module to **tune retention** and **lifecycle** .

It can manage up to three things, each behind a boolean flag (all **false by default**):

1. **AWS Config retention** (`enable_config_retention`)
2. **CloudWatch Logs retention** for the **CloudTrail log group** (`enable_cw_retention`) - needs to be imported first  `terraform import module.<name>.aws_cloudwatch_log_group.cloudtrail "<log group name>"`
3. **S3 lifecycle** on the **existing Control Tower log bucket** (`enable_s3_lifecycle`)

> Use this when Control Tower already set up your org trail, log archive bucket, and AWS Config, and you only want to enforce retention & lifecycle.

---

## Inputs (most important)

| Variable | Type | Default | When used |
|---|---|---|---|
| `enable_config_retention` | bool | `false` | Turn on Config history retention management in the current account/region |
| `config_retention_days` | number | `2557` | Days to keep AWS Config history (30..2557) |
| `enable_cw_retention` | bool | `false` | Manage CloudWatch Logs retention for CloudTrail log group |
| `cloudtrail_log_group_name` | string | `/aws/cloudtrail/ControlTower` | Name of the existing CloudTrail log group |
| `cloudwatch_retention_days` | number | `365` | Days to keep CloudTrail logs in CloudWatch |
| `enable_s3_lifecycle` | bool | `false` | Manage lifecycle on an existing S3 bucket (Log Archive account) |
| `s3_bucket_name` | string | `null` | **Required** when `enable_s3_lifecycle=true` |
| `s3_prefix` | string | `AWSLogs/` | Restrict lifecycle to logs path |
| `s3_lifecycle_rule_id` | string | `retain-3y-int-tiering` | Rule ID |
| `intelligent_tiering_after_days` | number | `0` | Transition to Intelligent-Tiering after N days |
| `expiration_days` | number | `1095` | Expire logs after N days (~3y) |

---

## Usage patterns

### Management account - mwt-master (CloudWatch only)

```hcl
module "org_logging_controls" {
  source = "./modules/org_logging_controls"

  # CloudWatch retention
  enable_cw_retention       = true
  cloudtrail_log_group_name = "/aws/cloudtrail/ControlTower"
  cloudwatch_retention_days = 365

  # Config retention
  enable_config_retention = true
  config_retention_days   = 2557 # ~7 years
}
```

Import once if the log group already exists

```bash
terraform import module.org_logging_controls.aws_cloudwatch_log_group.cloudtrail "/aws/cloudtrail/ControlTower"
```

### Log Archive account (S3 lifecycle only)

```hcl
module "org_logging_controls" {
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
```

### All other accounts

```hcl
module "org_logging_controls3" {
  source = "./modules/org_logging_controls"

  # Config retention
  enable_config_retention = true
  config_retention_days   = 2557 # ~7 years
}
```

## Notes

- CloudWatch Log Group ownership: if Control Tower/CloudTrail created it, Terraform doesn’t know it exists. Import once to avoid “already exists” errors
- If you cannot import, execute aws logs put-retention-policy out-of-band (CLI) and keep enable_cw_retention=false.
- S3 lifecycle is whole-resource: aws_s3_bucket_lifecycle_configuration manages the entire lifecycle configuration for that bucket. Consolidate lifecycle management to this module to avoid conflicts.
- No creation of buckets/trails: This module does not create S3 buckets or org trails. It only tunes retention/lifecycle on existing resources.