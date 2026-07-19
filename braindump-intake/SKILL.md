---
name: braindump-intake
description: Turn a free-form user braindump into a reviewed sequence of atomic outcomes. Use when the user dumps multiple ideas, requests, follow-ups, or project changes and wants them decomposed, reviewed one at a time, optionally persisted through available tools or companion skills; when they ask for quick versus guided intake; or when a mobile user needs the complete ledger restated during interactive intake.
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
  reference needs validation.
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

Turn the dump into a numbered ledger:

- Keep one item per outcome; split independent features, repairs, research leads, and workflow
  improvements.
- Keep any explicitly requested final meta-item last. Insert later additions before it unless the
  user directs otherwise.
- Preserve completed items and verified identifiers when adding work.
- Treat repository surveys and other cheap context gathering as preparation, not automatically as
  durable work.
- Mirror the ledger in the harness plan or checklist when available.

Use these states consistently: `Pending`, `In progress`, `Confirmed`, `Persisted`, and `Blocked`.
When the user is on mobile or cannot see the plan UI, restate the **complete numbered ledger at every
transition**, including each state and verified identifier.

## Process one item at a time

Keep exactly one item `In progress` and repeat this loop.

1. **Preflight.** Validate supplied durable references through their owning workflow when one is
   available. Surface validation failures instead of guessing the target, and add a distinct repair
   item when the failure needs user action. Gather only cheap local evidence that improves the next
   decision, such as repository instructions or a named prior implementation; do not turn intake
   into an audit.

2. **Review.** In Quick mode, propose a short name and one-sentence outcome. In Guided mode, state
   the current understanding and ask one scope-changing decision question at a time. Do not turn
   optional implementation ideas into requirements. Explicitly confirm the item's mode and essential
   intent before any write.

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

Finish when every item is `Confirmed`, `Persisted`, `Blocked`, or deliberately skipped. Report the
final numbered ledger, persisted identifiers and outcomes, normalized handoffs, blockers, repairs,
and skipped items. Never report a planned filename or identifier as created.

Read [worked-example.md](references/worked-example.md) only when maintaining or forward-testing this
skill. It is synthetic and demonstrates reference repair, cheap context gathering, one-question
reviews, backend-neutral persistence, and a preserved final meta-item.
