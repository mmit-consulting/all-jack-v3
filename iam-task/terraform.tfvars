iam_generic_roles = {
  shared_readonly = {
    role_name = "SharedReadOnlyRole"
    trusted_services = [
      "ec2.amazonaws.com",
      "lambda.amazonaws.com"
    ]
    trust_policy_conditions = [
      {
        test     = "StringEquals"
        variable = "aws:SourceAccount"
        values   = ["123456789012"]
      },
      {
        test     = "ArnLike"
        variable = "aws:SourceArn"
        values   = ["arn:aws:lambda:us-east-1:123456789012:function:*"]
      }
    ]
    custom_policy_paths = [
      "./policies/custom-readonly-policy.json"
    ]
    aws_managed_policy_arns = [
      "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess"
    ]
    create_inline_policy      = false
    custom_inline_policy_path = null
    tags = {
      Owner = "platform"
      Env   = "dev"
    }
  }

  dev_ops_role = {
    role_name = "DevOpsUtilityRole"
    trusted_services = [
      "ec2.amazonaws.com"
    ]
    custom_policy_paths = [
      "./policies/devops-policy.json"
    ]
    aws_managed_policy_arns = [
      "arn:aws:iam::aws:policy/AWSCodeBuildDeveloperAccess"
    ]
    create_inline_policy      = true
    custom_inline_policy_path = "./policies/devops-inline.json"
    tags = {
      Owner = "devops"
      Env   = "dev"
    }
  }

    dev_ops_role = {
    role_name = "DevOpsUtilityRole"
    trusted_services = [
      "ec2.amazonaws.com"
    ]
    custom_policy_paths = [
      "./policies/devops-policy.json"
    ]
    aws_managed_policy_arns = [
      "arn:aws:iam::aws:policy/AWSCodeBuildDeveloperAccess"
    ]
    create_inline_policy      = true
    custom_inline_policy_path = "./policies/devops-inline.json"
    tags = {
      Owner = "devops"
      Env   = "dev"
    }
  }
  aig_streaming = {
    role_name = "aig-streaming"

    trusted_services = [
      "ecs-tasks.amazonaws.com"
    ]

    trust_policy_conditions = []

    custom_policy_paths = []

    aws_managed_policy_arns = []

    create_inline_policy      = true
    custom_inline_policy_path = "./policies/aig-streaming-inline.json"

    tags = {
    }
  }

  github_actions_deployer = {
    role_name        = "github-actions-deployer"
    trusted_services = ["lambda.amazonaws.com"] # optional; can be []
    trust_policy_conditions = []                # optional

    federated_principals = [
      "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
    ]
    federated_trust_policy_conditions = [
      {
        test     = "StringEquals"
        variable = "token.actions.githubusercontent.com:aud"
        values   = ["sts.amazonaws.com"]
      },
      {
        test     = "StringLike"
        variable = "token.actions.githubusercontent.com:sub"
        values   = ["repo:xxxx-yhyy/*:*"]
      }
    ]

    custom_policy_paths = []
    aws_managed_policy_arns = []
    create_inline_policy      = false
    custom_inline_policy_path = null
    tags = {}
  }


}
