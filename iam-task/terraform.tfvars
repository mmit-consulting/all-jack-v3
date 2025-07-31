iam_generic_role = {
  role_name = "SharedReadOnlyRole"
  trusted_services = [
    "ec2.amazonaws.com",
    "lambda.amazonaws.com"
  ]

  custom_policy_paths = [
    "./policies/custom-readonly-policy.json"
  ]

  aws_managed_policy_arns = [
    "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess",
    "arn:aws:iam::aws:policy/AWSXRayReadOnlyAccess"
  ]

  create_inline_policy      = false
  custom_inline_policy_path = null

  tags = {
    Owner = "terraform"
  }
}