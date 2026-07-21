# s3-troubleshooting

`s3-troubleshooting` was guidance for debugging S3-compatible object storage (AWS S3, Scaleway
Object Storage, MinIO): bucket-policy resource formats, presigned POST/PUT condition mismatches,
and a step-by-step workflow for isolating IAM/policy issues from signature issues. It is retained
in the repository as a historical record, not as guidance to follow.

## Status

Historical; not recommended. `install.conf.sample` maps it to no harness:

```
s3-troubleshooting      none
```

[README.md](../README.md) already flags it: "**Historical; not recommended. May contain incorrect
or unsafe instructions.**" That warning is correct and should be treated as authoritative. The
skill is kept in the repository only as a record of what was tried, not as a maintained resource —
its presence in the tree is not an endorsement, and its trigger phrases (in `SKILL.md`'s
`description`) are still broad enough to look like active, invokable guidance. **Retention is not
validation.** Nothing about this skill being present, having a plausible-looking checklist, or
having survived past reviews means its instructions are safe to run. It must not be re-enabled or
pointed to as recommended guidance without a full rewrite against current provider documentation.

## Why it was retired

The skill was never backed by scripts or tests — the package is `SKILL.md` plus one reference file
(`references/bucket-policy-patterns.md`), and every command and policy shown is illustrative text
that was, as far as the repository shows, never executed or verified against a real bucket. Several
of its worked examples also demonstrate patterns that are unsafe to run as-is (see below), which
would make them actively harmful advice rather than merely outdated.

## Known risks

If re-enabled or copied out as-is, someone following the examples verbatim would reproduce several
unsafe patterns baked into the skill's own guidance:

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

Beyond these concrete patterns, several of the skill's factual claims are the kind that drift with
provider changes and were not dated or version-qualified when written: IAM/bucket-policy
propagation delay ("30-60s"), which endpoint/signing-region rules apply per provider, and the
claimed requirement that the `file` field be last in a multipart presigned POST body. None of these
should be trusted without checking current provider documentation first.

## Migration / replacement

There is no maintained skill in this repository that replaces `s3-troubleshooting` as of this
writing; check [skills.md](skills.md) for the current inventory before assuming otherwise. A safe
replacement, if one is built, would need at minimum:

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

Never validated. The skill package contains no scripts and no tests, and nothing in the repository
indicates its commands or policy examples were run against a real AWS S3, Scaleway, or MinIO
endpoint. Treat every command, policy JSON, and timing claim on this page and in the skill's own
files as unverified until checked against current provider documentation.

## Example (illustrative only)

The transcript below is a constructed illustration of what following the skill's Step 1 diagnostic
would look like — it is not a captured session, and the values are placeholders:

```text
$ echo "test" | aws s3 cp - s3://<bucket>/test.txt --endpoint-url <endpoint> --region <region>
upload failed: - to s3://<bucket>/test.txt An error occurred (AccessDenied) ...
```

This illustrates the failure mode the skill's checklist was meant to help diagnose (a bucket policy
missing the `bucket-name/*` resource). It does not vouch for the safety of running the underlying
commands against a real bucket; see "Known risks" above before doing so.
