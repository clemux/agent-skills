---
name: retro
description: Run a guided end-of-session retrospective — inventory the session for insights, friction, follow-ups, decisions, token waste, and reusable workflows; discuss them one at a time with the user; convert confirmed follow-ups into owned vault tasks; and write a draft retrospective note via the OAW workflow. Use this whenever the user invokes `/retro` or `$retro`, says "let's do a retrospective", "let's wrap up", "what did we learn", "before we close this out", or otherwise signals that a working session is ending and its lessons should be preserved. Also use when the user wants to review how a session went, capture friction they hit, or turn loose end-of-session observations into durable tasks — even if they never say the word "retrospective".
---

# retro

A retrospective turns a session that is about to be forgotten into durable, owned artifacts:
lessons the user will actually re-read, and follow-up work that has a home. The session transcript
disappears; the vault does not.

This skill runs in Claude Code (`/retro`), Codex (`$retro`), and other harnesses. The source of truth
is `~/dev/agent-skills/retro/`, symlinked into each harness's skill directory. The core workflow
below is harness-independent; the **Harness adapters** section at the end says how to do each
harness-specific step.

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
ID, and the retro links to it.

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
pending. This is session-local planning state, not a vault surface.

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

The moment the user confirms an item implies work, give it a home. Doing this inline (rather than
batching at the end) means the decision is fresh and the retro note can link to a real ID.

- **Actionable work with a clear owner** → `oaw task create --project <alias> --title "..."`
  (`--status todo` if it's genuinely next-up; default `backlog` otherwise).
- **An idea, lead, or "maybe later"** → a capture, via the `obsidian-capture` skill.
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

> That's a fresh-session job — I've captured it as `obs:XXX-TSK-thing`. Let's finish the agenda and
> you can start it clean.

The handoff is free, because step 4 already produced the artifact a cold session needs: the task
note. Offer the launch command at the *end* of the retro, once the agenda is done — pointing at the
repo the work actually lives in, not the one the retro happened to run in:

```bash
# Claude Code
cd <repo> && claude "Work on obs:XXX-TSK-thing. Resolve it with the oaw skill, read the task note, and implement it."

# Codex
cd <repo> && codex "Work on obs:XXX-TSK-thing. Resolve it with the oaw skill, read the task note, and implement it."
```

Both CLIs take a positional prompt and open an interactive session with it already loaded, so the
user lands in a fresh context that is briefed and ready.

The exception is a fix small enough to be indistinguishable from recording it — a one-line
correction, a link, a typo. Forking for those costs more than doing them. The test is whether the
work has its own shape: if you would need to explain it to a fresh session, it belongs in one.

### 5. Write the retrospective note

Create the draft:

```bash
oaw retro create --title "<short descriptive title>" --summary "<one paragraph: what this session was>"
```

This writes `Agents/Retrospectives/<date> <title>.md` with frontmatter (`type`, `status: draft`,
`provider`, `session-ids`, `id`, `aliases`) and a `## Summary` section. It resolves the session ID
from the harness environment itself — do not pass one, and do not use
`--allow-missing-session-id` unless the user explicitly accepts an untraceable note.

Then append each section as a dated block:

```bash
oaw note observe <RETRO-ID> --section Observations --title "What worked"          --body "- ..."
oaw note observe <RETRO-ID> --section Observations --title "Friction and lessons" --body "- ..."
oaw note observe <RETRO-ID> --section Decisions    --title "<what was decided>"   --body "- ..."
oaw note observe <RETRO-ID> --section Follow-ups   --title "Owned work"           --body "- obs:XXX-TSK-... — ..."
oaw note observe <RETRO-ID> --section Artifacts    --title "Durable outputs"      --body "- obs:... — ..."
```

Reference follow-ups and artifacts by `obs:` ID so they resolve later. Link the retro to the tasks it
spawned with `oaw link ensure-bidirectional ... --write`.

Finally, **verify** — `oaw resolve --meta <RETRO-ID>` to confirm it exists with `session-ids`
populated, and confirm it appears in `Agents/Retrospectives.base#Recent`. A retro note that didn't
actually get written is the one failure mode the user cannot see from the conversation.

Report back with the retro's `obs:` ID and the IDs of everything it spawned.

## Harness adapters

### Claude Code

- **Invocation:** `/retro`.
- **Checklist tool:** `TaskCreate` / `TaskUpdate` / `TaskGet` / `TaskList` (states `pending`,
  `in_progress`, `completed`). These may be *deferred* — load their schemas with `ToolSearch` before
  the first call. Older builds expose `TodoWrite` instead, with the same three states; use whichever
  the harness actually offers rather than assuming.
- **Session ID:** `CLAUDE_CODE_SESSION_ID` (or `CLAUDE_SESSION_ID`) in the Bash environment. `oaw`
  reads it for you.
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
  changes between builds. The `session-report` skill, if installed, already builds a fuller usage
  report (tokens, cache, subagents, skills, expensive prompts) from these files; prefer it over
  re-deriving the numbers by hand.

### Codex

- **Invocation:** `$retro`.
- **Checklist tool:** `update_plan` (states `pending`, `in_progress`, `completed`).
- **Session ID:** `CODEX_THREAD_ID`. `oaw` reads it for you.
- **Transcript:** rollout JSONL under `~/.codex/sessions/`. `oaw session lookup <thread-id> --verbose`
  reports timestamps, duration, turn count, and cumulative token usage from
  `total_token_usage` — use it instead of hand-parsing the rollout.

### Other harnesses (OMP and beyond)

Not yet mapped. Before running a retro in an unmapped harness, work out its invocation, checklist
tool, session-ID variable, and transcript location; run the retro with whatever subset is available;
and record the mapping in `obs:AGT-TSK-retro-skill` so the next session doesn't rediscover it.

If a harness has **no checklist tool**, keep the agenda in a scratch markdown file and re-read it
between items — the failure mode this guards against (losing pending items in a long discussion) is
real regardless of harness. If it has **no readable transcript**, say so explicitly and run the retro
from in-context evidence only, flagging that friction from subagents and compacted context is
invisible.

## Related

- `obs:AGT-TSK-retro-skill` — the task this skill implements; record harness mappings there.
- `obs:AGT-TSK-session-retrospectives` — the habit this supports.
- The `oaw` skill — task lifecycle, note intake, retro creation, session snapshots.
- The `obsidian-capture` skill — for parking ideas that aren't yet actionable work.
