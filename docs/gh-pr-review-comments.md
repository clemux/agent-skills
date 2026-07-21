# gh-pr-review-comments

Retrieves and replies to inline code-review comments on GitHub pull requests using the `gh` CLI.
This page documents it as a historical skill: read it to understand what is retained in the repo
and why, not as a recommendation to enable it.

## Status

Historical; not recommended. `install.conf.sample` maps it to no harness root:

```
gh-pr-review-comments   none
```

That means it is installed nowhere by default — no symlink is created into any Claude Code,
Codex, or neutral `~/.agents/skills` root, and no agent picks it up automatically. It is kept in
the repository only as prior art (the working-directory detection, the GraphQL pagination
pattern, and the REST reply call are each individually correct and may be worth reusing) and as a
record of why a hand-rolled review-reply workflow was superseded by an official one.

## Why it was retired

For Codex, the repository [README](../README.md) points users to the official
`gh-address-comments` skill as the replacement covering the same ground — see
[Migration](#migration--replacement) below. Once an official, maintained
implementation existed for that harness, keeping a parallel hand-rolled version in this repo
added duplicate maintenance surface for no benefit on that harness. For other harnesses, the
skill was never promoted to a supported default; see [Known risks](#known-risks) for the
behavioral gaps that would need closing before it should be.

## The three retained helpers

Source: [`../gh-pr-review-comments/SKILL.md`](../gh-pr-review-comments/SKILL.md) and the scripts
alongside it.

| Script | Transport | Purpose |
|---|---|---|
| `list-review-comments.sh <owner/repo> <pr_number>` | GraphQL (`gh api graphql --paginate`) | Full detail of unresolved inline review comments |
| `list-review-comment-ids.sh <owner/repo> <pr_number>` | GraphQL (`gh api graphql --paginate`) | Compact `id\|path\|line\|author` listing for scripting |
| `reply-to-comment.sh <owner/repo> <pr_number> <comment_id> "<body>"` | REST (`gh api repos/.../pulls/.../comments/.../replies`) | Post a threaded reply to one review comment |

**Working directory / argument assumptions**: all three scripts accept `owner/repo` as an
explicit first argument. The two listing scripts also accept a bare `<pr_number>` as their only
argument, in which case they shell out to `gh repo view --json nameWithOwner` to infer
`owner/repo` from the current directory — this only works when the working directory is inside a
git repository with a GitHub remote `gh` can resolve. `reply-to-comment.sh` has no such fallback;
`owner/repo` is always required as an explicit argument.

**GraphQL behavior** (both listing scripts run the same query): they page through
`reviewThreads(first: 100, after: $endCursor)` at the top level using `gh api graphql --paginate`,
so the number of *threads* fetched is not capped. Within each thread, though, the query requests
`comments(first: 100)` with no cursor handling — that inner connection is not paginated, so a
thread with more than 100 comments will silently be truncated to its first 100. Both scripts
filter with `select(.isResolved | not)` on the thread, then emit **every** comment in that thread,
including ones that individually might already read as addressed — the filter operates on
thread-level resolution, not per-comment.

**REST behavior** (`reply-to-comment.sh`): posts to the review-comment replies endpoint, which
creates a new comment in the same thread. It does not call any resolve/unresolve endpoint, so a
successful reply leaves the thread's resolved state unchanged.

## Known risks

- **Replying does not resolve a thread.** A caller that treats "reply posted" as "thread closed"
  will leave stale unresolved threads that `list-review-comments.sh` keeps re-surfacing.
- **Nested comments are capped at 100 and not paginated.** On a thread with unusually long
  back-and-forth, comments past the 100th are silently missing from both listing scripts' output.
- **Listings include all comments in an unresolved thread**, not just the ones a caller hasn't
  seen or acted on — repeated runs will re-emit comments already replied to, and downstream
  tooling must de-duplicate itself.
- **`reply-to-comment.sh` is a remote, human-facing write.** It posts a real comment visible to
  the PR's participants immediately, with no dry-run mode and no undo. Any agent invocation of it
  requires the same explicit-approval treatment as other user-facing outbound writes; it is not
  safe to run unattended as part of an automated loop.
- **No test coverage or CI check exercises these scripts** (see
  [Verification status](#verification-status)) — behavior against a live PR has not been
  independently confirmed since the skill was retired.

## Migration / replacement

- **Codex users**: use the official `gh-address-comments` skill instead of this one (the
  recommendation recorded in this repository's README; confirm it is still the current official
  replacement). It is maintained upstream rather than in this repository, so it does not carry the
  drift risk noted above.
- **Other harnesses**: there is no maintained default in this repo. A safe replacement would need,
  at minimum: cursor-based pagination on the nested `comments` connection (not just the top-level
  `reviewThreads` connection), a way to resolve a thread after a reply so re-listing does not
  re-surface addressed comments, and an explicit per-comment "already replied" filter instead of
  the current thread-level `isResolved` filter. Until those are addressed, treat re-enabling this
  skill as-is as reintroducing the problems above, not as restoring a working tool.

## Example

Illustrative only — placeholders stand in for a real repository, PR, and comment:

```bash
# List unresolved inline review comments (owner/repo inferred from the current git repo)
./list-review-comments.sh 49

# Get compact id|path|line|author rows for scripting
./list-review-comment-ids.sh owner/repo 49

# Reply in a specific comment's thread (does not resolve it)
./reply-to-comment.sh owner/repo 49 123456 "Fixed in <commit_hash>."
```

## Verification status

Never validated against a live PR as part of documenting this page — the behavior above is
derived from reading the scripts and `SKILL.md`, not from an observed run. Treat any claim about
`gh api` response shapes as tied to the GitHub API as of 2026-07-21; GitHub can change field
availability or pagination limits without notice.

## See also

- [skills.md](skills.md) — full skill catalog and installation mapping.
- [`../gh-pr-review-comments/SKILL.md`](../gh-pr-review-comments/SKILL.md) — the skill source this
  page describes.
- [`../install.conf.sample`](../install.conf.sample) — authoritative default harness mapping.
