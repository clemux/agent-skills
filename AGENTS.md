# AGENTS.md

This repository is the single source of truth for shared agent skills. Harnesses (Claude Code,
Codex, and the neutral `~/.agents/skills` root) reach each skill through a symlink back to this
repo.

## The rule that matters

**Never edit a skill through a harness path, and never copy a skill into a harness directory.**

Edit `~/dev/agent-skills/<skill>/SKILL.md` — the real file. If you find yourself writing to
`~/.claude/skills/<skill>/` or `~/.codex/skills/<skill>/`, stop: either that path is a symlink (in
which case use the repo path, so the diff is visible to `git status`) or it is a detached copy (in
which case editing it creates exactly the drift this repo exists to prevent, and the copy needs
reconciling instead).

Drift here is silent and expensive. Two copies of a skill that differ give no error — they just make
one harness behave differently from another, and the next agent cannot tell which version was
intended. That was the original motivating failure: a skill created under `~/.codex/skills/` was
invisible to Claude Code until someone noticed by hand.

Run `./install.sh --dry-run` to see which skills are properly linked and which are copies.

## Working here

- A skill is a directory with `SKILL.md` (frontmatter: `name`, `description`) plus optional
  `scripts/`, `references/`, `assets/`.
- The `description` frontmatter is the sole trigger mechanism — it must say what the skill does
  *and* the situations that should invoke it. A skill that never triggers is dead code.
- New skills need `./install.sh` before any harness can see them.
- Treat a finished skill change as commit-worthy in its own right: verify it, review the diff,
  commit. Do not leave a working skill uncommitted — it then exists only on one machine, which is
  the same failure mode as drift wearing a different hat.
- Shell scripts must pass `shellcheck` (enforced by pre-commit).

## Related

The `retro` skill writes into clemux's Obsidian vault via the `oaw` CLI, and records its harness
mappings in the vault task `AGT-TSK-retro-skill`. Vault-side conventions live with the vault, not
here; this repo owns the skill text only.
