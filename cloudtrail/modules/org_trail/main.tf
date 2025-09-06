
resource "aws_cloudwatch_log_group" "trail" {
  name              = var.cw_log_group_name
  retention_in_days = var.cw_retention_days
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "trail_to_cw" {
  name               = "${var.trail_name}-cw-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

resource "aws_iam_role_policy" "trail_to_cw" {
  role = aws_iam_role.trail_to_cw.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect : "Allow",
      Action : [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      Resource : "${aws_cloudwatch_log_group.trail.arn}:*"
    }]
  })
}

resource "aws_cloudtrail" "org" {
  name                          = var.trail_name
  s3_bucket_name                = var.s3_bucket_name
  is_organization_trail         = true
  is_multi_region_trail         = var.is_multi_region_trail
  include_global_service_events = var.include_global_events
  enable_log_file_validation    = true

  cloud_watch_logs_group_arn = aws_cloudwatch_log_group.trail.arn
  cloud_watch_logs_role_arn  = aws_iam_role.trail_to_cw.arn

  event_selector {
    include_management_events = true
    read_write_type           = "All"
  }
}
