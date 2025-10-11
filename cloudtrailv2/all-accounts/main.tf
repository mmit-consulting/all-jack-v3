
module "config_retention" {
  source         = "../modules/config_retention"
  retention_days = 2557 # ~7 years
}
