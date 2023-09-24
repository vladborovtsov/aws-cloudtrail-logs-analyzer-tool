output "cloud_trail_bucket_name" {
  value = aws_s3_bucket.cloud-trail-bucket.bucket
}

output "cloud_trail_bucket_region" {
  value = aws_s3_bucket.cloud-trail-bucket.region
}