# Master account only

Purpose: enforce retention on the existing CloudTrail CloudWatch Log Group.

If the log group already exists, import once in the management stack:
terraform import module.cw.aws_cloudwatch_log_group.cloudtrail "/aws/cloudtrail/ControlTower"