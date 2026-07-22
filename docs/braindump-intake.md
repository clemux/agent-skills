# Braindump intake

Turns a multi-item message into a numbered ledger and reviews one outcome at a time.

## Workflow

1. Split the message into atomic outcomes.
2. Review one outcome at a time.
3. Confirm an outcome before persisting it externally.
4. Record only identifiers returned or verified by the persistence mechanism.
5. Finish with the complete ledger, including blocked, skipped, and needs-clarification items.

If no persistence mechanism is available, return a normalized handoff instead of claiming a
write.

## States

`Pending`, `In progress`, `Confirmed`, `Persisted`, `Blocked`, `Skipped`, and
`Needs clarification`.

Only persistence failures use `Blocked`; missing inputs for the underlying work do not prevent the
outcome from being reviewed and confirmed.

`Needs clarification` is the terminal state for an item whose essential intent cannot be confirmed
when no further question can be asked, such as one-shot intake. The final report records its open
question, and nothing is persisted for it.
