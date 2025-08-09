## Verify in the example of calling the module how providers are defined
provider "aws" {
  region = var.aws_region
}

provider "aws" {
  alias  = "mwt-network"
  region = var.aws_region
}

## Do not forget to add the remote backend below.