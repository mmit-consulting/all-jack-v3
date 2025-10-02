# ---------- IAM role SSM will assume ----------
data "aws_iam_policy_document" "ssm_trust" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["ssm.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "remediator" {
  name               = var.remediation_role_name
  assume_role_policy = data.aws_iam_policy_document.ssm_trust.json
}

resource "aws_iam_role_policy_attachment" "ssm_automation_managed" {
  role       = aws_iam_role.remediator.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonSSMAutomationRole"
}

data "aws_iam_policy_document" "logs_put_retention" {
  statement {
    effect    = "Allow"
    actions   = ["logs:DescribeLogGroups", "logs:PutRetentionPolicy"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "logs_put_retention" {
  name   = "cwl-put-retention"
  policy = data.aws_iam_policy_document.logs_put_retention.json
}

resource "aws_iam_role_policy_attachment" "attach_logs_put_retention" {
  role       = aws_iam_role.remediator.name
  policy_arn = aws_iam_policy.logs_put_retention.arn
}

# ---------- AWS Config managed rule (ONLY flags missing retention) ----------
resource "aws_config_config_rule" "cw_log_retention_check" {
  name        = "cloudwatch-log-group-retention-check"
  description = "Non-compliant only when retention is missing (maxRetentionDays=3653)."

  source {
    owner             = "AWS"
    source_identifier = "CLOUDWATCH_LOG_GROUP_RETENTION_PERIOD_CHECK"
  }

  input_parameters = jsonencode({
    maxRetentionDays = var.rule_param_max_retention # 3653 → only null is non-compliant
  })

  scope {
    compliance_resource_types = ["AWS::Logs::LogGroup"]
  }
}

# ---------- Auto-remediation (SSM Automation) ----------
resource "aws_config_remediation_configuration" "cw_log_retention_fix" {
  config_rule_name = aws_config_config_rule.cw_log_retention_check.name
  target_type      = "SSM_DOCUMENT"
  target_id        = "AWSConfigRemediation-SetCloudWatchLogGroupRetention"
  automatic        = true

  maximum_automatic_attempts = 3
  retry_attempt_seconds      = 60

  parameter {
    name           = "LogGroupName"
    resource_value = "RESOURCE_ID"

  }

  parameter {
    name         = "RetentionInDays"
    static_value = tostring(var.default_retention_days)
  }

  parameter {
    name         = "AutomationAssumeRole"
    static_value = aws_iam_role.remediator.arn
  }

  depends_on = [
    aws_iam_role_policy_attachment.ssm_automation_managed,
    aws_iam_role_policy_attachment.attach_logs_put_retention
  ]
}
