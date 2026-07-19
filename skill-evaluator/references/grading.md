<!--
Adapted from the grading approach in Anthropic's Apache-2.0 skill-creator bundle
at commit 06a4dfeffbfee567b419357dbb693ecbd4ff740a. Modified for Codex artifacts.
-->

# Assertion grading

Grade saved artifacts independently from the executor.

1. Read `eval_metadata.json`, then inspect only the run's transcript and outputs.
2. Evaluate each assertion separately. Do not let one strong result compensate for another failure.
3. Prefer a deterministic command or focused script when the assertion is machine-checkable.
4. Mark `passed: true` only when concrete evidence establishes the claim.
5. Use `passed: false` when the claim fails or required evidence is absent.
6. Cite an output path, field, command result, or short artifact excerpt in `evidence`.
7. Record ambiguity under `user_notes_summary.needs_review`; do not silently convert subjective judgment into an objective pass.
8. Recalculate `passed`, `failed`, `total`, and `pass_rate` from the expectation records.

Do not read the candidate `SKILL.md` while grading unless the assertion explicitly
checks the skill package itself. Behavioral grades should depend on behavior.

For subjective work, leave assertions narrow and use the review UI for qualities
such as taste, clarity, visual polish, or appropriateness.
