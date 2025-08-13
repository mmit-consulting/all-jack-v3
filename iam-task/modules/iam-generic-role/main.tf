# ─────────────────────────────────────────────────────────────────────
# This module creates a generic IAM role.
# It accepts a custom trust policy, and allows attaching:
# - Custom managed policies (from JSON files)
# - AWS managed policies (by ARN)
# - Optional inline policy (from a separate JSON file)
# ─────────────────────────────────────────────────────────────────────

##########################
# Role Creation
##########################

# Assume role trust policy
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = var.trusted_services
    }
    actions = ["sts:AssumeRole"]

    dynamic "condition" {
      for_each = var.trust_policy_conditions
      content {
        test     = condition.value.test
        variable = condition.value.variable
        values   = condition.value.values
      }
    }

  }
}

# IAM Role definition
resource "aws_iam_role" "this" {
  name               = var.role_name
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags               = var.tags
}

##########################
# IAM Instance Profile
##########################

resource "aws_iam_instance_profile" "this" {
  name = var.role_name
  role = aws_iam_role.this.name
  tags = var.tags
}


##########################
# Customer Managed Policies
##########################

# Load each custom policy JSON file and create a managed policy for it
data "local_file" "custom_policies" {
  for_each = { for path in var.custom_policy_paths : path => path }
  filename = each.value
}

# Create the customer managed policies
resource "aws_iam_policy" "custom_managed" {
  for_each    = data.local_file.custom_policies
  name        = "${var.role_name}-${replace(replace(basename(each.key), ".json", ""), "_", "-")}"
  description = "Custom managed policy for ${var.role_name} from ${each.key}"
  policy      = each.value.content
}

# attach customer managed policies to the role
resource "aws_iam_role_policy_attachment" "custom_managed_attach" {
  for_each   = aws_iam_policy.custom_managed
  role       = aws_iam_role.this.name
  policy_arn = each.value.arn
}

##########################
# AWS Managed Policies
##########################

# Attach AWS managed policies
resource "aws_iam_role_policy_attachment" "aws_managed_attach" {
  for_each   = toset(var.aws_managed_policy_arns)
  role       = aws_iam_role.this.name
  policy_arn = each.value
}

##########################
# Inline Policies (optional)
##########################

# Optional: attach inline policy if enabled and path is provided
data "local_file" "inline_custom" {
  count    = var.create_inline_policy && var.custom_inline_policy_path != null ? 1 : 0
  filename = var.custom_inline_policy_path
}

resource "aws_iam_role_policy" "inline" {
  count  = var.create_inline_policy && var.custom_inline_policy_path != null ? 1 : 0
  name   = "${var.role_name}-inline-policy"
  role   = aws_iam_role.this.id
  policy = data.local_file.inline_custom[0].content
}
