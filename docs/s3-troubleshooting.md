# s3-troubleshooting

`s3-troubleshooting` was guidance for debugging S3-compatible object storage (AWS S3, Scaleway
Object Storage, MinIO), including bucket-policy resources, presigned POST/PUT conditions, and
isolating IAM/policy from signature issues. It is historical, not recommended guidance.

## Status

Historical; not recommended. `install.conf.sample` maps it to no harness:

```
s3-troubleshooting      none
```

[`README.md`](../README.md) flags it: "**Historical; not recommended. May contain incorrect or
unsafe instructions.**" Its presence and past review do not validate its instructions. Its broad
`SKILL.md` trigger phrases can look active, but it must not be re-enabled or recommended without a
full rewrite using current provider documentation.

## Why it was retired

The package contains `SKILL.md` and `references/bucket-policy-patterns.md`, with no scripts or
tests. Repository evidence does not show any command or policy verified against a real bucket.
Several examples are unsafe to run as-is.

## Known risks

Re-enabling or copying these examples as-is reproduces unsafe patterns:

- **`Action: "*"` in bucket policies.** The skill's own "fixed" example for the missing-resource
  pitfall still grants `"Action": "*"` — it corrects the `Resource` field but never narrows the
  action from a full-access wildcard to the specific S3 actions actually needed.
- **Wildcard principals.** The MinIO bucket-policy pattern in
  `references/bucket-policy-patterns.md` uses `"Principal": {"AWS": ["*"]}`, granting the policy's
  actions to any principal, not a scoped role or user.
- **Direct upload to a fixed object key.** The "isolate the layer" diagnostic step uploads
  arbitrary test content to a hardcoded key (`s3://BUCKET/test.txt`) with no guidance to use a
  disposable, uniquely-named test object, risking collision with or overwrite of a real object at
  that key.
- **Live bucket-policy replacement.** The "apply a new policy" pattern runs
  `aws s3api put-bucket-policy` directly against a target bucket, with no backup of the existing
  policy, no simulation/dry-run step, and no approval gate before the mutation takes effect.
- **Ambient credential use.** Every AWS CLI invocation in the skill (`aws s3 cp`, `aws s3api
  get-bucket-policy`, `aws s3api put-bucket-policy`) relies on whatever credentials are already
  configured in the environment. There is no instruction to scope down to a dedicated test
  principal or temporary credentials before running mutating commands.
- **Possible credential/signature leakage in logged output.** The presigned-POST debugging steps
  have the caller decode and print the full policy document, and the example `curl` invocation
  echoes `x-amz-credential`, `x-amz-date`, `policy`, and `x-amz-signature` fields in full on the
  command line — all of which could end up in shell history or terminal logs if handled with real
  values instead of placeholders.

Other claims may drift with provider changes: IAM/bucket-policy propagation delay ("30-60s"),
provider endpoint/signing-region rules, and whether the `file` field must be last in a multipart
presigned POST body. Check current provider documentation.

## Migration / replacement

There is no maintained replacement skill; check [skills.md](skills.md) for the current inventory.
A replacement needs at least:

- Guidance sourced from current provider documentation at time of use, not copied from this skill,
  since propagation times, endpoint rules, and multipart field-order requirements are
  version/configuration dependent and provider-specific.
- Least-privilege policy examples — no `Action: "*"` and no wildcard `Principal` in any worked
  example, replaced with the minimal action set and a scoped principal.
- Disposable, uniquely-named test objects/keys for diagnostic uploads instead of a fixed path, so a
  debugging session cannot collide with real data.
- A backup-and-simulate step before any live bucket-policy replacement (capture the existing
  policy, dry-run or simulate the new one) plus an explicit approval gate before applying a
  mutating change.
- Explicit use of scoped or temporary credentials for diagnostic and test operations rather than
  ambient/default credentials.
- Redaction of signing material (credentials, signatures, full policy documents) in anything the
  workflow prints or logs, and bounded/placeholder values in any signed-field examples.
- A cleanup step that removes test objects and reverts any policy changes made for diagnostic
  purposes.

## Verification status

Never validated. It has no scripts or tests, and the repository does not show its commands or
policies run against AWS S3, Scaleway, or MinIO. Treat commands, policy JSON, and timing claims as
unverified until checked against current provider documentation.

## Example (illustrative only)

This constructed Step 1 illustration is not a captured session; values are placeholders:

```text
$ echo "test" | aws s3 cp - s3://<bucket>/test.txt --endpoint-url <endpoint> --region <region>
upload failed: - to s3://<bucket>/test.txt An error occurred (AccessDenied) ...
```

It illustrates an `AccessDenied` failure the workflow was meant to diagnose; the output does not
establish the root cause. See "Known risks" before running the command against a real bucket.
