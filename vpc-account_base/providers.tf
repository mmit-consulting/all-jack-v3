provider "aws" {
  region = var.aws_region
}

provider "aws" {
  alias  = "mwt-network"
  region = var.aws_region
}