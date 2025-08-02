# terraform-aws-iam-generic-role

This Terraform module creates a generic IAM role with:

- Custom trust policy
- Customer-managed policies (from JSON files)
- AWS-managed policies (via ARNs)
- Optional inline policy (from a separate JSON file)

---

## 🛠️ Usage

```hcl
module "iam_generic_role" {
  source = "./modules/iam-generic-role"

  role_name        = "my-readonly-role"
  trusted_services = ["ec2.amazonaws.com", "lambda.amazonaws.com"]

  custom_policy_paths       = ["${path.module}/policies/custom-policy-1.json"]
  aws_managed_policy_arns   = ["arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"]

  create_inline_policy      = true
  custom_inline_policy_path = "${path.module}/policies/inline-policy.json"

  tags = {
    Environment = "dev"
    Owner       = "mahdi"
  }
}
```

---

## 📥 Input Variables

| Name                        | Type           | Description                                                             | Default                                         |
| --------------------------- | -------------- | ----------------------------------------------------------------------- | ----------------------------------------------- |
| `role_name`                 | `string`       | Name of the IAM role                                                    | **required**                                    |
| `trusted_services`          | `list(string)` | AWS services/entities allowed to assume this role                       | `["ec2.amazonaws.com", "lambda.amazonaws.com"]` |
| `tags`                      | `map(string)`  | Tags to assign to the IAM role                                          | `{}`                                            |
| `custom_policy_paths`       | `list(string)` | Paths to custom JSON files for customer-managed policies                | `[]`                                            |
| `aws_managed_policy_arns`   | `list(string)` | List of AWS managed policy ARNs to attach                               | `[]`                                            |
| `create_inline_policy`      | `bool`         | Whether to attach an inline policy                                      | `false`                                         |
| `custom_inline_policy_path` | `string`       | Path to inline policy JSON file (used if `create_inline_policy = true`) | `null`                                          |

---

## 📤 Outputs

| Name                         | Description                               |
| ---------------------------- | ----------------------------------------- |
| `role_name`                  | The name of the IAM role                  |
| `role_arn`                   | The ARN of the IAM role                   |
| `custom_managed_policy_arns` | List of ARNs of created customer policies |
| `aws_managed_policy_arns`    | List of attached AWS managed policy ARNs  |

---

## 📁 Folder Structure

```
.
├── main.tf
├── variables.tf
├── outputs.tf
└── README.md
```

---

## 🧪 Notes

- This module assumes policy files are valid JSON and follow AWS IAM policy structure.
- IAM policy size limits apply (max 6,144 characters per policy document).
- Inline policies are optional and only included if `create_inline_policy = true`.
