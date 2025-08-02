# Strategies to enable EBS encryption

## Introduction

To **specify EBS encryption for EC2 instances** in an Elastic Beanstalk environment, **you cannot do it directly via Terraform settings** in the `aws_elastic_beanstalk_environment` resource, because Beanstalk does not expose EBS encryption settings directly.

Reference links:

- https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/elastic_beanstalk_environment#option-settings
- https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/command-options-general.html#command-options-general-autoscalinglaunchconfiguration

## Option1: Use a Custom AMI with encrypted root volume

- Create your own AMI with an **encrypted EBS root volume**
- Use this AMI by setting:

```hcl
setting {
  namespace = "aws:autoscaling:launchconfiguration"
  name      = "ImageId"
  value     = "ami-xxxxxxxxxxxxxxx"
}
```

This way, all instances launched by Beanstalk will use the encrypted EBS volume from the AMI.

## Option2: Use a default EBS encryption policy in your AWS account

- Enable default encryption for all new EBS volumes in the region:

```bash
aws ec2 enable-ebs-encryption-by-default --region us-east-1
```

This will apply automatically to EBS volumes created by Beanstalk (via launch template), no code changes needed.

In our case, we are going to apply this one, so I suggesst we apply it, and test it on internal account

### To test, after changing the setings:

**Option A - Easiest (but disruptive)**:

- Go to the Beanstalk Console
- Select your environment
- Click **"Rebuild Environment"**

This will terminate current EC2s and recreate them using the existing Launch Template (which will now respect the new encryption policy).

<br/>

**Option B – Safer (no downtime)**:

- Go to **Beanstalk Console** / or **your terraform code**
- Do a minor configuration change (e.g., increase instance type, then revert it)
- This forces a new Launch Template version → new EC2s launched → encrypted

**Verify EBS Encryption**

After the new EC2 instaces are up, to verify:

Console: Go to EC2 -> instances -> your instance -> check the volume -> Encryption should be enabled

CLI

```bash
aws ec2 describe-volumes --filters Name=attachment.instance-id,Values=<instance-id> --region us-east-1 --query "Volumes[*].Encrypted"
```
