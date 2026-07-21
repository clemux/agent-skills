# Contributing

This page covers documentation, adding or retiring skills, pre-commit setup, and the
publication-boundary files. Repository rules live in [AGENTS.md](../AGENTS.md); read it first.

## Before you start

- The working tree is what every harness loads right now, and switching branches silently changes
  the deployed skills. See [AGENTS.md — "The working tree is the deployed state"](../AGENTS.md) for
  why this matters and what to check when a skill misbehaves.
- Never edit a skill through `~/.claude/skills/<skill-name>/` or `~/.codex/skills/<skill-name>/`.
  Edit the real file in the repo. See [AGENTS.md — "The rule that matters"](../AGENTS.md).
- The mechanics of the manifest and `install.sh` are documented separately in
  [installing.md](installing.md); this page references those steps rather than repeating them.

## The docs/ conventions

Each skill is documented in three places, in addition to its own `SKILL.md`:

1. **A row in the [`README.md`](../README.md) skill table** — the skill name (linked to its
   `docs/<skill-name>.md` page), a one-line description, the default roots, and the risk class.
   Historical or unrecommended skills carry a bold status prefix in the description cell (for
   example `**Historical; not recommended.**` or `**Not tested.**`).
2. **A page at `docs/<skill-name>.md`** — one Markdown page per skill, named exactly for the skill
   directory. This page carries the detail that does not fit in a README row: status, portability
   and privacy notes, verification state, and an illustrative example where one helps.
3. **A row in the [`skills.md`](skills.md) catalog** — the docs index linking the skill name to its
   page.

### Linking conventions

- Docs pages link to each other with docs-relative links (for example `skills.md`,
  `installing.md`).
- Docs pages link **up** into the repo with `../` (for example
  [`../install.conf.sample`](../install.conf.sample), [`../README.md`](../README.md), or a skill's
  own [`../<skill-name>/SKILL.md`](../accessibility-testing/SKILL.md)).
- Do not copy a skill's checklist, schema, or reference material into its docs page. Link to the
  file in the skill package instead.

### What a historical page looks like

Some skills are retained but mapped to no harness (`none` in
[`install.conf.sample`](../install.conf.sample)) and marked historical or unrecommended in the
README. Their docs pages follow a consistent shape so a reader can tell at a glance why the skill is
kept and what is unsafe about running it. See
[`docs/accessibility-testing.md`](accessibility-testing.md) as the worked example. A historical page
generally includes:

