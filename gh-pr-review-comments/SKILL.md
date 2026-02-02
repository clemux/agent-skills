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

## Replying to Review Comments

Reply in the comment thread (not as top-level PR comment):

```bash
./reply-to-comment.sh owner/repo 49 123456 "Fixed. Moved to CSS class."
```

**Key fields in response**: `id`, `path`, `line`, `original_line`, `body`, `user.login`, `in_reply_to_id`

## Workflow Example

```bash
# 1. Get PR number
gh pr view --json number

# 2. List review comments
./list-review-comments.sh owner/repo 49

# 3. Reply to each comment
./reply-to-comment.sh owner/repo 49 123456 "Fixed in commit abc123."
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `gh pr comment` for replies | Use `reply-to-comment.sh` for threaded replies |
| Missing `line` field (null) | Scripts handle this with `original_line` fallback |
| Confusing PR comments vs review comments | PR comments = `gh pr view --comments`, Review comments = scripts |
