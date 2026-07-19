# agent-skills

Shared agent skills for Claude Code, Codex, and other harnesses. This repository is the **single
source of truth**: a skill lives here once, and each harness reaches it through a symlink.

## Layout

Each top-level directory is one skill, containing a `SKILL.md` with `name` and `description`
frontmatter, plus any `scripts/`, `references/`, or `assets/` it needs.

| Skill | What it does |
| --- | --- |
| `accessibility-testing` | **Historical; not recommended.** Legacy Lighthouse and contrast-checking workflow |
| `braindump-intake` | Turns multi-item braindumps into reviewed atomic outcomes |
| `gh-issues` | GitHub issue management via `gh` |
| `gh-pr-review-comments` | **Historical; not recommended.** Codex users should use the official `gh-address-comments` skill |
| `git-gtr-worktrees` | Worktree creation and cleanup via `git gtr` |
| `obsidian-personal` | Supplies personal-vault targeting and machine-specific Obsidian CLI facts |
| `plan-mode-tdd` | **Historical; not recommended.** Structures plan-mode output as a TDD-first sequence |
| `pytest-profiling` | Diagnoses and fixes slow Python test suites |
| `retro` | Guided end-of-session retrospective, writing to the Obsidian vault |
| `s3-troubleshooting` | **Historical; not recommended. May contain incorrect or unsafe instructions.** Legacy S3 permissions and presigned-URL guidance |
| `session-inspect` | Inspects and compares local Codex and Claude Code session artifacts |

### `pytest-profiling` portability notes

The current workflow assumes `uv`, pytest, and Pyinstrument; includes optimization examples from
bcrypt, PostgreSQL, ASGI applications, and RSA-heavy suites; and expects profiling to lead to
edits, commits, and a written report. Test runs may also mutate project databases, services,
caches, or files. To make it more generic, detect the project's runner, treat example fixes and
timings as hypotheses, compare repeated measurements, and make edits, reports, and commits
conditional on the requested scope.

### `session-inspect`

#### Privacy notes

Default output is compact, local, and read-only. Detailed, uncapped, full-command, or JSON output
may reproduce sensitive paths, commands, repository names, prompts, or credentials stored in the
source transcripts; review it before sharing. The parser also depends on evolving Codex and Claude
Code artifact formats and may require updates as those harnesses change.

#### Example

These outputs were captured concurrently from an actual long Codex session. The `session-inspect`
session ID and the identifying fields from the matching `ccusage` record were omitted.

`session-inspect` compact output:

```text
codex <session-id> | gpt-5.6-sol/high | 2h31m | compactions=1
tokens direct=22.86M child=1.51M inclusive=24.38M
input uncached=715.3K cache-read=22.06M cache-write=unavailable | output=86.3K reasoning=42.8K
activity messages=36/85 tools=181 commands=135 reads=35 skills=16
children resolved=10 (native=10 shell=0) unresolved=0
```

The matching `ccusage 20.0.17` record, selected from:

```bash
ccusage codex session --json --offline --no-cost
```

```json
{
  "inputTokens": 727279,
  "cacheReadTokens": 22681856,
  "cacheCreationTokens": 0,
  "outputTokens": 90542,
  "reasoningOutputTokens": 44854,
  "totalTokens": 23499677,
  "models": {
    "gpt-5.6-sol": {
      "cacheCreationTokens": 0,
      "cacheReadTokens": 22681856,
      "inputTokens": 727279,
      "isFallback": false,
      "outputTokens": 90542,
      "reasoningOutputTokens": 44854,
      "totalTokens": 23499677
    }
  }
}
```

The totals disagree even though the reads were concurrent: `session-inspect` reported about 22.86M
direct tokens and 24.38M inclusive tokens, while `ccusage` reported 23,499,677 tokens for the
matching parent session. Treat figures from different inspectors as tool-specific measurements;
their snapshot and child-session aggregation rules are not interchangeable.

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
```

`install.sh` requires every skill to appear in the local manifest, including skills mapped to
`none`, and makes the harness roots match that manifest:

```bash
./install.sh            # link skills; refuse to clobber existing real directories
./install.sh --dry-run  # show what would change
./install.sh --force    # replace detached copies with symlinks (destructive)
```

A copy in a harness directory is invisible drift: you edit one, the other silently goes stale, and
neither announces which is authoritative. A symlink makes the repo the only place a skill can be
edited, so `git status` stays honest. `install.sh` reports any copies it finds so they can be
reconciled deliberately.

## Adding a skill

1. Create `<skill-name>/SKILL.md` with `name` and `description` frontmatter. The `description` is
   what the model uses to decide whether to invoke the skill, so it should say both what the skill
   does *and* when to reach for it.
2. Add its portable default mapping to `install.conf.sample` and add it to your local
   `install.conf`, then run `./install.sh` to link it into the selected roots.
3. Commit. Skill changes are commit-worthy on their own — an uncommitted skill is one that only
   exists on this machine.

Shell scripts are linted by `shellcheck` via pre-commit.
