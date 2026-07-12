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
| List unresolved inline review comments | `./list-review-comments.sh owner/repo 49` |
| List unresolved comment IDs (compact) | `./list-review-comment-ids.sh owner/repo 49` |
| Reply to review comment | `./reply-to-comment.sh owner/repo 49 123456 "Fixed."` |

## Scripts

### list-review-comments.sh

List unresolved inline code review comments with full details. Resolved review threads are ignored.

```bash
./list-review-comments.sh <owner/repo> <pr_number>

# If in a git repo, owner/repo can be auto-detected:
./list-review-comments.sh <pr_number>
```

### list-review-comment-ids.sh

List unresolved comment IDs in compact format for scripting (output: `id|path|line|author`). Resolved review threads are ignored.

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

**Unresolved inline code review comments** (on specific lines):
```bash
./list-review-comments.sh owner/repo 49
```

**Get unresolved comment IDs for replies**:
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

## Commit Practices

**CRITICAL**: Make atomic commits with explicit, descriptive commit messages.

**Commit immediately after each change** to avoid difficulties in separating changes later:
1. Make ONE logical change (e.g., add validation, fix schema, update types)
2. Run tests and style checks for that change
3. Commit immediately with an explicit message
4. Move to the next change

This workflow prevents the situation where multiple changes get mixed together and are hard to separate into atomic commits.

- **One logical change per commit** - Each commit should represent a single, complete change
- **Explicit commit messages** - Describe WHAT was changed and WHY (not "address feedback" or "fix review comments")
- **Follow project conventions** - Use the project's commit message format (e.g., Conventional Commits)
- **Separate concerns** - If review comments address different issues, make separate commits:
  - Validation logic fix → separate commit
  - Database schema change → separate commit
  - Type changes → separate commit
  - Refactoring → separate commit

**Good commit messages:**
- `fix(repository): require owner_id for sowing status changes`
- `feat(db): add CASCADE delete for sowing status changes`
- `refactor: extract validation logic to separate function`

**Bad commit messages:**
- `address feedback`
- `fix review comments`
- `apply suggestions`

## Workflow Example

```bash
# 1. Get PR number
gh pr view --json number -q .number

# 2. List unresolved review comments
./list-review-comments.sh owner/repo 49

# 3. Evaluate each comment (read code, assess validity, confirm with user)

# 4. For EACH review comment (one at a time):
#    a. Write/update test to reproduce the issue (should fail)
#    b. Make the fix to make the test pass
#    c. Run tests and style checks to verify
#    d. Stage affected files (code + tests): git add <specific files>
#    e. Commit immediately with explicit message describing THIS change
#    f. Capture the commit hash: HASH=$(git rev-parse --short HEAD)
#    g. Reply to the comment: ./reply-to-comment.sh owner/repo 49 123456 "Fixed in $HASH."
#
# This ensures each change stays atomic and is easy to track

# 5. Print summary
```

### Test Coverage

For each change, explicitly document test coverage in the summary:

**TDD Approach (preferred - test first):**
1. Write a test that reproduces the issue (it should fail)
2. Make the fix to make the test pass
3. The git diff should show BOTH test changes and fix changes in the same commit
4. Mention in summary: "Test added (TDD)", "Test updated (TDD)"

**Existing test coverage:**
- If existing tests already cover the change adequately
- Run tests to verify the fix doesn't break anything
- Mention in summary: "Covered by existing tests"

**Manual testing** (when automated tests aren't practical):
- Provide justification for manual testing instead of automated tests
- Examples of valid justifications:
  - Pure UI/visual changes that require human judgment
  - Changes to external integrations without test environments
  - Temporary fixes or experiments
- Mention in summary: "Manual (UI-only change)", "Manual (no test environment)", with justification

**Never skip testing entirely** - every change needs verification, whether automated or manual.

### Summary Table

After addressing all comments, print a summary:

| Comment | File:Line | Action | Commit | Test |
|---------|-----------|--------|--------|------|
| "Use optional chaining" | src/Foo.vue:42 | Fixed | abc123 | Test added (TDD) |
| "Add null check" | src/Bar.vue:17 | Fixed | def456 | Test updated (TDD) |
| "Rename variable" | src/Baz.vue:8 | Disagreed | - | N/A |
| "Handle edge case" | src/Qux.vue:99 | Fixed | 789abc | Covered by existing tests |
| "Fix button color" | src/Btn.vue:12 | Fixed | fedcba | Manual (UI-only change) |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `gh pr comment` for replies | Use `reply-to-comment.sh` for threaded replies |
| Missing `line` field (null) | Scripts handle this with `original_line` fallback |
| Confusing PR comments vs review comments | PR comments = `gh pr view --comments`, Review comments = scripts |

## Safety Rules

- **Never blindly apply suggestions.** Always read the code and evaluate whether a change is correct.
- **Make atomic commits.** Each commit should be one logical change with an explicit, descriptive message. Never use generic messages like "address feedback".
- **Do not push** — only commit locally. The user will push when ready.
- **Do not amend** existing commits. Always create new commits.
- **Verify changes** (run lint/tests) after each change to catch issues early.
