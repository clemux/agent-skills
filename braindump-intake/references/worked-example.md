# Worked example: synthetic mobile intake

Use this fictional scenario to calibrate or forward-test the interaction shape. Do not treat its
names, identifiers, or outcomes as content for future braindumps.

## Intake

A mobile user supplies four outcomes for a fictional dashboard: allow people to reorder cards,
notify them when an export is ready, locate an earlier notification example, and finally record an
improvement to the intake process itself. Because the plan UI is hidden, the agent restates the
complete numbered ledger at every transition.

The supplied `PROJECT-DEMO` reference cannot be validated by the available persistence workflow.
The agent surfaces the failure instead of guessing and inserts a distinct repair item before the
required final meta-item. After the user identifies the intended existing project record, the
persistence workflow repairs it in place, validates it, and returns the existing identifier.

A shallow survey of two explicitly fictional fixtures, `sample-dashboard` and
`notification-example`, finds reusable notification behavior. This evidence informs later questions
but does not become a durable item by itself.

The agent reviews one outcome at a time and asks one decision question per turn. The user confirms
that card ordering is shared across devices before the selected task mechanism returns `WORK-201`.
Separately, the user confirms the notification channel and failure behavior before it returns
`WORK-202`. The reusable example is recorded through the selected capture mechanism as `NOTE-044`.

The requested process-improvement item remains last despite the inserted repair. Before writing it,
the agent summarizes the session lessons and confirms the outcome. The task mechanism then returns
`WORK-203`.

## Calibration checks

- Validate supplied references before related writes and make failures visible repair work.
- Keep cheap context gathering distinct from durable outcomes.
- Review and confirm one atomic item at a time.
- Keep artifact selection and identifier creation in the persistence workflow.
- Preserve completed work and an explicitly final meta-item when the dump grows.
- Restate the full ledger when the user cannot see the plan UI.
- Report only identifiers returned or verified successfully.
