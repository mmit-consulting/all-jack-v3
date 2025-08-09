variable "aws_region" {
  description = "AWS region for the deployment"
  type        = string
}

variable "vpc_cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "azs" {
  description = "Availability Zones to use"
  type        = list(string)
}

# Ready-made NAME => CIDR maps (no zipmap)
variable "public_subnets" {
  description = "Map of public subnet names to CIDR blocks"
  type        = map(string)
}

variable "private_subnets" {
  description = "Map of private subnet names to CIDR blocks"
  type        = map(string)
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
}

# Pass through only if your module takes it; default empty to avoid dup rules
variable "default_security_group_ingress" {
  description = "Ingress rules for the default security group (if required by module)"
  type = list(object({
    description = optional(string)
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = []
}

# Optional TGW support (set in tfvars only if needed)
variable "transit_gateway_id" {
  description = "Transit Gateway ID to attach routes to (optional)"
  type        = string
  default     = null
}