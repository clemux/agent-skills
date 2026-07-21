# Installing skills

This repository is the source of truth for its skills. Each machine runs `install.sh`, which uses a
machine-local manifest (`install.conf`) to symlink skills into harness directories. For the policy
on editing skills and drift, see [AGENTS.md](../AGENTS.md).

## The three harness roots

`install.sh` recognizes three target roots, hard-coded in the script:

| Root name | Path | Harness |
| --- | --- | --- |
| `claude` | `~/.claude/skills/` | Claude Code |
| `codex` | `~/.codex/skills/` | Codex |
| `agents` | `~/.agents/skills/` | Neutral shared root, not tied to one harness |

Each harness scans its own directory. A skill is visible only when its symlink exists under that
harness's root.

## Symlink, don't copy

`install.sh` links skills into harness roots with `ln -s`; it never copies content. A copied skill
can diverge silently: edits to `~/.claude/skills/<skill-name>/` do not change the repo, and repo
edits do not change the copy. A symlink holds no content, so the repo remains the only file and
`git status` reflects what every harness sees.

`install.sh` treats any **real file or directory** at a target path as a **detached copy**, which
may contain edits not brought back into the repo, and refuses to touch it without `--force`. A
symlink outside the repo is drift, not a copy, and is relinked without `--force`.

## The manifest: `install.conf`

Target mappings live in `install.conf`, which is git-ignored (machine-specific) and read by
`install.sh`. The tracked [`install.conf.sample`](../install.conf.sample) is the portable default
mapping; each machine copies it and edits the copy for the harnesses actually installed there.

Manifest lines have the form:

```text
<skill-name>   <root> [<root> ...]
```

Roots are space-separated; `#` starts a comment. The special value `none` means the skill is
tracked in this repo but intentionally installed nowhere.

Exact semantics, read from `install.sh`:

- **Every skill directory in the repo must have a line in `install.conf`.** `install.sh` walks
  every top-level directory containing a `SKILL.md` and looks it up in the manifest; if a skill is
  missing from the manifest, the script prints an error and exits before making any changes. `none`
  is a valid, explicit entry — omitting the skill entirely is not.
- **A manifest entry naming a skill that doesn't exist in the repo is also an error.** `install.sh`
  checks that `<repo>/<skill-name>/SKILL.md` exists for every line it reads.
- **An unknown root name is an error.** Only `claude`, `codex`, and `agents` are recognized; a typo
  elsewhere in a manifest line stops the run.

## What `install.sh` does: link listed roots, remove unlisted ones

`install.sh` makes the harness roots match the manifest exactly — for every skill and every root,
not just the roots mentioned on that skill's line:

- **Root not present on disk**: skipped entirely (e.g. no `~/.codex/skills/` directory because
  Codex isn't installed on this machine).
- **Targeted root, no existing entry**: creates the symlink.
- **Targeted root, entry is already a symlink resolving into this repo**: left alone.
- **Targeted root, entry is a symlink resolving somewhere else** (e.g. into a different checkout):
  treated as drift even though it's a symlink — removed and relinked into this repo.
- **Targeted root, entry is a real directory (a detached copy)**: left in place with a warning
  unless `--force` is given, since it may hold edits never brought back into the repo. With
  `--force`, the copy is deleted and replaced with a symlink.
- **Root not targeted by the manifest, entry is a symlink**: removed. A symlink holds no content,
  so removing it cannot lose work — this happens unconditionally, without needing `--force`.
- **Root not targeted by the manifest, entry is a real directory (a detached copy)**: left in place
  with a warning unless `--force` is given. With `--force`, it is deleted outright.

`--force` is required only to touch **real directories** (detached copies), whether replacing one
with a symlink or deleting an unlisted one. Symlinks are created and removed without `--force`
because they hold no content.

At the end of a run, `install.sh` prints counts of linked and removed skills and detached copies.

### `--dry-run`

Add `--dry-run` to see links to create, symlinks to remove, and copies to flag or replace without
writing anything. Use it after editing `install.conf` or to confirm roots still match the manifest.

## Availability vs. compatibility

Mapping a skill to a root makes it **visible** to that harness; `install.sh` only creates a symlink.
It does not check prerequisites such as tools, credentials, file layouts, or environment variables.
Check the skill's `SKILL.md` and referenced materials before relying on it; [skills.md](skills.md)
lists the skills and notes.

## Bootstrapping a fresh machine

```bash
cd agent-skills
cp install.conf.sample install.conf
# edit install.conf: remove or change roots for harnesses not installed on this machine,
# and for any skill you don't want linked anywhere, set its roots to "none"
./install.sh --dry-run   # review what would happen
./install.sh             # apply it
```

Re-run `./install.sh` (optionally with `--dry-run` first) any time `install.conf` changes, a skill
is added or removed, or you want to confirm the harness roots haven't drifted from the manifest.

## Example

Illustrative excerpt of a manifest line and the corresponding dry run, using a placeholder skill
name:

```text
# install.conf
<skill-name>   claude agents
```

```bash
$ ./install.sh --dry-run
link    /home/<user>/.claude/skills/<skill-name>
link    /home/<user>/.agents/skills/<skill-name>

linked: 2   removed: 0   detached copies: 0
```

Running the same command without `--dry-run` creates the two symlinks shown above.
