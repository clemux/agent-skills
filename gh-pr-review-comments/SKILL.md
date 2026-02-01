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
| List inline review comments | `gh api repos/{owner}/{repo}/pulls/{pr}/comments` |
| Reply to review comment | `gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies -f body="..."` |

## Retrieving Review Comments

**General PR comments** (discussion thread):
```bash
gh pr view --comments
```

**Inline code review comments** (on specific lines):
```bash
# Get all review comments with key fields
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '.[] | "ID: \(.id)\nFile: \(.path)\nLine: \(.line // .original_line)\nAuthor: \(.user.login)\nBody: \(.body)\n---"'
```

**Get comment IDs for replies**:
```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --jq '.[] | "\(.id)|\(.path)|\(.line // .original_line)|\(.user.login)"'
```

## Replying to Review Comments

Reply in the comment thread (not as top-level PR comment):

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies \
  -f body="Fixed. Moved to CSS class."
```

**Key fields in response**: `id`, `path`, `line`, `original_line`, `body`, `user.login`, `in_reply_to_id`

## Workflow Example

```bash
# 1. Get PR number
gh pr view --json number

# 2. List review comments
gh api repos/owner/repo/pulls/49/comments \
  --jq '.[] | "ID:\(.id) File:\(.path):\(.line) Author:\(.user.login)\n\(.body)\n---"'

# 3. Reply to each comment
gh api repos/owner/repo/pulls/49/comments/123456/replies \
  -f body="Fixed in commit abc123."
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `gh pr comment` for replies | Use `gh api .../comments/{id}/replies` for threaded replies |
| Missing `line` field (null) | Use `original_line` as fallback: `.line // .original_line` |
| Confusing PR comments vs review comments | PR comments = `gh pr view --comments`, Review comments = API endpoint |