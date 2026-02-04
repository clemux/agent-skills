---
name: gh-pr-review-comments
description: Use when addressing PR review feedback, viewing inline code comments, or replying to reviewer comments on GitHub pull requests. Triggers on "review comments", "address feedback", "PR comments", "code review".
---

# GitHub PR Review Comments

## Overview

Retrieve and reply to inline code review comments on GitHub PRs using the `gh` CLI. PR comments (general discussion) and review comments (on specific code lines) use different API endpoints.

## Quick Reference

| Task | Command |
|------|---------|
| View PR info | `gh pr view` |
| View general comments | `gh pr view --comments` |
| List inline review comments | `./list-review-comments.sh owner/repo 49` |
| List comment IDs (compact) | `./list-review-comment-ids.sh owner/repo 49` |
| Reply to review comment | `./reply-to-comment.sh owner/repo 49 123456 "Fixed."` |

## Scripts

### list-review-comments.sh

List all inline code review comments with full details.

```bash
./list-review-comments.sh <owner/repo> <pr_number>

# If in a git repo, owner/repo can be auto-detected:
./list-review-comments.sh <pr_number>
```

### list-review-comment-ids.sh

List comment IDs in compact format for scripting (output: `id|path|line|author`).

```bash
./list-review-comment-ids.sh <owner/repo> <pr_number>
```

### reply-to-comment.sh

Reply to an inline review comment in its thread.

```bash
./reply-to-comment.sh <owner/repo> <pr_number> <comment_id> "<body>"
```

## Retrieving Review Comments

**General PR comments** (discussion thread):
```bash
gh pr view --comments
```

**Inline code review comments** (on specific lines):
```bash
./list-review-comments.sh owner/repo 49
```

**Get comment IDs for replies**:
```bash
./list-review-comment-ids.sh owner/repo 49
```

## Evaluating Review Comments

Before acting on comments, read the referenced file and surrounding code. Assess each comment:

| Classification | Meaning |
|----------------|---------|
| **Valid and actionable** | Reviewer is right — make the change |
| **Partially valid** | Concern is real but suggested fix isn't ideal |
| **Disagree** | Current code is correct/better as-is |
| **Needs clarification** | Comment is ambiguous or requires more info |

Consider: Is the concern well-founded? Does the suggestion introduce regressions or break conventions? Is it a style preference vs. a substantive issue?

Present your assessment to the user and get confirmation before making changes.

## Replying to Review Comments

Reply in the comment thread (not as top-level PR comment):

```bash
# When the comment was addressed:
./reply-to-comment.sh owner/repo 49 123456 "Fixed in <commit_hash>."

# When you disagree or skip:
./reply-to-comment.sh owner/repo 49 123456 "Keeping as-is: <brief reason>"
```

**Capture commit hash** for reply messages: `git rev-parse --short HEAD`

**Key fields in response**: `id`, `path`, `line`, `original_line`, `body`, `user.login`, `in_reply_to_id`

## Workflow Example

```bash
# 1. Get PR number
gh pr view --json number -q .number

# 2. List review comments
./list-review-comments.sh owner/repo 49

# 3. Evaluate each comment (read code, assess validity, confirm with user)

# 4. Group related comments by file/topic and fix in single commits
#    Stage only affected files: git add <specific files>

# 5. Reply to each comment
./reply-to-comment.sh owner/repo 49 123456 "Fixed in $(git rev-parse --short HEAD)."
./reply-to-comment.sh owner/repo 49 789012 "Keeping as-is: already handled by upstream validation."

# 6. Print summary
```

### Summary Table

After addressing all comments, print a summary:

| Comment | File:Line | Action | Commit |
|---------|-----------|--------|--------|
| "Use optional chaining" | src/Foo.vue:42 | Fixed | abc123 |
| "Add null check" | src/Bar.vue:17 | Fixed | abc123 |
| "Rename variable" | src/Baz.vue:8 | Disagreed | - |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `gh pr comment` for replies | Use `reply-to-comment.sh` for threaded replies |
| Missing `line` field (null) | Scripts handle this with `original_line` fallback |
| Confusing PR comments vs review comments | PR comments = `gh pr view --comments`, Review comments = scripts |

## Safety Rules

- **Never blindly apply suggestions.** Always read the code and evaluate whether a change is correct.
- **Group related comments** into single commits; don't create one commit per comment when they touch the same file or concern.
- **Do not push** — only commit locally. The user will push when ready.
- **Do not amend** existing commits. Always create new commits.
- **Verify changes** (run lint/tests) after each change to catch issues early.
