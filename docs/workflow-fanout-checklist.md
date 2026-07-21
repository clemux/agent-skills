# workflow-fanout-checklist

Gates a Claude Code ultracode / `Workflow` script through an approval checklist before launch, so
an `agent()` call that silently inherits the main session's expensive model is caught first.

## Summary

A `Workflow` approval dialog shows only declared configuration. An `agent()` call without `model`
inherits the main session's model, so apparent cheap parallel work can bill many agents at that
rate. The author provides a fan-out justification, then a separate, cheaper-model agent verifies
the script against [`references/approval-checklist.md`](../workflow-fanout-checklist/references/approval-checklist.md)
before user approval.

## Status

Active. Default harness mapping, quoted from
[`install.conf.sample`](../install.conf.sample):

```
workflow-fanout-checklist claude
```

Claude Code only: `Workflow`, `agent()`, and `meta.phases` are Claude Code constructs.

The description frontmatter triggers it before fan-out or when deciding whether a workflow is
appropriate. It can also be explicitly invoked when preparing or reviewing a workflow script.

## Triggers

Per the `description` frontmatter, the skill should be used when:

- preparing, reviewing, or approving a `Workflow` script from an expensive main session (the
  description gives Fable and Opus as examples of "expensive"),
- a task is about to fan out into subagents, or
- deciding "should this be a workflow at all?"

A single `agent()` call for a bounded lookup is ordinary delegation, not fan-out; see "When to
skip" in `SKILL.md`. Use this skill for `Workflow` scripts or fan-out where model choice is a real
cost decision.

## Prerequisites

- Claude Code, with the ability to author and launch `Workflow` scripts and spawn subagents
  (`Agent(...)` calls with a pinned `model`).
- No external tools, network access, or authentication are required — the skill only reads its own
  bundled checklist file and the script under review.
- No other skill is a hard dependency.

## Read/write and safety boundaries

- **Reads:** `references/approval-checklist.md` (the skill's own file — must not be paraphrased
  into the verifier's prompt, per `SKILL.md` step 1) and the proposed workflow script (saved to a
  file before verification, per step 3).
- **Writes:** none. Output is a verdict and justification paragraph.
- **External/human-facing actions:** the skill's entire purpose is a human-approval gate — step 5
  requires presenting the verifier's verdict, justification, and advisory flags to the user before
  the workflow script runs.
- **Mutating actions needing explicit approval:** running the `Workflow` script itself is the
  consequential action being gated; the skill does not run it (the verifier prompt explicitly says
  "Do not run it"). A run budget/no-progress rule is advisory (not mandatory) but is framed as its
  own consent point: raising an approved run cap "needs a fresh user decision" (see the checklist's
  "Run budget" item).

## Typical workflow

1. Read the checklist at `references/approval-checklist.md` — the single source of truth for both
   the author and the verifier.
2. Write the script and, in the same approval-request message, its justification: lane, model
   choice, agent count, concurrency, stop condition, and why fan-out beats a single cheaper agent
   or the main session. If it cannot be written honestly, do the work inline.
3. Save the script to a file, then launch an independent verifier agent — a separate agent
   instance, with `model` explicitly pinned to something cheaper than the model that authored the
   script. The verifier reads the checklist and the script, gives PASS/FAIL per mandatory item with
   quoted evidence, enumerates every `agent()` call and `meta.phases` entry with its declared model,
   lists advisory flags, and returns APPROVE or REJECT. The verifier does not fix or run the script.
4. Review the verdict. Do not accept PASS without visible quoted evidence. Do not overrule FAIL by
   re-reading: fix the script and re-verify (see Limitations).
5. Present the user with the verifier's verdict, the justification paragraph, and any advisory
   flags with reasoning, then ask for approval. Advisory flags do not block; they inform consent.

### Mandatory vs. advisory checklist items

Full text: [`../workflow-fanout-checklist/references/approval-checklist.md`](../workflow-fanout-checklist/references/approval-checklist.md).

