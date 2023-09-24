resource "aws_cloudtrail" "debug-trail" {
  name                          = "debug-trail"
  s3_bucket_name                = aws_s3_bucket.cloud-trail-bucket.id
  s3_key_prefix                 = "prefix"
  include_global_service_events = true
  is_multi_region_trail = true

   advanced_event_selector {
    name = "Log all S3 objects events except cloud trail logs bucket"

    field_selector {
      field  = "eventCategory"
      equals = ["Data"]
    }

    field_selector {
      field = "resources.ARN"

      not_starts_with = [
         aws_s3_bucket.cloud-trail-bucket.arn
       ]
    }

    field_selector {
      field  = "resources.type"
      equals = ["AWS::S3::Object"]
    }
  }

  advanced_event_selector {
    name = "Log readOnly and writeOnly management events"

    field_selector {
      field  = "eventCategory"
      equals = ["Management"]
    }
  }
}



resource "aws_s3_bucket" "cloud-trail-bucket" {
  bucket        = "cloud-trail-bucket-${random_uuid.uuid.result}"
  force_destroy = true
}

resource "random_uuid" "uuid" {}

data "aws_iam_policy_document" "cloud-trail-bucket-policy" {
  statement {
    sid    = "AWSCloudTrailAclCheck"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }

    actions   = ["s3:GetBucketAcl"]
    resources = [aws_s3_bucket.cloud-trail-bucket.arn]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = ["arn:${data.aws_partition.current.partition}:cloudtrail:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:trail/debug-trail"]
    }
  }

  statement {
    sid    = "AWSCloudTrailWrite"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }

    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.cloud-trail-bucket.arn}/prefix/AWSLogs/${data.aws_caller_identity.current.account_id}/*"]

    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = ["arn:${data.aws_partition.current.partition}:cloudtrail:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:trail/debug-trail"]
    }
  }
}
resource "aws_s3_bucket_policy" "cloud-trail-bucket-policy-attachment" {
  bucket = aws_s3_bucket.cloud-trail-bucket.id
  policy = data.aws_iam_policy_document.cloud-trail-bucket-policy.json
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

data "aws_region" "current" {}


provider "aws" {
  region                 = "us-east-1"
  skip_region_validation = false

  default_tags {
    tags = {
      Project              = "CloudTrailDebugStuff"
      ManagedWithTerraform = true
    }
  }

}

