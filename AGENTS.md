# AGENTS.md

This repository is the single source of truth for shared agent skills. Harnesses (Claude Code,
Codex, and the neutral `~/.agents/skills` root) reach each skill through a symlink back to this
repo.

Not every skill goes to every harness. `install.conf.sample` records the portable default mapping;
each machine copies it to the ignored `install.conf` and adjusts that local manifest for its
installed harnesses. `install.sh` makes the roots match the local table — linking the roots a skill
targets and removing it from the roots it does not. A skill missing from the local `install.conf`
is an error rather than a default, because leaving "where does this go?" implicit is how the roots
drifted apart before.

## The working tree is the deployed state

Because the harness roots symlink *into this checkout*, whatever is checked out right now is what
every harness loads. Switching branches silently changes the skills your agents are running — no
error, no warning, just different behaviour. So keep skill work short-lived and merge it promptly,
and remember when debugging a skill that behaves unexpectedly that the first thing to check is which
branch this repo is on.

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
  `scripts/`, `references/`, `assets/`. The `name` must match the directory name.
- The `description` frontmatter is the sole trigger mechanism — it must say what the skill does
  *and* the situations that should invoke it. A skill that never triggers is dead code.
- New skills need a portable default entry in `install.conf.sample`, a matching entry in the
  machine-local `install.conf`, and a run of `./install.sh` before any harness can see them.
- A bundled script must be runnable from any harness. Document the plain command it wraps, and never
  depend on a harness-specific variable to find it — a path that only resolves in one harness is a
  skill that silently does nothing in the others.
- Treat a finished skill change as commit-worthy in its own right: verify it, review the diff,
  commit. Do not leave a working skill uncommitted — it then exists only on one machine, which is
  the same failure mode as drift wearing a different hat.
- Shell scripts must pass `shellcheck` (enforced by pre-commit).

## Related

The `retro` skill writes into clemux's Obsidian vault via the `oaw` CLI, and records its harness
mappings in the vault task `AGT-TSK-retro-skill`. Vault-side conventions live with the vault, not
here; this repo owns the skill text only.
