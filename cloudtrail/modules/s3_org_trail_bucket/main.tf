resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    dynamic "apply_server_side_encryption_by_default" {
      for_each = var.use_kms ? [1] : []
      content {
        sse_algorithm     = "aws:kms"
        kms_master_key_id = var.kms_key_arn
      }
    }
    dynamic "apply_server_side_encryption_by_default" {
      for_each = var.use_kms ? [] : [1]
      content { sse_algorithm = "AES256" }
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    id     = "cloudtrail-retention"
    status = "Enabled"
    filter { prefix = "" }
    transition {
      days          = var.transition_days
      storage_class = "INTELLIGENT_TIERING"
    }
    expiration {
      days = var.expire_days
    }
  }
}

# bucket policy (no ACL condition; owner-enforced)
data "aws_iam_policy_document" "bucket" {
  statement {
    sid     = "AWSCloudTrailAclCheck20131101"
    effect  = "Allow"
    actions = ["s3:GetBucketAcl"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    resources = [aws_s3_bucket.this.arn]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = [var.trail_arn]
    }
  }

  statement {
    sid     = "AWSCloudTrailWrite20131101"
    effect  = "Allow"
    actions = ["s3:PutObject"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    resources = [
      "${aws_s3_bucket.this.arn}/AWSLogs/${var.mgmt_account_id}/*",
      "${aws_s3_bucket.this.arn}/o-${var.org_id}/AWSLogs/*",
      "${aws_s3_bucket.this.arn}/AWSLogs/o-${var.org_id}/*",
    ]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = [var.trail_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "this" {
  bucket = aws_s3_bucket.this.id
  policy = data.aws_iam_policy_document.bucket.json
}
