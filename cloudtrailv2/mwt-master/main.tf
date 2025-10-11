module "cw" {
  source = "../modules/cw_log_retention"

  log_group_name = "/aws/cloudtrail/ControlTower"
  retention_days = 365
}