Mandatory (any failure rejects the script): model declaration on every `agent()` call (a
deliberate inherit passes only with a comment on the call saying so and why), a review surface
where every `meta.phases` entry declares a model matching what its `agent()` calls actually use,
the fan-out justification paragraph, independent verification by a separate cheaper-pinned agent,
and a parent-facing return that carries only what the parent acts on (counts, final synthesis,
artifact paths/IDs — bulk per-item results pass only with a comment on the return saying why the
parent needs them).

Advisory (flagged with a reason, does not block): purpose is user-visible, agent count is bounded
per-agent, concurrency isn't hiding runaway token use, output contract keeps large content out of
the parent, verification scope matches the script's actual claims/joins/files, a cheaper
alternative was considered per phase, and any repeated/looped delegation states a hard run cap plus
a no-progress stop rule.

## Bundled resources

- `SKILL.md` — the five-step procedure, verifier prompt template, and "when to skip" scope note.
  No `scripts/` or `agents/` directory is bundled.
- `references/approval-checklist.md` — the mandatory/advisory checklist itself, plus a "failure
  this exists to catch" section with two illustrated past incidents that motivated the mandatory
  model-declaration and parent-facing-return items.

## Limitations

- Claude Code only; the checklist's language (`agent()`, `meta.phases`, `Workflow`) does not map to
  other harnesses' delegation mechanisms.
- The skill does not automatically detect or enforce use; no check confirms a `Workflow` script
  passed through it before running.
- "Re-verify" after a fix is not spelled out with more precision than "fix the script and
  re-verify" (step 4) — whether that means re-running the full verifier prompt or a lighter check
  is left to the operator's judgment.
- The advisory/mandatory split means several real cost risks (agent count, concurrency, run budget)
  can still result in an APPROVE verdict; they only require a flag and a reason, not a fix.
- No worked example or sample script ships with the skill; the only workflow scripts referenced are
  the two anonymized past-incident summaries in the checklist file.

## Compatibility and version notes

As of 2026-07-21, this page is checked against `workflow-fanout-checklist/SKILL.md` and
`workflow-fanout-checklist/references/approval-checklist.md`. `agent()` syntax, `meta.phases`, and
example model tiers (Fable, Opus, Sonnet) are version-specific. Treat
[`../workflow-fanout-checklist/references/approval-checklist.md`](../workflow-fanout-checklist/references/approval-checklist.md)
and [`../workflow-fanout-checklist/SKILL.md`](../workflow-fanout-checklist/SKILL.md) as the
canonical source for exact syntax and model-tier names.

## Verification status

Checked against `SKILL.md` and `references/approval-checklist.md`. No automated test, eval, or CI
check was found. The independent verifier checks governed workflow scripts, not this documentation.

## Example

Illustrative only — placeholder paths and content, not a real capture.

```
1. Author (main session, model: Fable) writes a Workflow script at
   /path/to/project/scripts/fanout-review.workflow and a justification:

   "Lane: code-review. Model: Sonnet for all 12 reader agents (script sets model on
   every agent() call). Agent count: 12, one per changed file. Concurrency: 4 at a
   time. Stop condition: all 12 return or one hard-fails. Why fan-out: 12 independent
   file reviews with no shared state; a single agent serializing them would take
   ~4x longer for the same token cost."

2. Author saves the script, then launches a verifier:

   Agent(model: "Sonnet", description: "Verify workflow script", prompt: """
     Read references/approval-checklist.md and the script above the justification
     text. Verify against the checklist, quote evidence, return APPROVE or REJECT.
   """)

3. Verifier returns: APPROVE. All mandatory items PASS (model declared on all 12
   agent() calls; meta.phases declares "sonnet" matching; justification present;
   this verification is itself the independent check; return carries only a
   pass/fail count and synthesis). Advisory: none flagged.

4. Main session presents the verdict, justification, and "no advisory flags" to
   the user and asks for approval before running the script.
```

## See also

- [skills.md](skills.md) — the full skill inventory this page is part of.
