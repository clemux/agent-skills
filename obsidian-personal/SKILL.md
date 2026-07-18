---
name: obsidian-personal
description: >-
  Personal Obsidian vault adapter for this user's environment: vault identity and
  paths, standalone CLI targeting/preflight/retry behavior, verified commands,
  plugin-state locations, and routing to OAW and capture workflows. Use
  whenever interacting with the personal vault or running the `obsidian` CLI on
  this machine. Complements the generic `obsidian:obsidian-cli` plugin skill.
---

# Personal Obsidian vault

Supplements the `obsidian:obsidian-cli` plugin skill with facts specific to this
machine plus the command subset already verified here. Read that plugin skill for
full CLI syntax; this file is the machine-specific layer on top of it.

## Vault

- **Name:** `clemux-personal`.
- **Path:** `/home/clemux/Documents/notes/Notes/clemux-personal`
- **CLI:** the registered standalone CLI from the Obsidian 1.12.7+ installer. It is
  not the Electron application entrypoint; never add `--no-sandbox` or other Electron
  flags.
- **Targeting:** the CLI uses the vault containing the current working directory when
  applicable, otherwise the active vault. For automation, always put
  `vault=clemux-personal` before the command so cwd/focus cannot redirect an operation.
- **Working mode:** interact through the `obsidian` CLI rather than editing the
  vault's files directly, so Obsidian's index and open panes stay consistent.
- **Vault-relative paths:** paths passed to the CLI are relative to the vault root.
  Include the complete subfolder path, but do not prefix it with the vault name.

## User-facing note references

When reporting a durable vault note with a stable frontmatter ID, refer to it
primarily as `obs:<ID>`, not by filesystem path or Markdown link. Use a path only
when diagnosing storage or location issues, when the user asks for it, or when the
note has no stable ID.

## Template-first note creation

Before automating creation of a structured Obsidian note, check whether the vault
already has a suitable template and render that template instead of reconstructing
the note structure in an agent prompt or hard-coded prose. Templates conserve agent
tokens, keep structure user-editable, and make output consistent across agents.

Workflow-specific skills should name the exact template and command they use. Only
generate the structure directly when no suitable template exists or when the file is
explicitly machine-owned.

When reporting a captured issue, task, or idea, distinguish recording it in the
vault from implementing it in a code repository. Say "recorded as `obs:<ID>`" for
a vault-only action. Mention repository modification only when code or tracked
repository files were actually changed.

## Plugins

Don't hand-maintain a plugin list — read the live one from the vault config:

- **Enabled community plugins:** `<vault>/.obsidian/community-plugins.json` — a JSON
  array of plugin IDs.
- **Core plugins:** `<vault>/.obsidian/core-plugins.json` — a map of `id: bool`.

What matters when authoring notes (check the files rather than assuming):

- **`dataview`** (community) and **`bases`** (core) were enabled as of 2026-07-07, so
  Dataview query blocks and `.base` files render. **Mermaid renders natively** — no
  plugin needed.
- **`obsidian-kanban`** (community) was enabled as of 2026-07-07, so notes in the
  Kanban board format (`kanban-plugin: board` frontmatter) render as boards.

## Discovering commands

Run plain `obsidian help` (or `obsidian help <command>` for one command's options).
Don't pipe it through `grep`/`head`/etc. — a compound command trips an approval
prompt, while the bare command runs freely. The `help` output is authoritative and
always current, so prefer it over guessing a command exists.

## Connection preflight, retry, and concurrency

Before the first vault operation in a session, run:

```bash
obsidian version
obsidian vault=clemux-personal vault info=path
```

The first CLI call launches Obsidian when needed. If the vault preflight fails only
because the app is still starting or the CLI cannot yet connect, wait two seconds and
retry it once. Do not retry syntax, missing-file, permission, or validation errors;
surface those immediately. Do not add Electron flags as a connection workaround.

Independent read-only calls may run concurrently after preflight. This was verified
locally with simultaneous `vault info=path`, `vault info=name`, and `files ... total`
calls on 1.12.7. The CLI documentation makes no transactional guarantee for writes,
so serialize operations that touch the same note or jointly maintain an invariant,
and read back shell-sensitive or otherwise consequential writes.

## Workflow routing

- Use `obsidian-capture` for general side observations and reminders.
- Use `oaw feedback create` for agent-tooling friction; load the `oaw` skill for the
  current schema, provenance rules, and command options.
- Use `oaw` for `obs:`-prefixed references.

`base:query path="Agents/Agent feedback.base" view="Feedback triage" format=json`
returns rows headlessly on 1.12.7. `base:views` still acts on the active Base and has
no file/path parameter in current help, so use a known view name for automation.

## Verified commands

Keep `vault=clemux-personal` before the command in automation.

| Task        | Command                                               |
| ----------- | ----------------------------------------------------- |
| Create note | `obsidian vault=clemux-personal create path="Folder/Note.md" content="..."` |
| Read note   | `obsidian vault=clemux-personal read file="Note"`     |
| List folder | `obsidian vault=clemux-personal files folder="Folder"` |
| Delete note | `obsidian vault=clemux-personal delete file="Note"`   |
| Vault path  | `obsidian vault=clemux-personal vault info=path`       |
| Set property | `obsidian vault=clemux-personal property:set name=id value="NOTE-123" type=text path="Folder/Note.md"` |
| List frontmatter | `obsidian vault=clemux-personal properties path="Folder/Note.md" format=yaml` |

Notes on these:

- `create path=` auto-creates any missing folders in the path — there's no separate
  "make folder" command. Use `\n` for newlines inside `content=`. The standalone
  1.12.7 help does not list the old `silent` flag; omit `open` to avoid opening the
  new note. Add `overwrite` only when you deliberately mean to replace an existing
  file (otherwise it errors, which is the safe default).
- **Content-heavy notes** (code fences, quotes, frontmatter) mangle easily because the
  shell command-substitutes backticks inside double quotes. Wrap the whole `content=`
  value in **single quotes** and avoid apostrophes in the text — that makes backticks
  and inner `"double quotes"` literal. Real newlines inside the single-quoted string
  work fine (no need for `\n`). Then `read` it back to confirm it round-tripped.
- `delete` moves the note to Obsidian's trash (recoverable). Add `permanent` only when
  you truly want it gone.
- `vault info=path` returns the absolute path directly — no need for `eval`.
- `property:set` writes only frontmatter (body untouched) and **overwrites** the named
  property. For a list, use `type=list value="NOTE-123,W0"` — commas split into items.
  It may reflow an inline `tags: [...]` into block form (cosmetic; parses the same).
- To target a different vault, replace `vault=clemux-personal`; the vault parameter
  must remain before the command.
