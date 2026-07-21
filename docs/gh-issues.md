# gh-issues

GitHub issue management with the `gh` CLI: listing, viewing, creating, editing, closing, and
reopening issues. The skill is one `SKILL.md` with command patterns; it has no scripts, references,
or agents.

## Status

Active.

Default harness mapping, from [`install.conf.sample`](../install.conf.sample):

```
gh-issues               claude
```

Claude-only by default. A machine's local `install.conf` can override that mapping.

The frontmatter `description` is the sole trigger mechanism (per [`AGENTS.md`](../AGENTS.md)). It
matches phrases such as "show open issues", "view issue 456", "create an issue", "file a bug",
"close issue", and "add label to issue".

## Triggers

Per the `description` frontmatter in
[`gh-issues/SKILL.md`](../gh-issues/SKILL.md):

- Listing issues — e.g. "show open issues"
- Viewing issue details — e.g. "view issue 456"
- Creating issues — e.g. "create an issue", "file a bug"
- Editing or closing issues — e.g. "close issue", "add label to issue"

## Prerequisites

- The `gh` CLI installed and authenticated. The skill documents checking this with:

  ```bash
  gh auth status
  ```
- Network access to GitHub.
- No dependency on other skills in this repository.

## Read/write and safety boundaries

- **Read-only operations** — `gh issue list` and `gh issue view` — query GitHub without mutation.
- **Write operations** — `gh issue create`, `gh issue edit`, `gh issue close`, `gh issue reopen` —
  are external, human-facing mutations against a real GitHub repository: they create issues,
  change titles/labels/assignees, or change issue state, all visible to anyone with access to that
  repository. The skill file itself contains no built-in confirmation step or target check; the
  agent invoking these commands is responsible for confirming both the exact repository the
  command will hit and the payload (title, body, labels, assignees, close reason) before a write.
  `gh issue` uses the repository inferred from the current directory or `-R owner/repo`.
- **Repository-target selection matters.** The documented commands do not use `-R`/`--repo`; every
  example relies on `gh`'s ambient repository resolution (current git remote). A wrong working
  directory can silently target the wrong repository.
- **Labels, assignees, and close reasons are repository-specific.** Labels (e.g. `bug`,
  `enhancement`, `needs-review`) and close reasons (e.g. `"not planned"`) must already exist or be
  valid for the target repository; the skill does not enumerate or validate them.
- **No dry run.** `gh issue create`, `edit`, `close`, and `reopen` all mutate GitHub state
  immediately on execution; there is no preview or `--dry-run` flag documented or used.

## Typical workflow

1. User asks to see or inspect issues ("show open issues", "view issue 456").
2. Agent runs the corresponding read-only `gh issue list` or `gh issue view` command and reports
   results.
3. If the user asks for a mutation (create/edit/close/reopen), the agent confirms the target
   repository and the exact payload, then runs the corresponding `gh issue` write command.
4. Agent reports the result (e.g. the new issue URL, or confirmation of the state change).

## Bundled resources

- [`gh-issues/SKILL.md`](../gh-issues/SKILL.md) — the entire skill: prerequisites and a quick
  reference of `gh issue` command patterns for listing, viewing, creating, editing, closing, and
  reopening issues. No `scripts/`, `references/`, or `agents/` subdirectories exist for this
  skill.

## Limitations

- Command patterns only cover single-issue and simple list operations; there is no coverage of
  bulk operations, issue templates, milestones, or projects.
- No explicit repository-targeting example (`-R owner/repo`) is included, so correctness depends
  on the caller's working directory matching the intended repository.
- Invalid labels, assignees, and close reasons surface only as a `gh` error at execution time.
- The skill has no automated tests of its own; it is a static instruction file.

## Compatibility and version notes

- Depends on GitHub CLI (`gh`) being installed and authenticated; command syntax shown
  (`gh issue list/view/create/edit/close/reopen`) matches `gh` CLI usage as of 2026-07-21 and is
  unverified against any specific pinned `gh` version.
- `--reason "not planned"` for `gh issue close` is a GitHub-defined close reason; other valid
  values (e.g. `"completed"`) are not documented in the skill and may vary by repository
  configuration, as of 2026-07-21.

## Verification status

- No automated checks (tests, CI) exercise this skill within the repository; it is not listed with
  any test harness in the sources read.
- Command syntax was cross-checked only against `SKILL.md`; no commands were run against a live
  repository for this page.

## Example

Illustrative only — placeholders, not a captured transcript:

```bash
# Read: list open issues in the current repository
gh issue list --state open

# Read: view one issue's details
gh issue view 123 --json title,body,labels,state

# Write: create an issue (requires explicit confirmation of target repo and payload)
gh issue create --title "<short bug summary>" --body "<repro steps>" --label bug

# Write: close an issue with a reason
gh issue close 123 --reason "not planned"
```
