# workflow-fanout-checklist

Gates a Claude Code ultracode / `Workflow` script through an approval checklist before it runs, so
that an `agent()` call which silently inherits the main session's (expensive) model gets caught
before launch rather than discovered on the bill.

## Summary

A `Workflow` script decides how many agents run and on which model, but the approval dialog only
shows what the script declares. An `agent()` call that omits `model` inherits the main session's
model — a script that reads like cheap parallel reader work can quietly bill many agents at the
main session's rate, with nothing in the dialog surfacing that. This skill supplies a checklist
(`references/approval-checklist.md`) and a two-step process: the author writes a fan-out
justification, then a separate, explicitly cheaper-model agent verifies the script against the
checklist before the main session presents it to the user for approval.

## Status

Active. Default harness mapping, quoted from
[`install.conf.sample`](../install.conf.sample):

```
workflow-fanout-checklist claude
```

Claude Code only — the skill's own text (mandatory checklist item, procedure step 3) is framed
entirely around Claude Code's `Workflow` scripts, `agent()` calls, and `meta.phases`, which are
Claude-Code-specific constructs. It has no Codex or cross-harness applicability documented.

This skill is meant to be model-triggered: the description frontmatter is written to fire
proactively ("whenever a task is about to fan out into subagents, and before answering 'should
this be a workflow at all?'") rather than requiring an explicit user invocation, though a user can
also invoke it directly when preparing or reviewing a workflow script.

## Triggers

Per the `description` frontmatter, the skill should be used when:

- preparing, reviewing, or approving a `Workflow` script from an expensive main session (the
  description gives Fable and Opus as examples of "expensive"),
- a task is about to fan out into subagents, or
- deciding "should this be a workflow at all?"

Explicitly out of scope (see "When to skip" in `SKILL.md`): a single `agent()` call for a bounded
lookup is ordinary delegation, not fan-out, and does not require this checklist. The skill applies
when a `Workflow` script is involved, or when a fan-out is large enough that model choice is a
real cost decision.

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
- **Writes:** none, to the repository or filesystem. The skill's output is a verdict and a
  justification paragraph, not file mutation.
- **External/human-facing actions:** the skill's entire purpose is a human-approval gate — step 5
  requires presenting the verifier's verdict, the justification paragraph, and any advisory flags
  to the user and asking for approval before the workflow script runs. No workflow script this
  skill governs should execute without that explicit user approval.
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
   or the main session. If that paragraph cannot be written honestly, the answer is to skip the
   workflow and do the work inline.
3. Save the script to a file, then launch an independent verifier agent — a separate agent
   instance, with `model` explicitly pinned to something cheaper than the model that authored the
   script. The verifier reads the checklist and the script, gives PASS/FAIL per mandatory item with
   quoted evidence, enumerates every `agent()` call and `meta.phases` entry with its declared model,
   lists advisory flags, and returns APPROVE or REJECT. The verifier does not fix or run the script.
4. The main agent reviews the verdict and decides. A PASS without visible quoted evidence should
   not be accepted; a FAIL should not be overruled by the main agent's own re-read — instead fix the
   script and re-verify (see Limitations for what "re-verify" does and does not require).
5. Present the user with the verifier's verdict, the justification paragraph, and any advisory
   flags with reasoning, then ask for approval. Advisory flags do not block; they inform consent.

### Mandatory vs. advisory checklist items

Full text: [`../workflow-fanout-checklist/references/approval-checklist.md`](../workflow-fanout-checklist/references/approval-checklist.md).

Mandatory (any failure rejects the script): model declaration on every `agent()` call, a review
surface where every `meta.phases` entry declares a model matching what its `agent()` calls
actually use, the fan-out justification paragraph, independent verification by a separate
cheaper-pinned agent, and a parent-facing return that carries only what the parent acts on (counts,
final synthesis, artifact paths/IDs — not bulk per-item results).

Advisory (flagged with a reason, does not block): purpose is user-visible, agent count is bounded
per-agent, concurrency isn't hiding runaway token use, output contract keeps large content out of
the parent, verification scope matches the script's actual claims/joins/files, a cheaper
alternative was considered per phase, and any repeated/looped delegation states a hard run cap plus
a no-progress stop rule.

## Bundled resources

- `SKILL.md` — the procedure described above (5 steps) plus the verifier prompt template and the
  "when to skip" scope note. No `scripts/` or `agents/` directory is bundled; the skill is
  process-only, no executable helper exists to run or check for.
- `references/approval-checklist.md` — the mandatory/advisory checklist itself, plus a "failure
  this exists to catch" section with two illustrated past incidents that motivated the mandatory
  model-declaration and parent-facing-return items.

## Limitations

- Claude Code only; the checklist's language (`agent()`, `meta.phases`, `Workflow`) does not map to
  other harnesses' delegation mechanisms.
- The skill does not itself detect or enforce anything — it is a documented procedure the main
  agent must choose to follow. There is no automated check that a `Workflow` script was actually
  routed through this skill before running.
- "Re-verify" after a fix is not spelled out with more precision than "fix the script and
  re-verify" (step 4) — whether that means re-running the full verifier prompt or a lighter check
  is left to the operator's judgment.
- The advisory/mandatory split means several real cost risks (agent count, concurrency, run budget)
  can still result in an APPROVE verdict; they only require a flag and a reason, not a fix.
- No worked example or sample script ships with the skill; the only workflow scripts referenced are
  the two anonymized past-incident summaries in the checklist file.

## Compatibility and version notes

As of 2026-07-21, this page is checked against `workflow-fanout-checklist/SKILL.md` and
`workflow-fanout-checklist/references/approval-checklist.md` in this repository. The `agent()`
call syntax, `meta.phases` structure, and Claude Code model-tier names used as examples (Fable,
Opus, Sonnet) are specific to the Claude Code `Workflow` feature as it exists at that date and are
expected to change as the feature evolves. Treat
[`../workflow-fanout-checklist/references/approval-checklist.md`](../workflow-fanout-checklist/references/approval-checklist.md)
and [`../workflow-fanout-checklist/SKILL.md`](../workflow-fanout-checklist/SKILL.md) as the
canonical, currently-accurate source for exact syntax and model-tier names; this page summarizes
but does not redefine them.

## Verification status

Manually verified by reading `SKILL.md` and `references/approval-checklist.md` in full against
this page's claims. No automated test, eval, or CI check for this skill was found in the
repository at the time of writing. The skill's own procedure includes a self-check (independent
verifier agent reviewing a script against the checklist), but that applies to workflow scripts the
skill governs, not to the skill's own documentation or behavior.

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