- **Status** — restates the README verdict (for example "Historical; not recommended for direct
  use") and shows the `install.conf.sample` mapping line.
- **Why it was retired** — the concrete defects (frontmatter/body mismatch, framework or
  environment coupling, side effects), each pointing at the specific evidence in the skill's
  `SKILL.md`.
- **Known risks** — what goes wrong if the skill is invoked as-is.
- **Migration / replacement** — what a safe replacement would need, or a note that none exists yet.
- **Verification status** — whether the skill was ever exercised against a real target, stated
  plainly (often "never validated").
- **Example** — clearly marked illustrative, never presented as a captured run for an unverified
  skill.

## Definition of done

A skill change is not finished until the manifest, README, and docs agree.

### Adding a skill

1. Create `<skill-name>/SKILL.md` with `name` and `description` frontmatter. `name` must match the
   directory name; the `description` is the sole trigger mechanism. See
   [AGENTS.md — "Working here"](../AGENTS.md) for the anatomy and description requirements.
2. Add a portable default entry to [`install.conf.sample`](../install.conf.sample), and a matching
   entry to your machine-local `install.conf`. An unlisted skill is an error, not a default. See
   [installing.md](installing.md) for the manifest format and root names.
3. Run `./install.sh` (optionally `./install.sh --dry-run` first) to link the skill into its
   targeted roots. See [installing.md](installing.md).
4. Add a row to the [`README.md`](../README.md) skill table.
5. Add a `docs/<skill-name>.md` page.
6. Add a row to the [`skills.md`](skills.md) catalog linking to that page.
7. Commit. A finished skill change is commit-worthy on its own — an uncommitted skill exists only on
   one machine, which is the same failure mode as drift. See
   [AGENTS.md — "Working here"](../AGENTS.md).

### Renaming a skill

A rename touches every place the old name appears, because the directory name is load-bearing (the
`SKILL.md` `name` and the harness symlink both key off it):

1. Rename the skill directory and update the `name` frontmatter in `SKILL.md` to match.
2. Update the entry in [`install.conf.sample`](../install.conf.sample) and your local
   `install.conf`.
3. Run `./install.sh` to create the new symlink, then remove the old-name symlink from each
   harness root yourself (for example `rm ~/.claude/skills/<old-name>`). `install.sh` only visits
   skill directories that currently exist, so it never sees the old name and cannot clean up its
   stale link. See [installing.md](installing.md).
4. Update the [`README.md`](../README.md) row.
5. Rename `docs/<old-name>.md` to `docs/<new-name>.md` and update its `../<old-name>/…` links.
6. Update the [`skills.md`](skills.md) row and any docs-relative links pointing at the old page
   name.
7. Commit.

### Retiring a skill

Retiring usually means keeping the skill in the repo as a historical reference while removing it
from every harness, rather than deleting it:

1. Map the skill to `none` in [`install.conf.sample`](../install.conf.sample) and your local
   `install.conf`.
2. Run `./install.sh` to remove its symlinks from every root. See [installing.md](installing.md).
3. Mark the [`README.md`](../README.md) row with a status prefix (for example
   `**Historical; not recommended.**`).
4. Rewrite `docs/<skill-name>.md` in the historical-page shape described above.
5. Update the [`skills.md`](skills.md) row to reflect the retired status.
6. Commit.

If instead the skill is being deleted outright, remove its directory, its `install.conf.sample` and
local `install.conf` entries, its README row, its `docs/<skill-name>.md` page, and its `skills.md`
row, then run `./install.sh` and commit.

## Pre-commit

The repository ships a [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) with three hooks:

- **shellcheck** — lints shell scripts (from `koalaman/shellcheck-precommit`, pinned at `v0.11.0`
  as of 2026-07-21). AGENTS.md requires shell scripts to pass shellcheck.
- **publication-boundary** — runs `python3 scripts/check_publication_boundary.py` over tracked text
  (see below).
- **publication-boundary-tests** — runs the unit tests for that check
  (`python3 -m unittest discover -s tests -p test_publication_boundary.py`).

Install and run the hooks:

```bash
pip install pre-commit        # or: pipx install pre-commit
pre-commit install            # register the git hook
pre-commit run --all-files    # run every hook against the whole repo
```

Once `pre-commit install` has registered the hook, the configured checks run automatically on
`git commit`.

## Publication boundary

Treat every tracked file as public. The full policy — what counts as private data, why shared
skills must be backend-neutral, and the integration-seam rule — is in
[AGENTS.md — "Publication boundary"](../AGENTS.md). The mechanics you interact with:

- **The check**: `python3 scripts/check_publication_boundary.py` scans tracked text for likely
  leaks (personal home paths, home-relative development-directory paths, `obs:` references,
  session-identity environment variables, and configurable private markers). It runs as the
  `publication-boundary` pre-commit hook, and can be run directly.
- **The allowlist**: [`.publication-boundary-allowlist.json`](../.publication-boundary-allowlist.json)
  is tracked and reserved for reviewed false positives and explicitly tracked legacy cleanup. Each
  exception must name an exact file, the specific rules, and a reason. Never add a directory-wide or
  catch-all exception, and remove an entry as soon as the underlying match disappears. See
  [AGENTS.md](../AGENTS.md).
- **The machine-local config**: `.publication-boundary-local.json` is git-ignored and holds
  machine-specific private markers (private reference prefixes and marker strings) so the check can
  flag your own workspace's identifiers. Copy
  [`.publication-boundary-local.sample.json`](../.publication-boundary-local.sample.json) as a
  starting point and replace its fictional values locally. Public checkouts still enforce the
  universal rules when this file is absent.

When your change trips the check on a genuine leak, fix the content — redact the path, ID, or name
and use a placeholder. Reserve the allowlist for confirmed false positives, not for silencing real
findings.

## Example

Illustrative only — a command sequence for adding a skill named `<skill-name>`, using placeholder
data:

```bash
# 1. create the skill
mkdir <skill-name>
$EDITOR <skill-name>/SKILL.md          # add name + description frontmatter

# 2. map it in the manifest (sample + your machine-local copy)
$EDITOR install.conf.sample            # e.g. "<skill-name>   claude agents"
$EDITOR install.conf

# 3. link it into the targeted harness roots
./install.sh --dry-run                 # review
./install.sh                           # apply

# 4-6. document it: README row, docs page, skills.md row
$EDITOR README.md
$EDITOR docs/<skill-name>.md
$EDITOR docs/skills.md

# 7. verify the boundary and commit
pre-commit run --all-files
git add -A && git commit -m "add <skill-name> skill"
```

The `./install.sh --dry-run` step prints the symlinks it would create; see
[installing.md](installing.md) for how to read that output and what the roots mean.
