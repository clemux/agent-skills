---
name: retro
description: Run a guided end-of-session retrospective — inventory the session for insights, friction, follow-ups, decisions, token waste, and reusable workflows; discuss them one at a time with the user; convert confirmed follow-ups into owned tasks; and write a durable retrospective note through a pluggable backend. Use this whenever the user invokes `/retro` or `$retro`, says "let's do a retrospective", "let's wrap up", "what did we learn", "before we close this out", or otherwise signals that a working session is ending and its lessons should be preserved. Also use when the user wants to review how a session went, capture friction they hit, or turn loose end-of-session observations into durable tasks — even if they never say the word "retrospective".
---

# retro

A retrospective turns a session that is about to be forgotten into durable, owned artifacts:
lessons the user will actually re-read, and follow-up work that has a home. The session transcript
disappears; the notes and tasks it produces do not.

This skill runs in Claude Code (`/retro`), Codex (`$retro`), and other harnesses. The core workflow
below is harness-independent; the **Harness adapters** section at the end says how to do each
harness-specific step. Where the retro's outputs *go* — tasks, captures, the retro note itself —
is delegated to a **backend** (see the next section), so the same workflow works whether the user
keeps notes in a personal knowledge vault, a repo directory, or nothing fancier than markdown.

## Backends: where the durable artifacts live

The workflow needs a backend that can do three things:

1. **Own follow-up work** — create a task or capture with a stable, referenceable identifier.
2. **Hold the retrospective note** — create a durable note that records the session identifier(s),
   so the retro can be traced back to its transcript.
3. **Verify** — confirm after writing that the note actually exists where it should.

**Discovery:** before converting follow-ups (step 4), check the available-skills list for a
**retro backend adapter** — a skill whose description names itself as a backend or adapter for the
`retro` skill. If one is installed, read it and use its command mappings for steps 4 and 5 instead
of the fallback below. The adapter owns the specifics: which CLI to call, which note schema to
follow, how to link and verify.

**Fallback (no adapter installed):** degrade to plain markdown, and say so.

- The retro note goes to `retrospectives/<YYYY-MM-DD>-<short-slug>.md` in the current project,
  unless the user names a different home. Ask once if unsure; don't scatter notes silently.
- Use frontmatter for traceability (`date`, `harness`, `session-id`, `status: draft`) and the
  section skeleton `## Summary`, `## Observations`, `## Decisions`, `## Follow-ups`,
  `## Artifacts`.
- Follow-ups become a checklist under `## Follow-ups`. If the project has an issue tracker the
  user actually uses (e.g. GitHub issues), offer to file them there instead — a tracked issue is a
  better owner than a checklist.

## What makes a retro good (read this before starting)

**Evidence beats memory.** Your in-context recollection of the session is unreliable — long sessions
get summarized, and subagent work never enters your context at all. Read the transcript. A retro
built from "what I remember happening" reproduces your own blind spots; a retro built from the
transcript surfaces the things you didn't notice at the time, which is the entire point.

**One item at a time, in free-form prose.** Do not dump a list of twelve observations and ask "which
of these are real?" — that offloads the sorting work onto the user, which is what they were trying
to avoid. Raise one item, say what you observed and why you think it matters, and let them respond
in their own words.

