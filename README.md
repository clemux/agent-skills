# agent-skills

A personal collection of agent skills, shared for illustration only. They are not a vetted library
or a set of recommendations. There is no claim that any skill is good, complete, safe, or sensible
to use as-is, and only some are still used by the author.

Much of the documentation was generated with AI. Sorry for the verbosity, repetition, and any
mistakes. Read the source and check the instructions before using a skill.

For the author's local setup, this repository is the **single source of truth**: a skill lives here
once, and each harness reaches it through a symlink.

## Layout

Each skill has a top-level directory containing a `SKILL.md` with `name` and `description`
frontmatter, plus any `scripts/`, `references/`, or `assets/` it needs. Each skill also has a
documentation page under [`docs/`](docs/skills.md) — the skill names below link to them.

| Skill | What it does | Default roots |
| --- | --- | --- |
| [`accessibility-testing`](docs/accessibility-testing.md) | Historical accessibility checks for a Quasar project | none |
| [`braindump-intake`](docs/braindump-intake.md) | Turns multi-item braindumps into reviewed atomic outcomes | claude codex agents |
| [`gh-issues`](docs/gh-issues.md) | Helps agents retrieve GitHub issues with `gh` | claude |
| [`gh-pr-review-comments`](docs/gh-pr-review-comments.md) | Historical helpers for inline pull-request review comments | none |
| [`git-gtr-worktrees`](docs/git-gtr-worktrees.md) | Worktree creation, inspection, tool launching, and cleanup via `git gtr` | claude codex agents |
| [`gpt-5.6-prompting`](docs/gpt-5.6-prompting.md) | Experimental GPT-5.6 prompting guidance for delegation from Claude Code | claude |
| [`obsidian-personal`](docs/obsidian-personal.md) | Temporary, machine-specific Obsidian adapter | claude codex agents |
| [`plan-mode-tdd`](docs/plan-mode-tdd.md) | Structures plan-mode output as a TDD sequence | none |
| [`pytest-profiling`](docs/pytest-profiling.md) | Diagnoses and fixes slow Python test suites | claude codex agents |
| [`retro`](docs/retro.md) | Guided end-of-session retrospective with pluggable storage backends | claude codex agents |
| [`s3-troubleshooting`](docs/s3-troubleshooting.md) | S3 troubleshooting notes the author no longer uses | none |
| [`session-inspect`](docs/session-inspect.md) | Inspects and compares local Codex and Claude Code session artifacts | claude codex agents |
| [`skill-evaluator`](docs/skill-evaluator.md) | Work-in-progress extraction of skill evaluation tooling for Codex | codex |
| [`workflow-fanout-checklist`](docs/workflow-fanout-checklist.md) | Reviews Claude Workflow fan-out scripts before they run | claude |

**Default roots** is the portable default harness mapping from
[`install.conf.sample`](install.conf.sample) (`none` = tracked but installed nowhere); each machine
can diverge in its local `install.conf`.

### `obsidian-personal` privacy warning

This machine-specific skill intentionally contains a hard-coded personal vault name, absolute vault
path, plugin-state locations, workflow routes, and a named Base view, and is allowlisted in the
publication-boundary check pending a template/private-instance split. Reusing it on another machine
means replacing that entire local configuration, not just two values — see
[docs/obsidian-personal.md](docs/obsidian-personal.md).

## Documentation

- [docs/skills.md](docs/skills.md) — skill catalog and default installation roots.
- [docs/installing.md](docs/installing.md) — manifest semantics and `install.sh` mechanics.
- [docs/verification.md](docs/verification.md) — every automated check, what it covers, and the
  coverage gaps.
- `docs/<skill>.md` — one concise page per skill.

The repository rules — the working tree is the deployed state, never edit a skill through a harness
path, the publication boundary — live in [AGENTS.md](AGENTS.md).

## Installing

Harnesses discover skills in their own directories:

- Claude Code — `~/.claude/skills/`
- Codex — `~/.codex/skills/`
- Neutral shared root — `~/.agents/skills/`

**Symlink, don't copy.** `install.conf.sample` provides the repository's default harness
mapping. Copy it to the ignored, machine-local `install.conf`, adjust the targets for the
harnesses installed on this machine, then run `./install.sh`:

```bash
cp install.conf.sample install.conf
./install.sh            # link skills; refuse to clobber existing real directories
./install.sh --dry-run  # show what would change
./install.sh --force    # replace detached copies with symlinks (destructive)
```

`install.sh` requires every skill to appear in the local manifest, including skills mapped to
`none`, and makes the harness roots match that manifest. A copy in a harness directory is invisible
drift: you edit one, the other silently goes stale, and neither announces which is authoritative.
See [docs/installing.md](docs/installing.md) for the exact manifest and removal semantics.

## Adding a skill

1. Create `<skill-name>/SKILL.md` with `name` and `description` frontmatter. The `description` is
   what the model uses to decide whether to invoke the skill, so it should say both what the skill
   does *and* when to reach for it.
2. Add its portable default mapping to `install.conf.sample` and add it to your local
   `install.conf`, then run `./install.sh` to link it into the selected roots.
3. Document it: a row in the table above, a `docs/<skill-name>.md` page, and a row in
   [docs/skills.md](docs/skills.md).
4. Commit the change.

Shell scripts are linted by `shellcheck` via pre-commit; see
[docs/verification.md](docs/verification.md) for all checks.
