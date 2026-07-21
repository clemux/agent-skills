# git-gtr-worktrees

Guidance for using `git-worktree-runner` (the `git gtr` subcommand) as the preferred interface for
creating, entering, launching tools in, inspecting, and cleaning up Git worktrees, with a fallback
to plain `git worktree` when the tool is unavailable or the user prefers it.

## Status

Active. Default harness mapping in [`install.conf.sample`](../install.conf.sample):

```
git-gtr-worktrees       claude codex agents
```

It targets all three roots (Claude Code, Codex, and the neutral `agents` root).

The skill is written as agent-facing operating instructions ("inspect the repo", "choose the
base", "verify before editing") rather than a single command a user types, so it is meant to be
model-triggered during a coding task — when a task should be isolated in a worktree, a repo
already has `.gtrconfig` or a worktree layout, or the user is coordinating parallel or same-branch
work. The bundled `agents/openai.yaml` `default_prompt` ("Use $git-gtr-worktrees to create and
manage a focused worktree for this task") also supports explicit user invocation in interfaces
that support skill mentions.

## Triggers

Per `SKILL.md`, the skill applies when:

- the user explicitly asks to use `git gtr` (stated in the skill body; the remaining cases come
  from the frontmatter description),
- the repository has a `.gtrconfig` file,
- the repository already has an established `git gtr` worktree directory,
- a coding task should be isolated in a worktree,
- the user is coordinating parallel branches or multiple worktrees on the same branch, or
- `git gtr` worktree setup itself needs debugging.

The skill body reiterates a narrower version of the same rule: prefer `git gtr` "when the
repository has a `.gtrconfig`, an established worktree directory, or the user explicitly asks to
use `git gtr`" — it does not repeat the parallel/same-branch or debugging cases in that sentence,
but those are covered later in dedicated sections ("Parallel Work", "Troubleshooting").

## Prerequisites

- **External dependency**: the `git-worktree-runner` tool, invoked as `git gtr` (a Git
  subcommand). The skill does not bundle or install it — if it is missing or errors before
  reading repo configuration, the skill instructs reporting the tool gap and falling back to plain
  `git worktree` only with the user's approval.
- A Git repository (worktree creation and inspection only make sense inside one).
- Optionally, a `.gtrconfig` file in the repo, which can define a default worktree directory,
  copied files, hooks, an AI-launch command, an editor command, a default remote, and a default
  branch.
- For provider-aware cleanup (`git gtr clean --merged --closed`), a provider CLI: `gh` for GitHub
  or `glab` for GitLab. That cleanup path may also fetch from `origin`.

## Read/write and safety boundaries

**Reads / inspects** (no side effects): `git status --short`, `git gtr list`, `git gtr config
list`, `.gtrconfig` contents, `git gtr doctor`, `git branch --merged main`, `git branch --list`.

**Mutates the working tree or repo state**: `git gtr new` (creates a worktree and branch), `git
gtr mv`/`rename` (renames worktree directory and local branch), `git gtr rm` (removes a
worktree), `git branch -d`/`-D` (deletes a branch), `git gtr clean` (prunes worktree metadata,
directories, and — with flags — branches).

**External / human-facing**: launching an AI tool (`git gtr ai`) or editor (`git gtr editor`) in a
worktree runs an externally configured command; the skill instructs not to assume it launches any
specific tool without checking `git gtr config list` first. Trusting `.gtrconfig` hooks or
AI/editor defaults is itself gated (see Safety protocol below).

**Requires explicit user approval before proceeding**:
- falling back to plain `git worktree` when `git gtr` is missing or errors,
- running `git gtr trust` after `.gtrconfig` warns its entries are untrusted,
- removing a worktree or deleting a branch at all ("Do not remove a worktree or delete a branch
  unless the user explicitly asks"),
- using `--force` on `git gtr rm` (removing a dirty worktree or bypassing a failing pre-remove
  hook),
- using `--delete-branch` on `git gtr rm` (branch deletion is explicit-request-only, not
  merged-only-safe),
- running `git gtr clean --merged`/`--closed` for real (non-dry-run) branch/PR cleanup.

## Safety protocol

The skill's core discipline (grouped thematically here; `SKILL.md` opens with the portability
rules, including the fallback listed last below):

1. **Inspect before trusting config/hooks/default commands.** Before creating, entering, or
   removing worktrees, run `git status --short`, `git gtr list`, and `git gtr config list`, and
   read `.gtrconfig` if present. Executable hooks and `.gtrconfig` editor/AI defaults are treated
   as untrusted until `git gtr trust` is run, and that trust step itself requires inspecting the
   commands and asking the user first.
2. **Explicit base selection.** Choose the worktree's base branch deliberately: `--from-current`
   to build on the current branch, `--from main` (or the repo's primary branch) for an
   independent feature, or an explicit `--from <ref>` when remotes are unusual, missing, or the
   inferred default should not be trusted. The documented default-base resolution order is
   `gtr.defaultRemote`/`gtr.defaultBranch` config, then remote HEAD, then remote `main`/`master`,
   then local `main`.
3. **Checkout verification after creation.** After entering a new worktree, verify before any
   edit: `pwd`, `git branch --show-current`, `git rev-parse --show-toplevel`, `git status
   --short`. The reported path and branch must match the intended worktree, or the agent must stop
   and correct the working directory before editing.
4. **Mistaken-edit containment.** When using patch/write tools whose target checkout is not yet
   proven, treat it as unverified until a first small edit confirms it, then check both the main
   checkout and the worktree (`git -C <main> status --short` and `git -C "$(git gtr go <name>)"
   status --short`). If a change lands in the main checkout instead of the worktree, stop
   immediately and move or revert only that mistaken change before continuing — do not keep
   implementing while the edit location is ambiguous.
5. **Same-branch worktree behavior.** For multiple worktrees on the same branch, use
   `git gtr new <name> --force --name <suffix> --from-current --no-fetch` with a descriptive
   suffix, keep same-branch worktrees on non-overlapping files, commit or stash before switching
   contexts, and inspect `git status --short` before integrating changes back.
6. **Fallback to plain `git worktree`.** Only when `git gtr` is missing or errors before reading
   repo configuration, and only with the user's approval for that specific fallback.

## Destructive-action table

| Action | What it destroys | Preview first | Explicit consent gate |
| --- | --- | --- | --- |
| `git gtr rm <name> --yes` | The selected worktree's working directory and its registry entry | `git gtr list`, `git status --short`, `git branch --merged main` | User must explicitly ask to remove the worktree at all |
| `git gtr rm <name> --force --yes` | Same as above, even with uncommitted changes present or a failing pre-remove hook | Same as above, plus confirm the worktree is in fact dirty or the hook is in fact failing | User must accept removing a dirty worktree or bypassing a failing hook |
| `git gtr rm <name> --delete-branch --yes` | The worktree, plus force-deletes the local branch (`git branch -D`, not merged-only-safe) | `git gtr list`, `git branch --list <name>`, `git branch --merged main` (to know if it's actually merged) | User must explicitly request branch deletion, separate from worktree removal |
| `git gtr clean` (plain) | Stale Git worktree metadata/registry entries and empty worktree directories | none specified beyond normal repo inspection | Lower risk (no branches touched), but still a mutation — confirm before running in an unfamiliar repo |
| `git gtr clean --merged --closed` | Branches matching merged/closed-PR criteria; may force-delete those branches; requires `gh`/`glab`; may fetch from `origin` | `git gtr clean --merged --closed --dry-run` | Run dry-run first; only run for real (`--yes`) after reviewing the dry-run matches |

`git branch -d <name>` (plain Git, not `git gtr`) is used only after confirming via `git gtr list`
that the worktree is gone, `git branch --list` shows the branch, and `git branch --merged main`
confirms it is merged — i.e. as the safe manual finish after a non-`--delete-branch` removal.

## Typical workflow

1. Inspect repo state (`git status --short`, `git gtr list`, `git gtr config list`, read
   `.gtrconfig`).
2. Choose a base branch deliberately and create the worktree, e.g.
   `git gtr new feature-name --from-current --no-fetch`.
3. Enter it: `cd "$(git gtr go feature-name)"`.
4. Verify the checkout (`pwd`, `git branch --show-current`, `git rev-parse --show-toplevel`,
   `git status --short`) before making any edit.
5. Optionally launch the configured AI tool (`git gtr ai feature-name`) or editor
   (`git gtr editor feature-name`), after checking `git gtr config list` for what they actually
   run.
6. Use `git gtr run <name> <command>` for one-off checks, or `cd` into the worktree for a longer
   session.
7. When finished, clean up only on explicit request: inspect, then `git gtr rm feature-name
   --yes` (add `--force` or `--delete-branch` only as the user directs), and verify afterward.

## Example

Illustrative only — placeholder names, no real repo state:

```bash
$ git status --short
$ git gtr list
$ git gtr config list
$ git gtr new payments-fix --from-current --no-fetch
$ cd "$(git gtr go payments-fix)"
$ pwd
/home/user/repos/example-project/.worktrees/payments-fix
$ git branch --show-current
payments-fix
$ git status --short
# clean — safe to start editing
```

## Bundled resources

- [`SKILL.md`](../git-gtr-worktrees/SKILL.md) — the full instruction set summarized above:
  portability rules, repo inspection, base selection, create/enter, verify-before-editing, launch
  tools, run commands, rename, parallel work, cleanup, and troubleshooting.
- [`agents/openai.yaml`](../git-gtr-worktrees/agents/openai.yaml) — Codex-facing agent metadata:
  `display_name` ("Git GTR Worktrees"), `short_description` ("Use git gtr for repo worktrees"),
  and a `default_prompt` template for invoking the skill on a task.

There is no `scripts/` or `references/` directory in this skill package; all guidance lives in
`SKILL.md` itself.

## Limitations

- The skill assumes `git gtr` is already installed; it has no install/setup step of its own and
  simply reports the gap if the command is missing.
- `SKILL.md` is written as portable operating rules ("Do not assume a specific home directory,
  global editor, AI command, branch naming convention, or worktree location from another
  computer") and explicitly does not hard-code a base branch, worktree directory, or tool
  invocation — those must be discovered per repo via `.gtrconfig` and `git gtr config list`.
- `git gtr mv`/`rename` does not rename remote branches; the skill defers to the command's own
  remote-branch guidance rather than documenting that behavior itself.
- Provider-aware cleanup (`--merged --closed`) depends on an external provider CLI (`gh` or
  `glab`) not bundled with this skill or the repo.
- The skill does not itself define what "the user explicitly asks" means procedurally (e.g. no
  confirmation-phrase convention) — it relies on the operating agent's judgment.

## Compatibility and version notes

- Assumes a `git-worktree-runner` version that provides the subcommands referenced throughout
  `SKILL.md`: `list`, `config list`, `new`, `go`, `ai`, `editor`, `run`, `mv`/`rename`, `rm`,
  `clean`, `doctor`, and `trust`, plus flags `--from-current`, `--from <ref>`, `--no-fetch`,
  `--yes`, `--no-hooks`, `--force`, `--name`, `--delete-branch`, `--merged`, `--closed`,
  `--dry-run`. Not independently verified against a specific `git-worktree-runner` release as of
  2026-07-21; re-check flag names against the installed tool's `--help`/`doctor` output if this
  page and the tool disagree.
- The example `git gtr ai feature-name --ai codex -- --model gpt-5.6-sol` in `SKILL.md` names a
  specific Codex model (`gpt-5.6-sol`) as illustrative override syntax, not a claim that this
  model is current or required — treat model names in that command as dated to whenever they were
  last edited.
- README.md's one-line description ("Worktree creation, inspection, tool launching, and cleanup
  via `git gtr`") summarizes the scope; `SKILL.md` additionally covers base selection, entering,
  running commands, and renaming.

## Verification status

No automated tests, CI checks, or eval harness were found for this skill in the repository (no
`scripts/`, no test files, no `evals/` directory under `git-gtr-worktrees/`). The publication
boundary is checked repo-wide by `scripts/check_publication_boundary.py`, but that only scans for
leaked personal data, not skill correctness. All behavioral claims on this page were verified by
reading `SKILL.md` and `agents/openai.yaml` directly; none were verified by running `git gtr`
commands in a live repository during this documentation pass.
