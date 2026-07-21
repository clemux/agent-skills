# retro

Runs a guided end-of-session retrospective: reads the transcript for evidence, discusses triaged
observations one at a time, converts confirmed follow-ups into tasks or captures, and writes a
durable note through a pluggable backend.

## Status

Active. Default harness mapping in [`install.conf.sample`](../install.conf.sample):

```
retro                   claude codex agents
```

Targets Claude Code, Codex, and the neutral `~/.agents/skills` root.

Invoke it as `/retro` in Claude Code or `$retro` in Codex; its description frontmatter also covers
natural-language requests.

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
  backend/adapter for `retro` (for example, an Obsidian- or issue-tracker-backed adapter). Without
  one, it uses the plain-Markdown fallback.
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
- **Confirmation before creating durable follow-ups.** Create a task or capture only when the user
  confirms that an item implies work; do not create one from evidence gathering alone.
- **Confirmation before writing an untraceable note.** If the session identifier is unavailable, the
  skill must say so and get the user's explicit OK before writing the note without it.
- **Destination confirmation when ambiguous.** In the fallback path, if the retro note's destination
  project is unclear, the skill asks once rather than guessing or scattering notes.
- **No structured/multiple-choice prompting for retro items.** The skill explicitly avoids
  `AskUserQuestion`-style tools for discussing items, because pre-baked options narrow the user's
  answer to what the agent already anticipated.
- **Substantive follow-ups run in a fresh session.** The retro records the follow-up and provides a
  launch command.

## Typical workflow

See [`retro/SKILL.md`](../retro/SKILL.md), "Workflow" (steps 1–5).

1. **Gather evidence.** Read the transcript (and subagent transcripts) for outcome, what worked,
   friction, token waste, decisions (made and deferred), reusable workflows, do-not-forget items,
   and user corrections. Triage to items worth the user's attention.
2. **Build the agenda as a visible checklist.** Every triaged item goes into the harness's checklist
   tool as one pending entry. This is session-local planning state, not a durable artifact.
3. **Discuss, one item at a time.** State the observation, cite evidence (a tool call, a transcript
   moment, a token count), say why it matters, then let the user respond. Follow tangents, drop
   dismissed items, add missed items the user raises, and update the checklist after each one.
4. **Convert follow-ups into owned work, inline.** As soon as the user confirms an item implies
   work, give it a home immediately (task, capture, or a `## Follow-ups` entry in the fallback).
   Corrections to agent behavior belong in agent memory or a skill, not only the retro.

   Recording (creating the task, filing the capture, adding the link) happens inline, in the retro
   session. Do not execute a substantive follow-up inline: name it, offer a fork ("that's a
   fresh-session job — I've captured it as `<task-id>`"), and defer it. End with a launch command
   for the repository where the work lives:

   ```bash
   # Claude Code
   cd <repo> && claude "Work on <task-id>. Read the task, then implement it."

   # Codex
   cd <repo> && codex "Work on <task-id>. Read the task, then implement it."
   ```

   Small fixes (a one-line correction, link, or typo) are done inline.
5. **Write the retrospective note**, through the backend. Summary paragraph first, then dated/titled
   sections (observations, decisions, follow-ups, artifacts), follow-ups and artifacts referenced by
   their identifiers, session identifier(s) for traceability, and bidirectional links to spawned
   tasks where supported. Verify that the note exists at its expected location and has the session
   identifier (re-read the file in the fallback).

## Adapter discovery and the no-adapter fallback

Before step 4, check available skills for a **retro backend adapter**, defined by its description.
If found, read it and use its command mappings for steps 4 and 5. A compatible adapter must own
follow-up work with a stable identifier, store the retrospective note with session identifier(s),
and verify the note exists after writing; see "Backends" in [`retro/SKILL.md`](../retro/SKILL.md).

**If no adapter is installed**, state that and use this plain-Markdown fallback:

- **Destination:** `retrospectives/<YYYY-MM-DD>-<short-slug>.md` in the current project, unless the
  user names a different home. If the current project is ambiguous, the skill asks once rather than
  guessing.
- **Frontmatter:** `date`, `harness`, `session-id`, `status: draft`.
- **Sections:** `## Summary`, `## Observations`, `## Decisions`, `## Follow-ups`, `## Artifacts`.
- **Follow-ups:** rendered as a checklist under `## Follow-ups`. If the project has an issue tracker
  the user actually uses (e.g. GitHub issues), the skill offers to file follow-ups there instead of
  the checklist.

## Bundled resources

The package contains only [`retro/SKILL.md`](../retro/SKILL.md); it has no `scripts/`,
`references/`, or `agents/` directories.

## Limitations

- **Harness coverage is explicit and partial.** Claude Code and Codex are fully mapped (invocation,
  checklist tool, session-ID variable, transcript location). Other harnesses are "not yet mapped";
  run the available subset and record the mapping in the skill file afterward.
- **No checklist tool:** the skill falls back to a scratch markdown file re-read between items,
  rather than a proper checklist.
- **No readable transcript:** state this and use in-context evidence only; subagent and compacted
  context friction is unavailable.
- **Deliberately excludes structured-choice UI** (`AskUserQuestion` and equivalents) for item
  discussion, even where using it would be faster, because it narrows answers to anticipated
  options.
- **Token-usage introspection is Claude-Code-specific and schema-fragile.** The documented `jq`
  commands assume the current `message.usage` shape of the transcript JSONL; the skill file itself
  notes this can change between builds and recommends treating the commands as a starting point.
- Adapter discovery trusts a description match; a malformed or unrelated claimed adapter may be
  selected, with no validation beyond reading it.

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

No automated tests, CI checks, or eval harness were found. This page was checked against
[`retro/SKILL.md`](../retro/SKILL.md); the transcript reads, checklist calls, and note writes were
not executed or independently reproduced.
