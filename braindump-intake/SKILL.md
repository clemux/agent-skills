---
name: braindump-intake
description: Turn a free-form user braindump into a reviewed sequence of atomic Obsidian captures or OAW project tasks. Use when the user dumps multiple ideas, requests, follow-ups, or project changes and wants them decomposed, reviewed one at a time, and recorded durably; when they ask for quick versus guided intake; or when a mobile user needs the complete plan restated during interactive intake.
---

# Braindump Intake

Convert a raw dump into durable work through a visible ledger and one-at-a-time confirmation. Finish with every successfully created or repaired `obs:` reference.

## Load companion workflows only when needed

- Read `oaw` before resolving or repairing an `obs:` reference, or before creating or promoting an OAW task.
- Read `obsidian-capture` only before writing a capture.

Let those skills own current schemas and commands; keep this skill focused on intake decisions.

## Initialize the intake

Ask one question unless the user already chose a mode:

> Which detail level should I use by default?
> 1. **Quick** — confirm a short name and one-sentence goal, record it, and move on.
> 2. **Guided** — review one decision question at a time and record richer requirements.

Allow per-item overrides. A default mode is not permission to write unreviewed items.

Turn the dump into a numbered ledger:

- Keep one item per durable outcome; split independent features, repairs, and workflow improvements.
- Keep any explicitly requested final meta-task last. Insert later additions before it unless directed otherwise.
- Preserve completed items and their `obs:` IDs when adding work.
- Treat repository surveys and other cheap context gathering as preparation, not automatically as durable work.
- Mirror the ledger in the harness plan/checklist when available.

When the user is on mobile or cannot see the plan UI, restate the **complete numbered ledger at every transition**, with `Done`, `In progress`, or `Pending` and any created IDs.

## Process one item at a time

Keep exactly one item `In progress` and repeat this loop.

1. **Preflight.** Resolve every supplied `obs:` reference. Surface resolver failures verbatim, never guess the target, and add a distinct repair item. Gather only cheap local evidence that improves the next decision, such as the project index, repository instructions, current model, or named prior implementation; do not turn intake into an audit.

2. **Review.** In Quick mode, propose a short name and one-sentence outcome. In Guided mode, state the current understanding and ask one scope-changing decision question at a time. Do not turn optional implementation ideas into requirements. Before any write, explicitly confirm the item's chosen mode and essential intent.

3. **Route and write.** Choose by outcome:
   - For a broken-reference repair, have the user identify and confirm the intended existing note, update it in place, rerun resolution, and attach the now-resolving existing ID. Do not create a note solely to represent the repair.
   - For an actionable change with a known project, create an OAW task. Promote an existing actionable project capture through OAW rather than creating an unrelated task.
   - For an idea, observation, lead, reminder, or unresolved possibility, create an Obsidian capture.

   Load the relevant companion workflow before writing. Explain the proposed artifact when the route is ambiguous, and never batch-write unconfirmed items.

4. **Update the ledger.** Attach only an ID returned or verified after a successful write, then mark that item `Done`. Keep failures unresolved. Add newly mentioned work without losing completed history or displacing a required final meta-task. Apply the mobile restatement rule, then continue.

## Close the intake

Finish only when every confirmed durable item has a verified `obs:` reference or an explicit blocker. Report the final numbered ledger, each created ID and outcome, repaired references, and unresolved or deliberately skipped items. Never report planned filenames or IDs as created.

Read [worked-example.md](references/worked-example.md) only when maintaining or forward-testing this skill. It captures the originating alias repair, shallow repository survey, one-question reviews, and preserved final workflow task.
