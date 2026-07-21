# obsidian-personal

`obsidian-personal` is a machine-specific adapter that supplies the identity, filesystem paths, CLI
targeting rules, verified command subset, plugin-state locations, and workflow routing for one
user's personal Obsidian vault. It is the layer on top of the generic `obsidian:obsidian-cli`
plugin skill that pins operations to a single configured vault and encodes locally verified
behavior of the standalone `obsidian` CLI. It is also this repository's one deliberate exception to
the publication boundary: the tracked [`SKILL.md`](../obsidian-personal/SKILL.md) hard-codes a
personal vault name, an absolute home-directory path, plugin-state file locations, private workflow
routes, and a named Base view, and it is explicitly allowlisted in the boundary check pending a
future template/private-instance split.

This page describes the skill without reproducing any of those private values. Where a specific
vault name, absolute path, or view name is needed, the canonical source is
[`SKILL.md`](../obsidian-personal/SKILL.md) itself.

## Status

Active. It is enabled on all three harness roots. The default mapping in
[`install.conf.sample`](../install.conf.sample) is:

```text
obsidian-personal       claude codex agents
```

That means a fresh local copy of `install.conf` links it into the Claude Code, Codex, and neutral
`~/.agents/skills` roots on every machine that starts from the sample — see [skills.md](skills.md)
for how the manifest drives installation. It is meant to be both model-triggered (its description
fires on personal-vault work) and user-invoked (the bundled `agents/openai.yaml` exposes a
`$obsidian-personal` default prompt). Because the sample enables it everywhere, any machine that is
not the configured personal environment must **opt out or replace the entire local configuration** —
not merely edit the two hard-coded strings the README mentions. See
[Compatibility and version notes](#compatibility-and-version-notes).

## Triggers

Per its description frontmatter, the skill fires whenever an agent is interacting with the personal
vault or running the `obsidian` CLI on this machine. It is scoped as a complement to the generic
`obsidian:obsidian-cli` plugin skill: that plugin skill covers full CLI syntax, and
`obsidian-personal` adds the machine-specific facts and the already-verified command subset on top.

The trigger is broad ("whenever interacting with the personal vault or running the `obsidian` CLI
on this machine"). It applies only to the single configured personal vault; generic Obsidian
guidance applies to any other vault. See [Read/write and safety boundaries](#readwrite-and-safety-boundaries).

## Prerequisites

- **Standalone `obsidian` CLI.** The skill targets the registered standalone CLI from the Obsidian
  1.12.7+ installer, not the Electron application entrypoint. It explicitly directs agents never to
  add `--no-sandbox` or other Electron flags.
- **A running or launchable Obsidian.** The first CLI call launches Obsidian when needed; the skill
  defines a preflight-and-retry sequence around app startup.
- **The generic `obsidian:obsidian-cli` plugin skill** for full CLI syntax. `obsidian-personal` is
  the machine-specific layer and defers syntax details to it.
- **Private workflow tooling for routing.** The skill routes some work to the `obsidian-capture`
  skill (general observations and reminders), agent-tooling friction to the `oaw feedback create`
  command, and `obs:`-prefixed reference resolution to the `oaw` skill generally — matching step 6
  of the workflow below. Those companion skills are their own dependencies; this adapter only
  routes to them.
- **The configured personal vault** must exist at the configured absolute path, and its
  `.obsidian` config directory must contain the community/core plugin-state files the skill reads.

No network access beyond the local CLI-to-app connection is described.

## Read/write and safety boundaries

Scope rule: everything below applies **only to the single configured personal vault**. For any
other vault, generic Obsidian guidance applies and this adapter's pinned targeting does not.

**Reads:**

- Vault notes via `read` and folder listings via `files`.
- Frontmatter/properties via `properties`.
- Live plugin state from the vault config directory: the enabled-community-plugins JSON array and
  the core-plugins map (paths given in [`SKILL.md`](../obsidian-personal/SKILL.md); the skill
  instructs agents to read these live rather than hand-maintain a plugin list).
- Base query rows headlessly through a named view via `base:query` (the specific Base path and view
  name are in the skill file).

**Writes (mutations):**

- Creates notes via `create` (auto-creates missing folders in the path).
- Sets frontmatter via `property:set`, which overwrites the named property and leaves the body
  untouched.

**Deletes:**

- `delete` moves a note to Obsidian's recoverable trash by default. The skill notes that the
  `permanent` flag is required to delete irrecoverably, and frames trash-by-default as the safe
  behavior.
- `create` errors rather than clobbering an existing file unless `overwrite` is passed; the skill
  frames the erroring default as safe.

**Launch:** the first CLI call may launch the Obsidian application.

**Actions needing explicit care per the skill:** using `permanent` on delete, using `overwrite` on
create, and any write touching a shared note or maintaining an invariant (the skill says to
serialize such writes and read them back, since the CLI documentation makes no transactional
guarantee for writes). Independent read-only calls may run concurrently after preflight.

The skill's working mode is to operate through the `obsidian` CLI rather than editing vault files
directly, so Obsidian's index and open panes stay consistent.

## Typical workflow

1. **Preflight** at the start of a session: run `obsidian version`, then a vault-scoped
   `vault info=path` call against the configured vault. If the vault preflight fails only because
   the app is still starting or the CLI cannot yet connect, wait two seconds and retry once. Syntax,
   missing-file, permission, and validation errors are surfaced immediately, not retried, and
   Electron flags are never added as a workaround.
2. **Target explicitly:** put the vault parameter (`vault=<configured-name>`) before every command
   in automation so the current working directory or window focus cannot redirect an operation.
   Vault-relative paths are relative to the vault root and are not prefixed with the vault name.
3. **Discover commands** with plain `obsidian help` or `obsidian help <command>`; the skill treats
   `help` output as authoritative and warns that piping it through `grep`/`head` trips an approval
   prompt.
4. **Prefer templates:** before automating creation of a structured note, check for an existing
   vault template and render it instead of reconstructing note structure in a prompt.
5. **Operate** using the verified command subset (create, read, list, delete, set/list properties,
   vault path), reading consequential writes back to confirm they round-tripped.
6. **Route** to the right workflow: `obsidian-capture` for side observations, `oaw feedback create`
   for agent-tooling friction, and `oaw` for `obs:`-prefixed references. Report durable notes with a
   stable ID as `obs:<ID>` rather than by path, and distinguish "recorded as `obs:<ID>`" (vault-only)
   from actual repository modification.

## Bundled resources

- [`agents/openai.yaml`](../obsidian-personal/agents/openai.yaml) — Codex/OpenAI interface metadata:
  a display name, short description, and a `$obsidian-personal` default prompt to target and operate
  on the personal vault with this machine's verified CLI behavior.

There are no `scripts/` or `references/` directories; all machine-specific facts, the verified
command table, and the operational rules live inline in [`SKILL.md`](../obsidian-personal/SKILL.md).

## Limitations

- **Not portable as written.** The skill is intentionally single-machine: it hard-codes the vault
  name and absolute path, the plugin-state file locations, the workflow routes, and a named Base
  view. Reuse on another machine requires replacing the whole local configuration, not editing two
  strings.
- **Deliberate privacy exception.** It is the only file in this repository allowlisted in the
  publication boundary check (see [`.publication-boundary-allowlist.json`](../.publication-boundary-allowlist.json),
  rules `personal-home` and `private-marker`), justified as a "legacy personal adapter pending its
  separately owned template and private-instance split."
- **No write transactionality.** The underlying CLI gives no transactional guarantee for writes, so
  concurrent or invariant-maintaining writes must be serialized and read back manually.
- **Content-heavy notes are fragile.** Code fences, quotes, and frontmatter in `content=` mangle
  because the shell command-substitutes backticks inside double quotes; the skill's mitigation is
  single-quoted content plus a read-back, and avoiding apostrophes in single-quoted text.
- **Depends on companion skills** (`obsidian:obsidian-cli`, `obsidian-capture`, `oaw`) that this
  adapter does not itself provide.
- **Base automation constraint.** `base:views` acts on the active Base and has no file/path
  parameter in current help, so automation must reference a known view name rather than discover
  views for an arbitrary Base.

## Compatibility and version notes

Version-sensitive claims below are drawn from the skill and are dated as the skill states them; a
maintainer should re-verify them against the installed environment.

- Standalone `obsidian` CLI from the **Obsidian 1.12.7+ installer**. Concurrency of independent
  read-only calls and headless `base:query` were verified on **1.12.7**. The `silent` flag is
  absent from 1.12.7 standalone help.
- `dataview` (community) and `bases` (core) were enabled **as of 2026-07-07**, so Dataview blocks
  and `.base` files render; `obsidian-kanban` (community) was enabled **as of 2026-07-07**. Mermaid
  renders natively with no plugin. The skill instructs agents to read the live plugin-state files
  rather than trust these snapshots.
- **README warning (updated 2026-07-21):** the repository README's privacy warning now states the
  full coupling — the skill hard-codes the vault name and path plus plugin-state locations,
  workflow routes, and a named Base view, so a real reuse means replacing the entire local
  configuration. Earlier README wording ("review and replace both values") understated this.
- **Intended future direction:** the allowlist entry documents a planned split into a separately
  owned portable **template** and a **private instance**, after which the portable core could be
  shared and the machine-specific values would live only in the private instance.

## Verification status

- **Automated:** `python3 scripts/check_publication_boundary.py` (repo pre-commit) enforces the
  boundary and treats this file as a reviewed exception via the allowlist; it does not verify the
  skill's runtime behavior. Shell-script linting does not apply here (no scripts are bundled).
- **Manually verified (per the skill, on 1.12.7):** the connection preflight/retry behavior, the
  verified command table (create/read/list/delete/property operations, vault path), concurrent
  read-only calls, and headless `base:query` through a named view.
- **Untested here:** whether the hard-coded vault name and absolute path resolve on any machine
  other than the configured personal environment (they will not by construction), and the current
  live plugin state beyond the dated 2026-07-07 snapshot.

## Example

Illustrative only — placeholder values, not a real capture. Replace `<vault>` with the configured
vault name from [`SKILL.md`](../obsidian-personal/SKILL.md).

```bash
# Session preflight (launches Obsidian if needed; retry once on a startup-only failure)
obsidian version
obsidian vault=<vault> vault info=path

# Create a note (folders auto-created; errors instead of clobbering unless overwrite is passed)
obsidian vault=<vault> create path="Folder/Note.md" content="First line\nSecond line"

# Read it back to confirm the write round-tripped
obsidian vault=<vault> read file="Folder/Note"

# Delete moves to recoverable trash unless 'permanent' is added
obsidian vault=<vault> delete file="Folder/Note"
```
