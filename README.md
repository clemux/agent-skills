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

| Skill | What it does | Default roots | Risk |
| --- | --- | --- | --- |
| [`accessibility-testing`](docs/accessibility-testing.md) | **Historical; not recommended.** Legacy Lighthouse and contrast-checking workflow | none | Local writes |
| [`braindump-intake`](docs/braindump-intake.md) | Turns multi-item braindumps into reviewed atomic outcomes | claude codex agents | External writes |
| [`gh-issues`](docs/gh-issues.md) | GitHub issue management via `gh` | claude | External writes |
| [`gh-pr-review-comments`](docs/gh-pr-review-comments.md) | **Historical; not recommended.** Codex users should use the official `gh-address-comments` skill | none | External writes |
| [`git-gtr-worktrees`](docs/git-gtr-worktrees.md) | Worktree creation, inspection, tool launching, and cleanup via `git gtr` | claude codex agents | Local writes |
| [`gpt-5.6-prompting`](docs/gpt-5.6-prompting.md) | **Not tested.** Guidance for composing Codex and GPT-5.6 prompts delegated from Claude Code | claude | Read-only |
| [`obsidian-personal`](docs/obsidian-personal.md) | Supplies personal-vault targeting and machine-specific Obsidian CLI facts (see privacy warning below) | claude codex agents | Local writes |
| [`plan-mode-tdd`](docs/plan-mode-tdd.md) | **Historical; not recommended.** Structures plan-mode output as a TDD-first sequence | none | Read-only |
| [`pytest-profiling`](docs/pytest-profiling.md) | Diagnoses and fixes slow Python test suites | claude codex agents | Local writes |
| [`retro`](docs/retro.md) | Guided end-of-session retrospective with pluggable storage backends | claude codex agents | External writes |
| [`s3-troubleshooting`](docs/s3-troubleshooting.md) | **Historical; not recommended. May contain incorrect or unsafe instructions.** Legacy S3 permissions and presigned-URL guidance | none | External writes |
| [`session-inspect`](docs/session-inspect.md) | Inspects and compares local Codex and Claude Code session artifacts | claude codex agents | Read-only |
| [`skill-evaluator`](docs/skill-evaluator.md) | Benchmarks and improves Codex skills against controlled baselines | codex | Local writes |
| [`workflow-fanout-checklist`](docs/workflow-fanout-checklist.md) | Claude Workflow fan-out safety checklist | claude | Local writes |

**Default roots** is the portable default harness mapping from
[`install.conf.sample`](install.conf.sample) (`none` = tracked but installed nowhere); each machine
can diverge in its local `install.conf`. **Risk** is the strongest side effect the skill can have
when followed — see the [skill catalog](docs/skills.md) for the full compatibility matrix, the
column legend, and per-skill prerequisites.

### `obsidian-personal` privacy warning

This machine-specific skill intentionally contains a hard-coded personal vault name, absolute vault
path, plugin-state locations, workflow routes, and a named Base view, and is allowlisted in the
publication-boundary check pending a template/private-instance split. Reusing it on another machine
means replacing that entire local configuration, not just two values — see
[docs/obsidian-personal.md](docs/obsidian-personal.md).

## Documentation

- [docs/skills.md](docs/skills.md) — complete skill catalog and compatibility matrix.
- [docs/installing.md](docs/installing.md) — manifest semantics and `install.sh` mechanics.
- [docs/contributing.md](docs/contributing.md) — docs conventions and the definition of done for
  adding, renaming, or retiring a skill.
- [docs/verification.md](docs/verification.md) — every automated check, what it covers, and the
  coverage gaps.
- `docs/<skill>.md` — one page per skill: status, triggers, prerequisites, read/write boundaries,
  limitations, and verification state.

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
   [docs/skills.md](docs/skills.md). See [docs/contributing.md](docs/contributing.md) for the full
   definition of done.
4. Commit the change.

Shell scripts are linted by `shellcheck` via pre-commit; see
[docs/verification.md](docs/verification.md) for all checks.
