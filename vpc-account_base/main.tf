locals {
  datacenter_cidr = "10.223.0.0/16"
  fortisase_cidr  = "10.224.0.0/16"

  # Reusable rule templates
  sg_rule_templates = [
    { name = "https", from_port = 443, to_port = 443, protocol = "tcp" },
    { name = "http",  from_port = 80,  to_port = 80,  protocol = "tcp" },
    { name = "ssh",   from_port = 22,  to_port = 22,  protocol = "tcp" },
    { name = "rdp",   from_port = 3389,to_port = 3389,protocol = "tcp" },
    { name = "ping",  from_port = -1,  to_port = -1,  protocol = "icmp" },
  ]

  datacenter_rules = [
    for rule in local.sg_rule_templates : {
      description = "Allow ${rule.name} from datacenter"
      from_port   = rule.from_port
      to_port     = rule.to_port
      cidr_blocks = local.datacenter_cidr
      protocol    = rule.protocol
    }
  ]

  fortisase_rules = [
    for rule in local.sg_rule_templates : {
      description = "Allow ${rule.name} from datacenter FortiSASE"
      from_port   = rule.from_port
      to_port     = rule.to_port
      cidr_blocks = local.fortisase_cidr
      protocol    = rule.protocol
    }
  ]

  # Final list passed into the module
  default_security_group_ingress = concat(local.datacenter_rules, local.fortisase_rules)
}


######## Module call ########
module "account_base" {
  # adjust the relative path to your repo layout
  source = "../../../modules/ops/account_base"

  providers = {
    aws.nonprod_account = aws
    aws.network_account = aws.mwt-network
  }

  businessunit = var.tags["businessunit"]
  environment  = var.tags["environment"]
  region       = var.aws_region
  vpc_cidr     = var.vpc_cidr_block
  azs          = var.azs

  public_subnets  = var.public_subnets
  private_subnets = var.private_subnets

  default_security_group_ingress = local.default_security_group_ingress

  transit_gateway_id = var.transit_gateway_id
}