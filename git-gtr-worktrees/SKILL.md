---
name: git-gtr-worktrees
description: Use git-worktree-runner (`git gtr`) to create, enter, launch tools in, inspect, or clean up Git worktrees. Use when a coding task should be isolated in a worktree, when a repo has `.gtrconfig` or an established worktree directory, when coordinating parallel branches or same-branch worktrees, or when debugging `git gtr` worktree setup.
---

# Git GTR Worktrees

Use `git gtr` as the preferred worktree interface when the repository has a `.gtrconfig`, an established worktree directory, or the user explicitly asks to use `git gtr`.

## Portability Rules

Start from the current machine's repo state. Do not assume a specific home directory, global editor, AI command, branch naming convention, or worktree location from another computer.

If `git gtr` is missing or errors before reading repo configuration, report the tool gap and use normal `git worktree` only when the user approves that fallback.

## Inspect The Repo

Before creating, entering, or removing worktrees, inspect the current state:

```bash
git status --short
git gtr list
git gtr config list
```

Read `.gtrconfig` when it exists. Treat its configured worktree directory, copied files, post-create hooks, AI command, and editor command as repo-local facts. Do not assume settings from another repo apply.

## Choose The Base

Choose the base branch deliberately:

- Use `--from-current` when the new worktree should build on the current branch.
- Use `--from main` or the repo's primary branch for an independent feature in repos without an `origin` remote.
- Use the default only when the repo has a healthy `origin/HEAD` or configured default branch that resolves locally.

Use `--no-fetch` when network access is unnecessary or unavailable.

## Create And Enter

Create from the current branch:

```bash
git gtr new feature-name --from-current --no-fetch
cd "$(git gtr go feature-name)"
```

Create from a local primary branch:

```bash
git gtr new feature-name --from main --no-fetch
cd "$(git gtr go feature-name)"
```

If the repo's `.gtrconfig` defines post-create hooks and they were skipped or failed, run only the relevant hook commands for that repo after inspecting them. For example, run `mise trust --yes mise.toml` only when the repo uses `mise.toml` and the hook or local setup expects it.

## Verify Before Editing

After entering a worktree, verify the active checkout before any file edit:

```bash
pwd
git branch --show-current
git rev-parse --show-toplevel
git status --short
```

The reported top-level path and branch must match the intended worktree. If they do not, stop and correct the command working directory before editing.

When using editor-style patch tools or other write helpers, treat their target checkout as unverified until the first small edit proves it. After the first edit, immediately check both the main checkout and the worktree:

```bash
git -C /path/to/main-checkout status --short
git -C "$(git gtr go feature-name)" status --short
```

If the new change appears in the main checkout instead of the worktree, stop immediately and move or revert only that mistaken change before continuing. Do not continue implementing while the edit location is ambiguous.

## Launch Tools

Start the configured AI tool in a worktree:

```bash
git gtr ai feature-name
```

Open the configured editor when one is set:

```bash
git gtr editor feature-name
```

Use `git gtr config list` first when the configured AI or editor command matters. Do not assume the command launches Claude, Codex, or a specific editor unless the current repo config says so.

## Parallel Work

For multiple worktrees on the same branch, use a descriptive suffix:

```bash
git gtr new feature-name --force --name tests --from-current --no-fetch
git gtr ai feature-name-tests
```

Keep same-branch worktrees on non-overlapping files, commit or stash before switching contexts, and inspect `git status --short` before integrating.

## Cleanup

Do not remove a worktree or delete a branch unless the user explicitly asks. When asked, inspect first:

```bash
git gtr list
git status --short
git branch --merged main
```

Then remove the selected worktree:

```bash
git gtr rm feature-name
```

Use `--delete-branch` only when the user explicitly requested branch deletion. In non-interactive tool runs, `git gtr rm feature-name --delete-branch` may still prompt and leave the branch in place. Always verify afterward:

```bash
git gtr list
git branch --list feature-name
```

If the worktree is gone, the branch is listed, and `git branch --merged main` shows it is merged, delete it directly:

```bash
git branch -d feature-name
```

## Troubleshooting

Run:

```bash
git gtr doctor
git gtr config list
```

If worktrees are inside the repo, ensure the configured worktree directory is ignored by Git. For example, if `.gtrconfig` stores worktrees under `.worktrees`, `.worktrees/` should be in `.gitignore`.
