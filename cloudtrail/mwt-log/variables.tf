variable "region" {
  type = string
}
variable "bucket_name" {
  type = string
}
variable "org_id" {
  # "oc3rtgmpo8" (no "o-")
  type = string
}
variable "mgmt_account_id" {
  # "271563910642"
  type = string
}
variable "trail_arn" {
  # from Stack B output
  type = string
}
