# Workflow approval checklist

Applies to any Claude Code ultracode / `Workflow` script authored from an expensive main session.

## Mandatory — reject the script if any item fails

- **Model declaration.** Every `agent()` call sets `model`. No call inherits the main session's
  model by omission. A deliberate inherit is allowed only when a comment on the call says so and why.
- **Review surface.** Every `meta.phases` entry declares `model`, and it matches the model actually
  used by that phase's `agent()` calls. This is what the approval dialog shows the user; a phase
  that omits `model` hides the routing.
- **Fan-out justification.** The proposal states, in the message that asks for approval: lane, model
  choice, agent count, concurrency, stop condition, and why workflow fan-out beats a single cheaper
  agent or the main session for this task.
- **Independent verification.** A separate verifier agent — explicitly pinned to a model that is
  sufficiently capable and cheaper than the authoring model — has checked the script against this
  file, and the main agent is reviewing that verdict rather than substituting its own unassisted read.

## Advisory — flag with a reason, may still pass

- **Purpose.** The user-visible result is named, not just the mechanism.
- **Agent count.** Each agent has an independent input slice and a bounded output.
- **Concurrency.** Parallelism is not hiding runaway token use.
- **Output contract.** Workers return compact structured results or write artifacts; large content is
  not injected into the parent repeatedly.
- **Verification scope.** The verifier checks claims, joins, generated files, or source coverage as
  applicable, and reports any failed mandatory item.
- **Cheaper alternative.** A single cheaper agent or the main session was rejected for a concrete
  reason, per phase.
- **Run budget.** Any repeated or looped delegation (retry loops, loop-until-dry, refire cycles)
  states a hard run cap up front plus a no-progress rule: two consecutive runs without measurable
  progress toward the stop condition means stop and escalate, not re-fire. The cap is a consent
  point — raising it needs a fresh user decision.

## The failure this exists to catch

A previous workflow described Sonnet-style reader work but omitted `model` on its `agent()`
calls, so fifteen agents inherited the far more expensive main-session model. The approval dialog
did not surface the mismatch because `meta.phases` omitted model fields too — which is why the
review surface is its own mandatory item.
