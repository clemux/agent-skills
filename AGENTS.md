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

Edit `<repo>/<skill>/SKILL.md` — the real file. If you find yourself writing to
`~/.claude/skills/<skill>/` or `~/.codex/skills/<skill>/`, stop: either that path is a symlink (in
which case use the repo path, so the diff is visible to `git status`) or it is a detached copy (in
which case editing it creates exactly the drift this repo exists to prevent, and the copy needs
reconciling instead).

Drift here is silent and expensive. Two copies of a skill that differ give no error — they just make
one harness behave differently from another, and the next agent cannot tell which version was
intended. That was the original motivating failure: a skill created under `~/.codex/skills/` was
invisible to Claude Code until someone noticed by hand.

Run `./install.sh --dry-run` to see which skills are properly linked and which are copies.

## Publication boundary

Treat every tracked file in this repository as if it will be published publicly. Shared skills
must be portable, backend-neutral, and safe to use without access to one person's machine, vault,
or project history.

- Do not commit personal or confidential data: usernames, hostnames, absolute personal paths,
  vault names or IDs, private project identifiers, raw session artifacts, or historical details
  that identify a private workspace.
- Do not put Obsidian Agent Workflow lifecycle commands, note schemas, vault conventions, or other
  OAW-specific orchestration into shared skills. When a workflow has a reusable core and an OAW
  adapter, keep the backend-neutral core here and the adapter in the OAW repository.
- A shared skill may depend on files bundled in its own repository package or on official platform
  capabilities. It must not require a personal helper, private plugin, custom skill, or CLI owned by
  another repository. Expose an integration seam instead and keep the custom adapter with its
  owning repository.
- Examples must use placeholders and generic sample data. Do not paste real command output before
  redacting paths, IDs, names, and project-specific context.

Run `python3 scripts/check_publication_boundary.py` before committing. The check scans tracked text
for likely leaks. `.publication-boundary-allowlist.json` is reserved for reviewed false positives
and explicitly tracked legacy cleanup: each exception must name an exact file, specific rules, and
a reason. Never add a directory-wide or catch-all exception, and remove an entry as soon as the
underlying match disappears. Machine-specific private markers belong in the ignored
`.publication-boundary-local.json`; copy `.publication-boundary-local.sample.json` as a starting
point and replace its fictional values locally. Public checkouts still enforce the universal rules
when that file is absent.

## Documentation

Skill pages are public documentation, not records of an agent reviewing the repository.

- Write concise facts. Do not invent retirement reasons, usage history, quality judgments,
  compatibility claims, or replacements.
- Include an author's reason or assessment only when the author supplied it explicitly.
- Do not publish review-process language such as "checked against," "verified for this page," or
  descriptions of what an agent inspected while drafting the documentation.
- Keep useful factual examples and test evidence. Concision does not require removing concrete
  evidence that helps readers understand the skill.
- Do not force every page into the same template. Omit sections that add no useful information.
- Prefer an explicit `TODO` or placeholder to a guess.
- Preserve author-supplied wording verbatim when requested.
- When deriving an example from a past session, inspect the source evidence and distinguish work
  caused by the retrospective from work that happened before it.
- When reviewing multiple skill pages with the user, treat each page as a separate decision gate.
  Do not mark it complete or advance to the next page until the user explicitly approves it. A
  requested revision reopens the gate.

## Keeping skill representations synchronized

A skill change is complete only when its directory, manifest entries, README row, documentation
page, and `docs/skills.md` row agree.

- Adding: create the skill, update both manifests, run `./install.sh`, and add the README and docs
  entries.
- Renaming: update the directory, frontmatter, manifests, links, and docs; run `./install.sh` and
  remove stale old-name symlinks.
- Retiring: map the skill to `none`, run `./install.sh`, and update its README and docs entries. Do
  not invent a reason for the retirement.
- Deleting: remove the skill, both manifest entries, README row, documentation page, and catalog
  row, then run `./install.sh`.

Run `pre-commit run --all-files` before committing.

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
