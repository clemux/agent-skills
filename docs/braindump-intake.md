# Braindump intake

Turns a multi-item message into a numbered ledger and reviews one outcome at a time.

## Workflow

1. Split the message into atomic outcomes.
2. Review one outcome at a time.
3. Confirm an outcome before persisting it externally.
4. Record only identifiers returned or verified by the persistence mechanism.
5. Finish with the complete ledger, including blocked and skipped items.

If no persistence mechanism is available, return a normalized handoff instead of claiming a
write.

## States

`Pending`, `In progress`, `Confirmed`, `Persisted`, `Blocked`, and `Skipped`.

Only persistence failures use `Blocked`; missing inputs for the underlying work do not prevent the
outcome from being reviewed and confirmed.
