---
name: braindump-intake
description: Turn a free-form user braindump into a reviewed sequence of atomic outcomes. Use whenever the user dumps multiple ideas, requests, follow-ups, or project changes in one message and wants them decomposed, reviewed one at a time, or persisted through available tools or companion skills — including when they say "brain dump", "here's everything on my mind", paste a messy mixed list of tasks and ideas, or ask for quick versus guided intake. Also use when a mobile user asks you to restate the full ledger mid-intake.
---

# Braindump Intake

Convert a raw dump into a visible ledger of atomic outcomes and review one item at a time. Use the
skill without a persistence backend when the user only wants a clarified plan. When durable records
are requested, hand confirmed items to the applicable persistence tool or companion skill and accept
only identifiers it verifies.

## Keep persistence separate

Own the intake conversation, item ordering, confirmation state, and final ledger. Let the selected
persistence mechanism own destinations, schemas, commands, reference resolution, and identifiers.

- Load a persistence workflow only when a confirmed item is ready to write or an existing durable
  reference (for example a ticket or note identifier the user supplies) needs validation.
- When more than one destination or artifact type is plausible, explain the meaningful choice and
  confirm it with the user.
- When no persistence mechanism is available, return a normalized handoff instead of inventing a
  write, filename, or identifier.
- Do not bake backend-specific paths, taxonomies, commands, or identifier formats into this skill.
  Use concrete values supplied by the user or selected persistence workflow during the intake
  process.

## Initialize the intake

Ask one question unless the user already chose a mode:

> Which detail level should I use by default?
> 1. **Quick** — confirm a short name and one-sentence outcome, then move on.
> 2. **Guided** — review one decision question at a time and capture richer requirements.

Allow per-item overrides. A default mode is not permission to persist unreviewed items.

When the user cannot or will not answer questions — a one-shot request, "no questions, just process
this" — use Quick mode. Treat the request as confirmation only for outcomes, writes, and destinations
it states unambiguously. An item whose essential intent stays ambiguous ends as `Needs
clarification`: record the open question for the final report instead of persisting a guess.

Turn the dump into a numbered ledger:

- Keep one item per outcome; split independent features, repairs, research leads, and workflow
  improvements.
- Keep any explicitly requested final meta-item (for example "and lastly, capture improvements to
  this intake process itself") last. Insert later additions before it unless the user directs
  otherwise.
- Preserve completed items and verified identifiers when adding work.
- Treat repository surveys and other cheap context gathering as preparation, not automatically as
  durable work.
- Mirror the ledger in the agent's own plan or todo UI when available.

Use these states consistently: `Pending`, `In progress`, `Confirmed`, `Persisted`, `Blocked`,
`Skipped`, and `Needs clarification`.
Intake records outcomes; it does not execute them. Reserve `Blocked` for failed writes and missing
persistence capability — an item whose underlying work merely lacks inputs (data, access, a
decision) is still reviewable, so confirm it and note what the work will need.
Use `Needs clarification` when an item's essential intent cannot be confirmed and no further
question can be asked — the request was one-shot or the user deferred the decision. It exists
because such an item fits no other terminal state honestly: it was never confirmed, no write
failed, and the user never declined it. Record the specific unresolved question and persist
nothing for the item.
Whenever the ledger is shown, label every numbered line with its own current state — a collective
claim like "all four persisted" hides per-item drift. Keep the shown states consistent with the
surrounding prose: an item the same reply reviews or acts on is already `In progress`, not
`Pending`.
When the user is on mobile or cannot see the plan UI, restate the **complete numbered ledger at every
transition**, including each state and verified identifier.

## Process one item at a time

New items start `Pending`. Keep exactly one item `In progress` and repeat this loop.

1. **Preflight.** Validate supplied durable references through their owning workflow when one is
   available. Surface validation failures instead of guessing the target, and add a distinct repair
   item when the failure needs user action. Gather only cheap local evidence that improves the next
   decision, such as repository instructions or a named prior implementation; do not turn intake
   into an audit.

2. **Review.** In Quick mode, propose a short name and one-sentence outcome. In Guided mode, state
   the current understanding and ask one scope-changing decision question at a time. Do not turn
   optional implementation ideas into requirements. Confirm the item's mode and essential intent
   before any write, applying the one-shot confirmation rule above when applicable. When the user
   declines to pursue an item, mark it `Skipped`, note the reason for the final report, and move on.
   When no question can be asked and the item's essential intent stays ambiguous, mark it `Needs
   clarification` with the specific open question and move on.

3. **Route or hand off.** If persistence was not requested, mark the reviewed item `Confirmed`. If
   persistence was requested:

   - Route an actionable change to the available task or work-item mechanism.
   - Route an idea, observation, lead, reminder, or unresolved possibility to the available capture
     or note mechanism.
   - Repair an existing record in place when the owning workflow supports it; do not create a new
     record solely to disguise a broken reference.
   - When no suitable mechanism is available, provide a handoff containing the confirmed title,
     outcome, requirements, relevant context, and intended artifact type, then mark the item
     `Blocked` with the missing capability.

   Never batch-write unconfirmed items.

4. **Update the ledger.** Attach only an identifier returned or verified after a successful write,
   then mark that item `Persisted`. Keep failed writes `Blocked` and unpersisted reviewed items
   `Confirmed`. Add newly mentioned work without losing completed history or displacing a required
   final meta-item. Apply the mobile restatement rule, then continue.

## Close the intake

Finish when every item is `Confirmed`, `Persisted`, `Blocked`, `Skipped`, or `Needs clarification`.
Report the final numbered ledger, persisted identifiers and outcomes, normalized handoffs, blockers,
repairs, skipped items, and the open question for each item needing clarification. Never report a
planned filename or identifier as created.

Read [worked-example.md](references/worked-example.md) when unsure how the interaction should flow,
or when maintaining or forward-testing this skill. It is synthetic — never reuse its names or
identifiers — and demonstrates reference repair, cheap context gathering, one-question reviews,
backend-neutral persistence, and a preserved final meta-item.
