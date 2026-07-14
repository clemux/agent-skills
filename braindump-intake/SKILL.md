---
name: braindump-intake
description: Turn a free-form user braindump into a reviewed sequence of atomic Obsidian captures or OAW project tasks. Use when the user dumps multiple ideas, requests, follow-ups, or project changes and wants them decomposed, reviewed one at a time, and recorded durably; when they ask for quick versus guided intake; or when a mobile user needs the complete plan restated during an interactive intake.
---

# Braindump Intake

Convert a raw dump into durable work without making the user design the filing system. Keep an explicit intake ledger, confirm each item before writing it, and end with a complete list of created `obs:` references.

## Required companion workflows

Read and follow the local `oaw` skill for reference resolution and project-task lifecycle. Read and follow `obsidian-capture` before creating captures. Those skills own the current schemas and write commands; do not duplicate or guess them here.

## 1. Establish the intake contract

Ask one question before processing the dump:

> Which detail level should I use by default?
> 1. **Quick** — confirm a short name and one-sentence goal, record it, and move on.
> 2. **Guided** — review one decision question at a time and record richer requirements.

Let the user override the mode for any item. Treat the answer as a default, not permission to write every item immediately. Do not write an item until the user has confirmed both its chosen detail level and its essential intent.

If the user already specified a mode, acknowledge it and continue without asking again.

## 2. Build the intake ledger

Decompose the dump into numbered atomic items before reviewing any one item deeply:

- Keep one item per durable outcome. Split feature work, metadata repair, research leads, and workflow improvements when they can be completed independently.
- Preserve an explicitly requested final meta-task as the final item. Insert later additions before it unless the user says otherwise.
- Record cheap context gathering as part of the relevant item or as a non-durable preparation item; do not create a vault note merely for looking around.
- Add new dump items without deleting, renumbering away, or reopening completed work. Keep already-created `obs:` IDs attached to their items.
- Use the harness plan/checklist tool when available. The ledger remains the semantic source of truth even if the tool only shows short labels.

When the user is on mobile or says they cannot see the plan UI, restate the **complete numbered ledger** at every transition: after decomposition, after a decision, after a write, and before the next question. Show each item as `Done`, `In progress`, or `Pending`, including created `obs:` IDs.

## 3. Preflight references and cheap context

Before reviewing or writing an item:

1. Resolve every supplied `obs:` reference with `oaw resolve`.
2. If a reference fails, quote the resolver failure, do not infer its target, and add an explicit repair item to the ledger. Repair only after the user confirms the intended target and the repair's detail level.
3. Gather cheap local evidence that can remove obvious questions: inspect the relevant project index, repository instructions, directory names, current data model, or a named prior implementation.
4. Summarize only the evidence that changes the next decision. Do not turn intake into an exhaustive repository audit.

Reference resolution and context gathering do not authorize a durable write.

## 4. Review one item at a time

Set exactly one item to `In progress`. Do not ask about later items while it is unresolved.

### Quick mode

Propose:

- a short task/capture name; and
- one sentence stating the desired outcome.

Ask the user to confirm or adjust those two fields. Ask an additional question only when the destination, actionability, or meaning is genuinely ambiguous. After confirmation, write the item and move on.

### Guided mode

State the current understanding, then ask **one decision question at a time**. Prefer the question that most changes scope, ownership, or acceptance behavior. Incorporate the answer, restate the ledger when required, and ask the next question only if the item still lacks essential intent.

Before writing, summarize the agreed outcome and key requirements and obtain confirmation. Avoid converting optional implementation ideas into requirements unless the user chose them.

## 5. Choose the durable artifact

Choose based on actionability, not on how long the note would be:

- Create an **OAW task** when the user wants a concrete change or deliverable, the owning project is known, and the outcome is actionable.
- Create an **Obsidian capture** when the item is an idea, observation, lead, reminder, or unresolved possibility that still needs later triage.
- If an actionable request starts from an existing project capture, use OAW's capture-promotion workflow rather than creating an unrelated task.
- Use the owning project's intentional lifecycle. Default unscheduled work to `backlog`; use `todo` only when the user deliberately selects near-term work.

Tell the user which artifact type you propose and why when the choice is not obvious. Then use the companion skill's current command/schema to write it. Never batch-write unconfirmed items.

## 6. Maintain the ledger after each write

After a successful write:

1. Attach the returned durable `obs:` ID to the item.
2. Mark only that item `Done`.
3. Preserve failures as unresolved items; do not report a planned ID as created.
4. Incorporate any newly mentioned work as a new atomic item, keeping the completed history and any required final meta-task intact.
5. Restate the complete ledger when the mobile rule applies, then start the next pending item.

## 7. Close the intake

Finish only when every confirmed durable item has either a successfully created `obs:` reference or an explicitly reported blocker. Report:

- the final numbered ledger;
- every created `obs:` ID with a one-line outcome;
- any repaired reference and what changed;
- any unresolved or deliberately skipped item.

Do not claim completion from proposed filenames, planned IDs, or partial writes.

## Worked example

Read [worked-example.md](references/worked-example.md) when calibrating the workflow or changing this skill. It records the originating mobile intake: a broken project alias became its own repair item, a quick repository survey found a reusable notification example, feature decisions were reviewed one question at a time, and the explicitly requested process-improvement item remained last.
