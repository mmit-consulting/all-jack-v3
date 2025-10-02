
# ---------- Package Lambda code from a separate python file ----------
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = var.lambda_source_dir
  output_path = "${path.module}/build/cwl_retention_rule.zip"
}

# ---------- Lambda IAM ----------
resource "aws_iam_role" "lambda_role" {
  name = var.lambda_role_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect : "Allow"
        Principal : {
          Service : "lambda.amazonaws.com"
        }
        Action : "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "lambda_api" {
  name = "lambda-cwl-describe-puteval"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect : "Allow"
        Action : ["logs:DescribeLogGroups"]
        Resource : "*"
      },
      {
        Effect : "Allow"
        Action : ["config:PutEvaluations"]
        Resource : "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_api_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_api.arn
}

# ---------- Lambda function ----------
resource "aws_lambda_function" "rule" {
  function_name    = var.lambda_function_name
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 60
}

resource "aws_lambda_permission" "allow_config" {
  statement_id  = "AllowConfigInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rule.function_name
  principal     = "config.amazonaws.com"
}

# ---------- Custom AWS Config rule (Lambda-backed) ----------
resource "aws_config_config_rule" "rule" {
  name        = var.rule_name
  description = "NON_COMPLIANT when a CloudWatch log group has no retention set (Lambda-backed)."

  source {
    owner             = "CUSTOM_LAMBDA"
    source_identifier = aws_lambda_function.rule.arn

    # Event-driven: evaluate on resource change
    source_detail {
      event_source = "aws.config"
      message_type = "ConfigurationItemChangeNotification"
      # optional:
      maximum_execution_frequency = var.maximum_execution_frequency
    }

    # Periodic: sweep all groups
    source_detail {
      event_source = "aws.config"
      message_type = "ScheduledNotification"
      # optional:
      maximum_execution_frequency = var.maximum_execution_frequency
    }
  }

  scope {
    compliance_resource_types = ["AWS::Logs::LogGroup"]
  }
}

# ---------- SSM Automation IAM role for remediation ----------
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

# ---------- Auto-remediation wiring (SSM Automation runbook) ----------
resource "aws_config_remediation_configuration" "retention_fix" {
  config_rule_name = aws_config_config_rule.rule.name
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
