# retro

Runs a guided end-of-session retrospective: it reads the session transcript for evidence, discusses
a triaged list of observations with the user one item at a time, converts confirmed follow-ups into
owned tasks or captures as the discussion happens, and writes a durable retrospective note through a
pluggable storage backend.

## Status

Active. Default harness mapping in [`install.conf.sample`](../install.conf.sample):

```
retro                   claude codex agents
```

That targets all three roots (Claude Code, Codex, and the neutral `~/.agents/skills` root).

The skill is both model-triggered and user-invoked. It has an explicit invocation per harness
(`/retro` in Claude Code, `$retro` in Codex — see [`retro/SKILL.md`](../retro/SKILL.md), "Harness
adapters"), and its description frontmatter also lists natural-language phrasings it should
recognize without an explicit command.

## Triggers

Per the `description` frontmatter in [`retro/SKILL.md`](../retro/SKILL.md), the skill fires on:

- Explicit invocation: `/retro` (Claude Code) or `$retro` (Codex).
- Session-ending signals: "let's do a retrospective", "let's wrap up", "what did we learn", "before
  we close this out", or other signs that a working session is ending and its lessons should be
  preserved.
- Requests to review how a session went, capture friction hit during the session, or turn loose
  end-of-session observations into durable tasks — even without the word "retrospective".

## Prerequisites

- A readable session transcript for the current harness. Claude Code: a JSONL file under
  `~/.claude/projects/<cwd-with-slashes-as-dashes>/<session-id>.jsonl` (including nested subagent
  transcripts). Codex: a rollout JSONL under `~/.codex/sessions/`. `jq` is used in the documented
  Claude Code token-accounting commands.
- A session identifier from the environment: `CLAUDE_CODE_SESSION_ID` (or `CLAUDE_SESSION_ID`) for
  Claude Code, `CODEX_THREAD_ID` for Codex.
- A checklist tool to hold the session-local agenda: Claude Code's `TaskCreate`/`TaskUpdate`/
  `TaskGet`/`TaskList` (or the older `TodoWrite`, whichever the running build offers), or Codex's
  `update_plan`.
- Optionally, a **retro backend adapter** skill — a skill whose description names itself as a
  backend/adapter for `retro` (for example an Obsidian- or issue-tracker-backed adapter). Without
  one, the skill uses its own plain-Markdown fallback (see below); no adapter is required to run a
  retro.
- Optionally, a session-analysis skill (e.g. `session-inspect` or `session-report`) — if installed,
  the skill prefers it over hand-deriving token/tool-call statistics from the transcript.

## Read/write and safety boundaries

**Reads:** the session transcript (and nested subagent transcripts), the harness's checklist-tool
state, and — when present — the installed retro-backend adapter's own skill file for its command
mappings.

**Writes, human-facing and durable:**

- The retrospective note itself (fallback path documented below, or the adapter's note-creation
  workflow).
- Follow-up items converted to tasks or captures, via the backend (adapter or fallback).
- Session-local checklist entries in the harness's checklist tool — not durable, discarded with the
  session.

**Safety boundaries the skill states explicitly:**

- **No invented evidence.** If the transcript, token counts, or session ID cannot be read/resolved,
  the skill is required to say so plainly rather than estimate or fabricate numbers.
- **Confirmation before creating durable follow-ups.** A follow-up is only converted into a task or
  capture "the moment the user confirms an item implies work" during the one-item-at-a-time
  discussion — it is not created speculatively from the evidence-gathering pass alone.
- **Confirmation before writing an untraceable note.** If the session identifier is unavailable, the
  skill must say so and get the user's explicit OK before writing the note without it.
- **Destination confirmation when ambiguous.** In the fallback path, if the retro note's destination
  project is unclear, the skill asks once rather than guessing or scattering notes.
- **No structured/multiple-choice prompting for retro items.** The skill explicitly avoids
  `AskUserQuestion`-style tools for discussing items, because pre-baked options narrow the user's
  answer to what the agent already anticipated.
- **Execution of substantive follow-ups happens in a fresh session**, not inline in the retro (see
  Typical workflow below) — the retro session only records the follow-up and hands off a launch
  command.

## Typical workflow

The full sequence is in [`retro/SKILL.md`](../retro/SKILL.md), "Workflow" (steps 1-5). Summary:

1. **Gather evidence.** Read the transcript (and subagent transcripts) for outcome, what worked,
   friction, token waste, decisions (made and deferred), reusable workflows, do-not-forget items,
   and user corrections. Triage down to the handful of items worth the user's attention before
   speaking.
2. **Build the agenda as a visible checklist.** Every triaged item goes into the harness's checklist
   tool as one pending entry — session-local planning state, not a durable artifact — so a long
   discussion cannot silently drop later items.
3. **Discuss, one item at a time.** State the observation, cite evidence (a tool call, a transcript
   moment, a token count), say why it matters, then stop and let the user respond. Follow tangents;
   drop dismissed items without arguing; add items the user raises that were missed; update the
   checklist after each one.
4. **Convert follow-ups into owned work, inline.** As soon as the user confirms an item implies
   work, it gets a home immediately (task, capture, or a `## Follow-ups` entry in the fallback) —
   not batched to the end. A correction to how the agent should work is flagged as belonging in
   agent memory or a skill, not just a retro bullet.

   Recording (creating the task, filing the capture, adding the link) happens inline, in the retro
   session. **Executing** a follow-up that has grown into its own piece of work does not: the skill
   names it, offers a fork ("that's a fresh-session job — I've captured it as `<task-id>`"), and
   defers doing it. At the end of the retro it offers a launch command pointed at the repo the work
   actually lives in:

   ```bash
   # Claude Code
   cd <repo> && claude "Work on <task-id>. Read the task, then implement it."

   # Codex
   cd <repo> && codex "Work on <task-id>. Read the task, then implement it."
   ```

   The stated exception is a fix too small to have its own shape (a one-line correction, a link, a
   typo) — those are done inline rather than forked.
5. **Write the retrospective note**, through the backend. Summary paragraph first, then dated/titled
   sections (observations, decisions, follow-ups, artifacts), follow-ups and artifacts referenced by
   their identifiers, the session identifier(s) recorded for traceability, and the note linked
   bidirectionally to any tasks it spawned where the backend supports links. Finally the skill is
   required to **verify** — confirm the note exists at its expected location with the session
   identifier populated (re-reading the file, in the fallback) — because a note that silently failed
   to write is not visible from the conversation alone.

## Adapter discovery and the no-adapter fallback

Before step 4, the skill checks the available-skills list for a **retro backend adapter**: a skill
whose description names itself as a backend or adapter for `retro`. If one is found, the skill reads
it and defers to its command mappings for steps 4 (converting follow-ups) and 5 (writing the note)
instead of the fallback. Backend authors: the seam a compatible adapter must fill is the three
responsibilities listed under "Backends" in [`retro/SKILL.md`](../retro/SKILL.md) — own follow-up
work with a stable identifier, hold the retrospective note with the session identifier(s) recorded,
and verify the note exists after writing. Read that section directly rather than relying on this
summary.

**If no adapter is installed**, the skill degrades to a plain-Markdown fallback and says so
explicitly rather than silently picking a storage location. The fallback:

- **Destination:** `retrospectives/<YYYY-MM-DD>-<short-slug>.md` in the current project, unless the
  user names a different home. If the current project is ambiguous, the skill asks once rather than
  guessing.
- **Frontmatter:** `date`, `harness`, `session-id`, `status: draft`.
- **Sections:** `## Summary`, `## Observations`, `## Decisions`, `## Follow-ups`, `## Artifacts`.
- **Follow-ups:** rendered as a checklist under `## Follow-ups`. If the project has an issue tracker
  the user actually uses (e.g. GitHub issues), the skill offers to file follow-ups there instead of
  the checklist.

## Bundled resources

The skill package contains a single file, [`retro/SKILL.md`](../retro/SKILL.md) — no `scripts/`,
`references/`, or `agents/` subdirectories exist for this skill. All workflow detail, the fallback
schema, and the harness adapter mappings live in that one file.

## Limitations

- **Harness coverage is explicit and partial.** Claude Code and Codex are fully mapped (invocation,
  checklist tool, session-ID variable, transcript location). Other harnesses are documented as "not
  yet mapped" — the skill runs with whatever subset of the workflow is available and asks the
  running agent to record the new mapping in the skill file afterward, rather than failing closed.
- **No checklist tool:** the skill falls back to a scratch markdown file re-read between items,
  rather than a proper checklist.
- **No readable transcript:** the skill is required to say so explicitly and run from in-context
  evidence only, flagging that friction from subagents and compacted context becomes invisible in
  that mode.
- **Deliberately excludes structured-choice UI** (`AskUserQuestion` and equivalents) for item
  discussion, even where using it would be faster, because it narrows answers to anticipated
  options.
- **Token-usage introspection is Claude-Code-specific and schema-fragile.** The documented `jq`
  commands assume the current `message.usage` shape of the transcript JSONL; the skill file itself
  notes this can change between builds and recommends treating the commands as a starting point.
- The skill does not itself define what counts as a "retro backend adapter" beyond a description
  match — a malformed or unrelated skill whose description happens to claim adapter status for
  `retro` would be picked up as-is; the skill does not describe a validation step beyond reading it.

## Compatibility and version notes

- The Claude Code checklist-tool guidance (`TaskCreate`/`TaskUpdate`/`TaskGet`/`TaskList`, possibly
  deferred and requiring a `ToolSearch` schema load, versus the older `TodoWrite`) is
  build-dependent; verify which tool set the running Claude Code build exposes before assuming
  either name (as of 2026-07-21).
- The Claude Code transcript path and per-record `message.usage` token-accounting fields are treated
  in the skill file itself as subject to change between builds; re-check the JSONL shape against the
  documented `jq` commands before trusting summed totals (as of 2026-07-21).
- The Codex session-ID environment variable (`CODEX_THREAD_ID`) and rollout `total_token_usage`
  record shape are Codex-CLI-version-specific and unverified against a specific Codex release in
  this review (as of 2026-07-21).
- "Other harnesses" mapping is explicitly empty as of this writing; any harness beyond Claude Code
  and Codex runs the skill's degraded, self-discovering fallback path.

## Verification status

No automated tests, CI checks, or eval harness for this skill were found in the skill's own
directory or referenced from it. This page's description of the workflow is based on a manual read
of [`retro/SKILL.md`](../retro/SKILL.md) in full; the workflow itself (transcript reads, checklist
tool calls, note writes) was not executed or independently reproduced as part of writing this page.
