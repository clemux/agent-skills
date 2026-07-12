# agent-skills

Shared agent skills for Claude Code, Codex, and other harnesses. This repository is the **single
source of truth**: a skill lives here once, and each harness reaches it through a symlink.

## Layout

Each top-level directory is one skill, containing a `SKILL.md` with `name` and `description`
frontmatter, plus any `scripts/`, `references/`, or `assets/` it needs.

| Skill | What it does |
| --- | --- |
| `accessibility-testing` | WCAG compliance, contrast ratios, Lighthouse audits |
| `gh-issues` | GitHub issue management via `gh` |
| `gh-pr-review-comments` | Reading and replying to PR review comments |
| `git-gtr-worktrees` | Worktree creation and cleanup via `git gtr` |
| `plan-mode-tdd` | Structures plan-mode output as a TDD-first sequence |
| `pytest-profiling` | Diagnoses and fixes slow Python test suites |
| `retro` | Guided end-of-session retrospective, writing to the Obsidian vault |
| `s3-troubleshooting` | S3 permissions, policies, presigned URLs |

## Installing

Harnesses discover skills in their own directories:

- Claude Code — `~/.claude/skills/`
- Codex — `~/.codex/skills/`
- Neutral shared root — `~/.agents/skills/`

**Symlink, don't copy.** Run `./install.sh` to link every skill in this repo into all three roots:

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
2. Run `./install.sh` to link it into the harness roots.
3. Commit. Skill changes are commit-worthy on their own — an uncommitted skill is one that only
   exists on this machine.

Shell scripts are linted by `shellcheck` via pre-commit.
