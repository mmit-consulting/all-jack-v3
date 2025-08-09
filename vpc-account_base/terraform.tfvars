aws_region     = "us-east-1"
vpc_cidr_block = "10.103.0.0/16"

azs = [
  "us-east-1a",
  "us-east-1b"
]

public_subnets = {
  "serverless-dev-public-us-east-1a"  = "10.103.101.0/24"
  "serverless-prod-public-us-east-1a" = "10.103.102.0/24"
  "serverless-prod-public-us-east-1b" = "10.103.103.0/24"
}

private_subnets = {
  "serverless-dev-private-us-east-1a"  = "10.103.1.0/24"
  "serverless-prod-private-us-east-1a" = "10.103.2.0/24"
  "serverless-prod-private-us-east-1b" = "10.103.3.0/24"
}

tags = {
  application  = "vpcnetwork"
  owner        = "jmezinko"
  name         = "ecom-serverless"
  environment  = "prod"
  department   = "infrastructure"
  businessunit = "midwesttape"
}

# Get this value from our old terraform.tfvars
# transit_gateway_id = "tgw-xxxxxxxxxxxxxxxxx"
