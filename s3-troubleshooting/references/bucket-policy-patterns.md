# Bucket Policy Patterns

## Resource Format by Provider

### AWS S3

AWS uses ARN format for resources:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME"},
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::BUCKET_NAME/*"
    },
    {
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME"},
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::BUCKET_NAME"
    }
  ]
}
```

### Scaleway Object Storage

Scaleway uses a simplified resource format (bucket name, not ARN):

```json
{
  "Version": "2023-04-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"SCW": "application_id:APP_ID"},
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"],
      "Resource": ["BUCKET_NAME", "BUCKET_NAME/*"]
    }
  ]
}
```

Key differences from AWS:
- `Principal` uses `SCW` namespace with `application_id:` or `user_id:` prefix
- `Resource` uses bare bucket name, not ARN
- Both bucket and `bucket/*` must be in the same statement or separate statements

### MinIO

MinIO follows AWS-style ARN format:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": ["*"]},
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": ["arn:aws:s3:::BUCKET_NAME/*"]
    }
  ]
}
```

## Common Mistakes

### Mistake: Single Resource Without Wildcard

```json
"Resource": "my-bucket"
```

This grants access to the bucket itself (ListBucket, GetBucketPolicy) but NOT to objects within it. Object operations (PutObject, GetObject, DeleteObject, HeadObject) require the `my-bucket/*` resource.

### Mistake: Only Wildcard Without Bucket

```json
"Resource": "my-bucket/*"
```

This grants access to objects but NOT to the bucket itself. Operations like ListBucket will fail.

### Correct: Both Resources

```json
"Resource": ["my-bucket", "my-bucket/*"]
```

This grants access to both bucket-level and object-level operations.

## Debugging Bucket Policies

### Retrieve Current Policy

```bash
# AWS
aws s3api get-bucket-policy --bucket BUCKET

# Scaleway
aws s3api get-bucket-policy --bucket BUCKET \
  --endpoint-url https://s3.REGION.scw.cloud

# MinIO
aws s3api get-bucket-policy --bucket BUCKET \
  --endpoint-url http://localhost:9000
```

### Apply a New Policy

```bash
# Write policy to file first
cat > /tmp/policy.json << 'EOF'
{
  "Version": "2023-04-17",
  "Statement": [...]
}
EOF

# Apply
aws s3api put-bucket-policy --bucket BUCKET \
  --policy file:///tmp/policy.json \
  --endpoint-url ENDPOINT
```

### Policy Propagation

After applying a new policy, allow 30-60 seconds for propagation before testing. This applies to both bucket policies and IAM policies on all providers.
