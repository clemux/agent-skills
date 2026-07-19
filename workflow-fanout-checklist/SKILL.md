---
name: workflow-fanout-checklist
description: Gate a Claude Code ultracode / Workflow script through an approval checklist before it runs, catching agents that silently inherit an expensive model. Use when preparing, reviewing, or approving a Workflow script from an expensive main session (e.g. Fable, Opus), whenever a task is about to fan out into subagents, and before answering "should this be a workflow at all?".
---

# Workflow Fan-out Checklist

A workflow script decides how many agents run and on which model, and the approval dialog only
shows what the script declares. An `agent()` call that omits `model` inherits the main session's
model — so a script that reads like cheap parallel reader work can quietly bill fifteen agents at
the main session's rates, and nothing in the dialog says so. This skill is the gate.

Two rules make it work: the checklist is a file, not something you recall from memory, and the
verification is done by a *different* agent than the one that wrote the script. An author checking
their own script reliably confirms what they intended to write rather than what they wrote.

## Procedure

**1. Read the checklist.** `references/approval-checklist.md` in this skill directory. It is the
single source of truth for both you and the verifier — do not paraphrase it into the verifier's
prompt.

**2. Write the script and the justification together.** The message that asks for approval must
state lane, model choice, agent count, concurrency, stop condition, and why fan-out beats a single
cheaper agent or the main session here. If you cannot write that paragraph honestly, the answer to
"should this be a workflow?" is no — say so and do the work inline.

**3. Launch an independent verifier.** Save the script to a file first, then spawn a *separate*
agent against it. Pin the verifier's model explicitly: sufficiently capable to read a script
against a checklist, and cheaper than the model that authored the script. The verifier reads a
script and a checklist, which is not a job for the most expensive model available — this skill
would be hypocritical otherwise. From a Fable main session, for example, an Opus verifier is
appropriate; from an Opus session, Sonnet.

```
Agent(
  subagent_type: "general-purpose",
  model: "<explicitly pinned; cheaper than the authoring model>",
  description: "Verify workflow script",
  run_in_background: false,
  prompt: """
    Read the checklist at <abs path>/references/approval-checklist.md and the proposed
    workflow script at <abs path to script>. Also read the approval justification below.

    <paste the justification paragraph from step 2>

    Verify the script against the checklist. For every mandatory item, give a PASS or FAIL
    with the specific line or `agent()` call that decides it — quote it. Enumerate every
    `agent()` call and every `meta.phases` entry with the model each declares, and say
    explicitly where a model is absent. Then list advisory items that warrant a flag.

    Return a verdict: APPROVE, or REJECT with the failing mandatory items.
    Do not fix the script. Do not run it. You are verifying, not authoring.
  """
)
```

**4. Review the verdict, then decide.** The verifier reports; you decide. Do not accept a PASS whose
quoted evidence you cannot see, and do not overrule a FAIL by re-reading the script yourself — fix
the script and re-verify. Any mandatory FAIL means the script does not run as written.

**5. Present to the user.** Give them the verifier's verdict, the justification paragraph, and any
advisory flags with your reasoning, then ask for approval. Advisory flags do not block; they are
things the user should know they are consenting to.

## When to skip

A single `agent()` call for a bounded lookup is delegation, not fan-out — this skill is not a tax on
every subagent. It applies when a `Workflow` script is involved, or when a fan-out is large enough
that the model choice is a real cost decision.