Do **not** use a structured-question or multiple-choice tool for this (Claude Code's
`AskUserQuestion`, Codex's equivalent), even though it is available and looks convenient.
Retrospective items are open-ended. The value is in what the user says that you did not anticipate,
and offering pre-baked options narrows their answer to the options you already thought of. This is a
deliberate constraint, not an oversight.

**Nothing durable without ownership.** A follow-up that becomes a bullet in a retro note and nothing
else is a follow-up that dies. If an item implies work, it becomes a task or a capture with a real
identifier, and the retro links to it.

**Degrade explicitly; never invent evidence.** If you cannot read the transcript, cannot get token
counts, or cannot resolve the session ID, say so plainly and work from what you can observe. Do not
estimate token waste. A retro that fabricates numbers is worse than one that says "unavailable".

## Workflow

### 1. Gather evidence

Read the session transcript (see **Harness adapters**). You are looking for things the user would
not think to tell you, across these categories:

- **Outcome** — what actually got done, versus what the session set out to do.
- **What worked** — approaches worth repeating. Be specific; "collaboration went well" is noise.
- **Friction** — tool failures, wrong turns, repeated retries, permission prompts, misunderstandings,
  things that took five steps and should have taken one.
- **Token waste** — expensive tool calls, files read in full when a slice would do, work redone after
  a compaction, subagents that returned nothing useful. Measure it; don't guess.
- **Decisions** — choices made that a future session would otherwise re-litigate, *including* ones the
  user made in passing. Also: decisions that were *deferred* and are still open.
- **Reusable workflows** — command sequences or patterns that worked and should become a skill, a
  script, or a documented convention.
- **Do-not-forget** — anything raised mid-session and parked.
- **Corrections** — places where the user corrected you. These are the highest-signal items in the
  whole transcript, because they encode a preference you got wrong and will get wrong again.

Then **triage before you speak**. Not everything you find is worth the user's attention; a retro that
walks them through fourteen trivia items is a retro they will not run again. Aim for the handful of
items that would change how the next session goes.

### 2. Build the agenda as a visible checklist

Put the triaged items into the harness's checklist tool (see adapters) — one entry per item, all
pending. This is session-local planning state, not a durable artifact.

The checklist exists so that items survive a long discussion: retros branch, the user goes deep on
item two, and without a durable agenda items five through eight quietly vanish. Mark each item
complete only after the user has actually responded to it.

### 3. Discuss, one item at a time

For each item: state what you observed, cite the evidence (a tool call, a transcript moment, a token
count), say why you think it matters, and stop. Let the user respond.

Follow where they go. If an item opens a bigger topic, chase it — the tangent is often the real
retrospective. If they dismiss an item, drop it without arguing; they have context you don't.
Update the checklist and move to the next item.

Listen for items *they* raise that you missed, and add those to the checklist too.

### 4. Convert follow-ups into owned work — during the discussion, not after

The moment the user confirms an item implies work, give it a home using the backend (adapter
commands if one is installed; the fallback otherwise). Doing this inline (rather than batching at
the end) means the decision is fresh and the retro note can link to a real identifier.

- **Actionable work with a clear owner** → a task in the backend's task system.
- **An idea, lead, or "maybe later"** → a capture, if the backend has a capture mechanism; a
  `## Follow-ups` entry marked as an idea otherwise.
- **A gap in the agent tooling itself** → a task in the relevant tooling project, not a vague note.
- **A correction to how you should work** → this belongs in agent memory or a skill, not just a retro
  bullet. Say so, and offer to make the change.

If work happened this session that no task owns, create or promote a task for it before closing the
retro — a retrospective should not be the only record of substantive work.

#### Record the item here; execute it somewhere else

There is a hard line between *recording* an item and *doing* it.

**Recording belongs inline** — creating the task, filing the capture, adding the link. It is cheap,
and the note comes out good precisely because you write it with the evidence still in hand.

**Executing belongs in a fresh session.** The moment an item turns into "now let's build the thing",
it is a new piece of work with its own shape, and the retro context is close to the worst context to
do it in: it is full of the previous task's detritus, none of which helps, and all of which gets
re-read on every turn. Worse, the retro stalls — the remaining agenda items sit pending while the
detour runs long, and items the user never got to are items the retro failed to surface.

So when the user starts pulling on an item, name it and offer the fork:

> That's a fresh-session job — I've captured it as `<task-id>`. Let's finish the agenda and
> you can start it clean.

The handoff is free, because step 4 already produced the artifact a cold session needs: the task
note. Offer the launch command at the *end* of the retro, once the agenda is done — pointing at the
repo the work actually lives in, not the one the retro happened to run in:

```bash
# Claude Code
cd <repo> && claude "Work on <task-id>. Read the task, then implement it."

# Codex
cd <repo> && codex "Work on <task-id>. Read the task, then implement it."
```

Both CLIs take a positional prompt and open an interactive session with it already loaded, so the
user lands in a fresh context that is briefed and ready.

The exception is a fix small enough to be indistinguishable from recording it — a one-line
correction, a link, a typo. Forking for those costs more than doing them. The test is whether the
work has its own shape: if you would need to explain it to a fresh session, it belongs in one.

### 5. Write the retrospective note

Write the note through the backend: with an adapter, follow its note-creation workflow; without
one, use the fallback path and skeleton from **Backends** above. Either way:

- **Summary first** — one paragraph: what this session was.
- **Sections as dated, titled blocks** — observations ("What worked", "Friction and lessons"),
  decisions, follow-ups, artifacts.
- **Reference follow-ups and artifacts by their identifiers** so they resolve later, and link the
  retro to the tasks it spawned (bidirectionally, if the backend supports links).
- **Record the session identifier(s)** in the note so it can be traced back to the transcript.
  Do not silently write an untraceable note — if the session ID is unavailable, say so and get the
  user's explicit OK.

Finally, **verify** — confirm the note exists at its expected home with the session identifier
populated (the adapter says how; in the fallback, re-read the file). A retro note that didn't
actually get written is the one failure mode the user cannot see from the conversation.

Report back with the retro note's identifier or path and the identifiers of everything it spawned.

## Harness adapters

### Claude Code

- **Invocation:** `/retro`.
- **Checklist tool:** `TaskCreate` / `TaskUpdate` / `TaskGet` / `TaskList` (states `pending`,
  `in_progress`, `completed`). These may be *deferred* — load their schemas with `ToolSearch` before
  the first call. Older builds expose `TodoWrite` instead, with the same three states; use whichever
  the harness actually offers rather than assuming.
- **Session ID:** `CLAUDE_CODE_SESSION_ID` (or `CLAUDE_SESSION_ID`) in the Bash environment.
- **Transcript:** `~/.claude/projects/<cwd-with-slashes-as-dashes>/<session-id>.jsonl`. Subagent
  transcripts are nested under the same project directory — read them, since subagent friction is
  invisible from the main conversation.
- **Token usage:** each assistant record carries `message.usage`. Sum it:

  ```bash
  jq -s '[.[].message.usage // empty] | {
    input:      (map(.input_tokens // 0)             | add),
    output:     (map(.output_tokens // 0)            | add),
    cache_read: (map(.cache_read_input_tokens // 0)  | add),
    cache_write:(map(.cache_creation_input_tokens//0)| add)
  }' "$TRANSCRIPT"
  ```

  Tool-call frequency (a good proxy for where the session spent its effort):

  ```bash
  jq -r '.message.content[]? | select(.type=="tool_use") | .name' "$TRANSCRIPT" | sort | uniq -c | sort -rn
  ```

  Treat these as a starting point — explore the JSONL rather than trusting a fixed schema, since it
  changes between builds. If a session-analysis skill is installed (e.g. `session-inspect` or
  `session-report`), prefer it over re-deriving the numbers by hand.

### Codex

- **Invocation:** `$retro`.
- **Checklist tool:** `update_plan` (states `pending`, `in_progress`, `completed`).
- **Session ID:** `CODEX_THREAD_ID`.
- **Transcript:** rollout JSONL under `~/.codex/sessions/`. Cumulative token usage lives in the
  rollout's `total_token_usage` records; if a session-analysis skill is installed (e.g.
  `session-inspect`), prefer it over hand-parsing the rollout.

### Other harnesses

Not yet mapped. Before running a retro in an unmapped harness, work out its invocation, checklist
tool, session-ID variable, and transcript location; run the retro with whatever subset is available;
and record the mapping in this skill so the next session doesn't rediscover it.

If a harness has **no checklist tool**, keep the agenda in a scratch markdown file and re-read it
between items — the failure mode this guards against (losing pending items in a long discussion) is
real regardless of harness. If it has **no readable transcript**, say so explicitly and run the retro
from in-context evidence only, flagging that friction from subagents and compacted context is
invisible.

## Related

- A **retro backend adapter** skill, if installed — owns where tasks, captures, and the retro note
  live. This skill defines the workflow; the adapter defines the storage.
