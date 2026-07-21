# workflow-fanout-checklist

Reviews Claude Code `Workflow` scripts before they run. It catches undeclared model inheritance and
unnecessarily large fan-out results before user approval.

## Workflow

1. Read the bundled approval checklist.
2. Write the workflow script and explain its models, agent count, concurrency, stop condition, and
   reason for using fan-out.
3. Have a separate, explicitly cheaper agent verify the saved script without running it.
4. Fix and recheck mandatory failures.
5. Show the verdict and advisory flags to the user before asking permission to run the workflow.

## Mandatory checks

- Every `agent()` call declares a model or documents deliberate inheritance.
- `meta.phases` agrees with the models used by its agents.
- The fan-out has a written justification.
- A separate cheaper agent performs the verification.
- The parent receives only the results it needs to act on.

The checklist also flags unbounded agent counts, concurrency, excessive output, weak verification,
missing cheaper alternatives, and loops without run limits or stop conditions.

See
[`references/approval-checklist.md`](../workflow-fanout-checklist/references/approval-checklist.md)
for the full checklist.

## Limitations

- Specific to Claude Code `Workflow`, `agent()`, and `meta.phases`.
- It reviews scripts but does not enforce that every workflow passes through it.
- Advisory findings do not block approval.
