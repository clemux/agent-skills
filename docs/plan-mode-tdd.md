# plan-mode-tdd

`plan-mode-tdd` produced Plan-mode output structured as a sequence of TDD cycles: for each
discrete behavior change, write a failing test, implement the minimal fix, run tests, run a
review-agent pass, then commit.

## Status

Historical; not recommended. It is not mapped to any harness in
[`install.conf.sample`](../install.conf.sample):

```
plan-mode-tdd           none
```

The package is retained as a record of the pattern and its limitations, not as an executable
workflow. See [skills.md](skills.md) for current mapped skills.

## Why it was retired

- **Depends on an agent that is not bundled here.** Step 4 of the workflow instructs Plan mode to
  "Run the `feature-dev:code-reviewer` agent." That agent is not part of this repository and is not
  installed by `install.sh`; the skill assumes a plugin or agent that a harness must supply
  separately. Where it is absent, step 4 has nothing to invoke.
- **Conflates planning with execution and commit behavior.** The skill is triggered by a request
  for "a plan or planning mode workflow," but its output prescribes running tests, running a review
  agent, and creating commits — actions that go beyond producing a plan. A user asking Plan mode
  for a sequenced TDD plan may not expect the resulting steps to execute code changes and commit
  them without a separate, explicit go-ahead.
- **Unqualified test-layer ordering.** The Notes section states a fixed preference — "e2e, then
  integration, then unit" — as a general rule for which test layer to write first, with no
  qualification for project type, existing test suite shape, or cost of e2e tests. That ordering is
  not universally appropriate and is asserted without caveats in the source file; see
  [`../plan-mode-tdd/SKILL.md`](../plan-mode-tdd/SKILL.md).

## Known risks

Re-enabling this skill as-is (e.g. adding it back to `install.conf` and pointing it at a harness)
risks:

- A blocked or silently skipped step 4 wherever `feature-dev:code-reviewer` is not present, with no
  fallback defined in the skill.
- Plan-mode output that commits changes as a matter of course, surprising a user who expected only
  a plan to review before any code or commits were produced.
- Test-suite churn from defaulting every feature to an e2e-first test, even for changes better
  covered by a unit test.

## Migration / replacement

No direct replacement exists. A successor would need to:

- Either bundle or explicitly declare a dependency on a concrete, available review step (agent,
  skill, or manual instruction) rather than naming an unbundled agent by name, and degrade
  gracefully when no reviewer is configured.
- Separate the planning step (producing a sequenced TDD plan) from the execution step (running
  tests, invoking a reviewer, committing), so a user can review the plan before agreeing to have it
  executed.
- Make the test-layer ordering a heuristic conditioned on the project's existing test setup instead
  of a fixed e2e-first default.

## Verification status

Never validated. There is no evidence in the skill package of it having been run end-to-end against
a real Plan-mode session; the `agents/openai.yaml` file bundled alongside `SKILL.md` supplies a
display name, short description, and default prompt but no evidence of use or testing outcome.

## Example (illustrative only)

Constructed Plan-mode output using placeholder data. It is not from a real session; step 4 retains
the unresolved agent reference from the skill.

```text
Plan for: add input validation to <endpoint-name>

Change 1: reject empty payload
  1. Add failing test: test_rejects_empty_payload
  2. Implement minimal validation in <handler-file>
  3. Run: pytest tests/<handler-file>_test.py
  4. Run feature-dev:code-reviewer, address findings
  5. Commit: "reject empty payload in <endpoint-name>"

Change 2: reject payload over size limit
  ...
```
