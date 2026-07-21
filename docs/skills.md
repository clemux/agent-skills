# Skill catalog and compatibility matrix

This index lists each skill's purpose, lifecycle, default installation roots, side effects, and
prerequisites. It reflects `SKILL.md` frontmatter and
[`../install.conf.sample`](../install.conf.sample) as of 2026-07-21. If they disagree with this
table, update the table. See [Keeping this page synchronized](#keeping-this-page-synchronized).

## Matrix

| Skill | Purpose | Lifecycle | Default roots | Interaction risk | Key prerequisites |
| --- | --- | --- | --- | --- | --- |
| [accessibility-testing](accessibility-testing.md) | Lighthouse audits and WCAG contrast checks for a running site | Historical | none | Local writes | Node/`npx` (`lighthouse`, `get-contrast`), headless Chrome, a running dev server, `jq` |
| [braindump-intake](braindump-intake.md) | Decompose a multi-item braindump into a reviewed ledger of atomic outcomes | Active | claude, codex, agents | External writes | Optional persistence tool or companion skill; runs plan-only without one |
| [gh-issues](gh-issues.md) | List, view, create, edit, and close GitHub issues via `gh` | Active | claude | External writes | `gh` CLI installed and authenticated |
| [gh-pr-review-comments](gh-pr-review-comments.md) | Retrieve and reply to inline PR review comments via `gh` and bundled scripts | Historical | none | External writes | `gh` CLI authenticated; bundled `*.sh` scripts |
| [git-gtr-worktrees](git-gtr-worktrees.md) | Create, enter, inspect, and clean up Git worktrees with `git gtr` | Active | claude, codex, agents | Local writes | `git-worktree-runner` (`git gtr`) installed; falls back to `git worktree` only with approval |
| [gpt-5.6-prompting](gpt-5.6-prompting.md) | Guidance for composing Codex / GPT-5.6 prompts delegated from Claude Code | Untested | claude | Read-only | Reference only; targets GPT-5.6 models such as `gpt-5.6-sol` |
| [obsidian-personal](obsidian-personal.md) | Machine-specific adapter for one user's Obsidian vault and CLI | Active | claude, codex, agents | Local writes | Obsidian standalone CLI (1.12.7+); the specific personal vault; machine-bound values |
| [plan-mode-tdd](plan-mode-tdd.md) | Structure Plan-mode output as a tests-first TDD sequence | Historical | none | Read-only | Plan mode; references a `feature-dev:code-reviewer` agent |
| [pytest-profiling](pytest-profiling.md) | Diagnose slow pytest suites, apply fixes, and write a report | Active | claude, codex, agents | Local writes | Python suite, the project's pytest runner, `pyinstrument`; may edit code and mutate project state |
| [retro](retro.md) | Guided end-of-session retrospective written through a pluggable backend | Active | claude, codex, agents | External writes | A retro backend adapter skill (optional); `/retro` or `$retro` entry point |
| [s3-troubleshooting](s3-troubleshooting.md) | Debug S3-compatible storage: policies, presigned URLs, CORS | Historical | none | External writes | Access to AWS S3 / Scaleway / MinIO; advisory — may recommend policy changes |
| [session-inspect](session-inspect.md) | Inspect and diff local Codex and Claude Code session artifacts | Active | claude, codex, agents | Read-only | `python3`; local `~/.codex/sessions` and `~/.claude/projects` files; bundled script |
| [skill-evaluator](skill-evaluator.md) | Benchmark and improve a Codex skill against controlled baselines | Active | codex | Local writes | Codex CLI with auth, Git, Python 3; spends real Codex tokens per run |
| [workflow-fanout-checklist](workflow-fanout-checklist.md) | Gate a Claude Workflow fan-out script through an approval checklist | Active | claude | Local writes | Claude Code Workflow / ultracode; a separate verifier agent |

## Column legend

### Skill

The directory name, which must equal the `name` in that skill's `SKILL.md` frontmatter. The link
goes to the skill's own documentation page under `docs/`.

### Purpose

A one-line paraphrase of the skill's frontmatter `description`. It is a summary, not the trigger:
the full `description` — which also states *when* the skill fires — is on the linked page and in the
skill's `SKILL.md`.

### Lifecycle

Current maintenance status. These labels do not endorse a skill or claim that it suits another
environment:

- **Active** — still used or maintained by the author.
- **Historical** — kept for reference but not recommended; may be superseded, narrow, or tied to a
  workflow the maintainer no longer uses. `s3-troubleshooting` additionally carries a
  "may contain incorrect or unsafe instructions" warning in `../README.md`.
- **Untested** — present and mapped to a harness but not verified to work as described.
  `gpt-5.6-prompting` is the only such entry.

### Default roots

Which harness roots `install.sh` links the skill into *by default*, taken verbatim from
[`../install.conf.sample`](../install.conf.sample):

- **claude** — `~/.claude/skills`
- **codex** — `~/.codex/skills`
- **agents** — `~/.agents/skills`, the harness-neutral root
- **none** — the skill lives in this repo but no harness loads it by default

This column records **where a skill is installed by default, not whether it will work on a given
machine** — availability, not compatibility. A skill can be mapped to `claude` and still do nothing
if its prerequisites are missing (see the next column); conversely `none` means "not installed by
default," not "broken." `gpt-5.6-prompting` illustrates the gap: it is mapped to `claude` yet
labelled Untested. The mapping in `install.conf.sample` is the *portable default*; each machine
copies it to an ignored, machine-local `install.conf` and may target different roots, so a
particular checkout can differ from this column. `install.conf` is the source of truth for what a
specific machine actually links.

### Interaction risk

The strongest side effect the skill can have when followed, so a reader knows what is at stake
before invoking it:

- **Read-only** — inspects, plans, or advises without writing. `session-inspect` states it is
  "strictly local and read-only"; `gpt-5.6-prompting` and `plan-mode-tdd` produce guidance or a
  plan rather than changes.
- **Local writes** — creates or modifies files, worktrees, or state on the local machine. Examples:
  `git-gtr-worktrees` (worktrees and branches), `pytest-profiling` (edits, reports, and possibly
  mutated project databases/services), `obsidian-personal` (local vault), `skill-evaluator`
  (eval artifacts), `accessibility-testing` (a report file), `workflow-fanout-checklist` (a script
  file).
- **External writes** — can change state in a remote or shared system. `gh-issues` and
  `gh-pr-review-comments` write to GitHub; `s3-troubleshooting` may advise changes to bucket or IAM
  policies; `retro` and `braindump-intake` persist through a backend or companion tool whose
  destination (a knowledge vault, a task system) can be remote or shared.

This is a ceiling, not a promise every run reaches it — most skills also have read-only modes.

### Key prerequisites

The external tools, credentials, or companion skills a skill needs. A missing prerequisite is why a
skill mapped to a harness can still be effectively unavailable on a machine — the compatibility half
of the availability-versus-compatibility distinction called out under **Default roots**.

## Example: reading one row

Illustrative, using placeholder data. To go from a matrix row to a working invocation of, say,
`<skill-name>`:

```bash
# 1. Confirm the skill is actually linked into this harness on this machine
#    (the matrix shows the DEFAULT; install.conf is what this machine did).
#    A correctly linked skill prints nothing in the dry run, so check the link directly:
ls -l ~/.claude/skills/<skill-name>          # should be a symlink into this repo
./install.sh --dry-run                       # would report anything broken or drifted

# 2. Check the prerequisite named in the row is present, e.g. a CLI:
<prereq-cli> --version

# 3. Read the skill's own page for the full description and trigger phrases:
#    docs/<skill-name>.md
```

The matrix tells you a skill *could* apply; the linked page and the prerequisite check tell you
whether it applies *here, now*.

## Keeping this page synchronized

This page duplicates each `*/SKILL.md` frontmatter and
[`../install.conf.sample`](../install.conf.sample), so it can drift. A skill added, renamed,
retired, or remapped without a matching row update is incomplete. Specifically:

- The set of rows must equal the set of skill directories (one `SKILL.md` each). No orphan rows, no
  missing skills.
- Each row's **Skill** name must match the directory name and the frontmatter `name`.
- Each row's **Default roots** must match that skill's line in `install.conf.sample`.
- Each row's link target `docs/<skill>.md` must exist.

Commands a maintainer runs to spot drift:

```bash
# From the repository root.

# Rows-vs-directories: every skill directory should have exactly one SKILL.md,
# and every one of those names should appear in this page.
for d in */SKILL.md; do echo "${d%/SKILL.md}"; done | sort

# The authoritative default mapping, minus comments and blank lines. Each name +
# roots here must match the Default roots column above.
grep -vE '^\s*(#|$)' install.conf.sample

# What is actually linked on THIS machine (uses install.conf, not the sample),
# and which entries are copies rather than symlinks.
./install.sh --dry-run
```

If any of those outputs disagrees with the matrix, fix the matrix in the same change that moved the
skill — do not leave the reconciliation for later, because a stale catalog is the same silent-drift
failure this repository exists to prevent (see [`../AGENTS.md`](../AGENTS.md)).
