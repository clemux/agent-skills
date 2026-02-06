---
name: S3 Troubleshooting
description: This skill should be used when the user asks to "debug S3 uploads", "fix S3 access denied", "troubleshoot S3 presigned POST", "investigate S3 403 error", "design S3 upload flow", "configure S3 bucket policy", or when working with S3-compatible object storage (AWS S3, Scaleway, MinIO) and encountering permission, policy, or presigned URL issues.
---

# S3 Troubleshooting

Guidance for debugging and avoiding common issues with S3-compatible object storage, including AWS S3, Scaleway Object Storage, and MinIO.

## When to Use

- Investigating S3 upload/download failures (403, AccessDenied, SignatureDoesNotMatch)
- Designing presigned POST/PUT upload flows
- Configuring bucket policies or IAM policies for S3 access
- Debugging differences between S3-compatible providers (AWS vs Scaleway vs MinIO)

## Quick Diagnostic Checklist

When facing S3 access issues, check in this order:

1. **Bucket policy resources** — Verify both bucket and object resources are listed
2. **IAM policy propagation** — Wait 30-60s after policy changes
3. **Presigned POST conditions** — Check for duplicate conditions
4. **CORS configuration** — Distinguish browser CORS errors from server-side 403s
5. **Endpoint URL mismatches** — Signing endpoint must match upload endpoint

## Common Pitfalls

### 1. Missing Wildcard Resource in Bucket Policy

S3 bucket policies require **two resource entries**: one for the bucket itself and one for objects within it. A policy granting access only to the bucket resource silently denies all object operations (PutObject, GetObject, DeleteObject).

**Broken:**
```json
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "my-bucket"
}
```

**Fixed:**
```json
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": ["my-bucket", "my-bucket/*"]
}
```

Without the `/*` wildcard entry, bucket-level operations (ListBucket) succeed but object-level operations (PutObject, GetObject) return `AccessDenied`.

For detailed patterns, see **`references/bucket-policy-patterns.md`**.

### 2. Duplicate Conditions in Presigned POST

`boto3.generate_presigned_post()` automatically adds `bucket` and `key` conditions based on the `Bucket` and `Key` parameters. Manually adding these same conditions causes duplicates in the policy document.

- AWS S3 tolerates duplicate conditions silently
- Scaleway and other S3-compatible providers may reject them with `AccessDenied`

**Broken:**
```python
conditions = [
    {"bucket": bucket_name},      # duplicate — boto3 adds this
    {"key": remote_key},          # duplicate — boto3 adds this
    {"Content-Type": mime_type},
    ["content-length-range", 1, max_size],
]
response = client.generate_presigned_post(
    Bucket=bucket_name,  # boto3 auto-adds bucket condition
    Key=remote_key,      # boto3 auto-adds key condition
    Conditions=conditions,
)
```

**Fixed:**
```python
conditions = [
    {"Content-Type": mime_type},
    ["content-length-range", 1, max_size],
]
response = client.generate_presigned_post(
    Bucket=bucket_name,
    Key=remote_key,
    Conditions=conditions,
)
```

**Note on Fields vs Conditions:** `boto3` does NOT auto-add conditions for items in the `Fields` parameter, nor does it auto-add fields for items in `Conditions`. Only `Bucket` and `Key` get auto-added to conditions.

### 3. Provider-Specific Behavior Differences

S3-compatible providers do not behave identically. When something works on one provider (e.g., MinIO locally) but fails on another (e.g., Scaleway in production):

- Decode the base64 policy document from the presigned POST response to inspect actual conditions
- Test with direct `aws s3 cp` before testing presigned URLs to isolate policy vs signature issues
- Check provider-specific documentation for known differences

## Debugging Workflow

### Step 1: Isolate the Layer

Determine whether the issue is in IAM/bucket policy, presigned signature, or client-side:

```bash
# Test direct upload (bypasses presigned logic)
echo "test" | aws s3 cp - s3://BUCKET/test.txt \
  --endpoint-url ENDPOINT --region REGION

# If direct upload fails → IAM or bucket policy issue (go to Step 2)
# If direct upload works but presigned fails → signature/policy issue (go to Step 3)
```

### Step 2: Check Policies

```bash
# Inspect bucket policy
aws s3api get-bucket-policy --bucket BUCKET \
  --endpoint-url ENDPOINT

# Verify both bucket AND object resources are present
# Look for: "Resource": ["bucket-name", "bucket-name/*"]
```

### Step 3: Inspect Presigned POST Policy

Decode the base64 policy from the presigned POST response:

```bash
echo 'BASE64_POLICY' | base64 -d | python3 -m json.tool
```

Check for:
- Duplicate `bucket` or `key` conditions
- Correct expiration timestamp
- Matching credential region

### Step 4: Test Upload

```bash
# Test presigned POST with curl (file field must be LAST)
curl -X POST 'PRESIGNED_URL' \
  -F 'Content-Type=image/jpeg' \
  -F 'key=REMOTE_KEY' \
  -F 'x-amz-algorithm=AWS4-HMAC-SHA256' \
  -F 'x-amz-credential=...' \
  -F 'x-amz-date=...' \
  -F 'policy=...' \
  -F 'x-amz-signature=...' \
  -F 'file=@test.jpg'
```

## Additional Resources

### Reference Files

- **`references/bucket-policy-patterns.md`** — Correct bucket policy patterns for common S3-compatible providers
