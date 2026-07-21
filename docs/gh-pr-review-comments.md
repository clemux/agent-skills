# gh-pr-review-comments

Historical `gh` CLI guidance for retrieving and replying to inline pull-request review comments.
It is retained for reference, not recommended for use.

## Status

Historical; not recommended. `install.conf.sample` maps it to no harness root:

```
gh-pr-review-comments   none
```

It is installed nowhere by default. The working-directory detection, GraphQL pagination pattern,
and REST reply call are retained for reference; the skill also records why the hand-rolled
workflow was replaced by an official one.

## Why it was retired

For Codex, [README](../README.md) points to the official `gh-address-comments` replacement. Once
that maintained implementation existed, a parallel local version was unnecessary. Other harnesses
never received a supported default; see [Known risks](#known-risks) before enabling it.

## The three retained helpers

Source: [`../gh-pr-review-comments/SKILL.md`](../gh-pr-review-comments/SKILL.md) and the scripts
alongside it.

| Script | Transport | Purpose |
|---|---|---|
| `list-review-comments.sh <owner/repo> <pr_number>` | GraphQL (`gh api graphql --paginate`) | Full detail of unresolved inline review comments |
| `list-review-comment-ids.sh <owner/repo> <pr_number>` | GraphQL (`gh api graphql --paginate`) | Compact `id\|path\|line\|author` listing for scripting |
| `reply-to-comment.sh <owner/repo> <pr_number> <comment_id> "<body>"` | REST (`gh api repos/.../pulls/.../comments/.../replies`) | Post a threaded reply to one review comment |

**Working directory / arguments**: all scripts accept `owner/repo` first. The listing scripts also
accept only `<pr_number>`, then use `gh repo view --json nameWithOwner` to infer `owner/repo` from
the current directory. That requires a Git repository with a GitHub remote that `gh` can resolve.
`reply-to-comment.sh` always requires explicit `owner/repo`.

**GraphQL behavior** (both listing scripts run the same query): they page through
`reviewThreads(first: 100, after: $endCursor)` at the top level using `gh api graphql --paginate`,
so the number of *threads* fetched is not capped. Within each thread, though, the query requests
`comments(first: 100)` with no cursor handling, so a thread with more than 100 comments is
silently truncated. Both scripts filter threads with `select(.isResolved | not)`, then emit
**every** comment in those threads; filtering is at thread level, not per-comment.

**REST behavior** (`reply-to-comment.sh`): posts to the review-comment replies endpoint, which
creates a comment in the same thread. It does not resolve or unresolve threads, so a reply leaves
the thread state unchanged.

## Known risks

- **Replying does not resolve a thread.** A caller that treats "reply posted" as "thread closed"
  will leave stale unresolved threads that `list-review-comments.sh` keeps re-surfacing.
- **Nested comments are capped at 100 and not paginated.** On a thread with unusually long
  back-and-forth, comments past the 100th are silently missing from both listing scripts' output.
- **Listings include all comments in an unresolved thread.** Repeated runs re-emit comments already
  replied to; downstream tooling must de-duplicate.
- **`reply-to-comment.sh` is a remote, human-facing write.** It posts a real comment visible to
  the PR's participants immediately, with no dry-run mode and no undo. Any agent invocation of it
  requires the same explicit-approval treatment as other user-facing outbound writes; it is not
  safe to run unattended as part of an automated loop.
- **No test coverage or CI check exercises these scripts.** Behavior against a live PR has not
  been independently confirmed since retirement.

## Migration / replacement

- **Codex users**: use the official `gh-address-comments` skill (the replacement recorded in this
  repository's README; confirm it is still current). It is maintained upstream.
- **Other harnesses**: there is no maintained default in this repo. A safe replacement would need,
  at minimum: cursor-based pagination on the nested `comments` connection (not just the top-level
  `reviewThreads` connection), a way to resolve a thread after a reply so re-listing does not
  re-surface addressed comments, and an explicit per-comment "already replied" filter instead of
  the current thread-level `isResolved` filter. Until then, re-enabling it reintroduces these
  problems.

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

Never validated against a live PR; this page is derived from the scripts and `SKILL.md`. `gh api`
response-shape claims reflect GitHub as of 2026-07-21 and may change.

## See also

- [skills.md](skills.md) — full skill catalog and installation mapping.
- [`../gh-pr-review-comments/SKILL.md`](../gh-pr-review-comments/SKILL.md) — the skill source this
  page describes.
- [`../install.conf.sample`](../install.conf.sample) — authoritative default harness mapping.
