output "bucket_name" {
  value = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  value = aws_s3_bucket.this.arn
}

output "policy_json" {
  value = data.aws_iam_policy_document.bucket.json
}
