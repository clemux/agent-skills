---
name: skill-evaluator
description: Evaluate and improve an existing Codex skill with controlled with-skill versus baseline or old-skill runs, assertions, grading, benchmark aggregation, qualitative review, iterative revision, optional blind comparison, and observational trigger-description tests. Use when Codex needs to test whether a drafted or revised skill materially improves outcomes, compare skill versions, build an eval set, inspect variance or token/time tradeoffs, review generated artifacts, or tune a skill description without replacing the built-in skill creator.
---

# Skill Evaluator

Evaluate a drafted Codex skill after authoring. Use the bundled `$skill-creator` for creation and structural validation; use this skill for comparative evidence and iteration.

## Protect evaluation integrity

- Keep task prompts, input artifacts, and assertions independent from the candidate skill.
- Never put expected answers, grading rubrics, or known defects in executor prompts.
- Snapshot an old skill before editing when it is the baseline.
- Run paired configurations from isolated repositories with the same model, sandbox, inputs, and raw task prompt.
- Treat one run as directional evidence. Use repeats when variance or consequential decisions matter.
- Do not let evaluators modify live repositories or production systems. Use disposable workspaces and the least permissive sandbox.

## Choose the comparison

- New skill: compare `with_skill` against `without_skill`.
- Revised skill: compare `with_skill` against an immutable `old_skill` snapshot.
- User-selected alternative: use two clearly named configurations and record their provenance.
- Behavior-only check: use explicit `$skill-name` invocation.
- Description-trigger check: use implicit prompts and the observational harness described in [trigger-evidence.md](references/trigger-evidence.md).

## Build the eval set

Create realistic prompts that vary in phrasing, complexity, and edge cases. Prefer tasks whose outputs can be inspected without touching live systems. Put them in `evals/evals.json` using [schemas.md](references/schemas.md).

Draft assertions after prompts are fixed. Use objective checks for file existence, required fields, valid syntax, calculations, or concrete workflow steps. Reserve subjective qualities for human review. Explain the assertions to the user before using them to drive revisions.

## Run paired evaluations

Use `scripts/run_eval.py` when independent `codex exec` runs are appropriate:

```bash
python scripts/run_eval.py \
  --eval-set /path/to/evals.json \
  --skill-path /path/to/candidate-skill \
  --workspace /path/to/candidate-workspace/iteration-1
```

For a revised skill, add `--baseline-skill /path/to/old-snapshot`. The script creates isolated Git repositories, installs only the selected target skill in each repository, invokes it explicitly for skill-bearing configurations, captures Codex JSONL, saves final outputs and usage, and never edits the source skill.

Before running potentially slow, costly, or externally connected evals, show the user the prompts, configurations, model choice, run count, and sandbox. Get approval when the run could take substantial time, need new permissions, or affect a live system.

When subagents are available and appropriate, paired subagents are also valid. Launch corresponding configurations together, give each only its task-local input, and record the actual model, duration, and token evidence exposed by the platform. Do not infer missing metrics.

## Grade and aggregate

Read [grading.md](references/grading.md) before grading. Grade assertions from saved outputs and transcripts, not from executor self-reports. Prefer deterministic check scripts for machine-verifiable assertions. Save each result as `grading.json` beside its run using the required schema.

Aggregate completed runs:

```bash
python scripts/aggregate_benchmark.py /path/to/workspace/iteration-1 \
  --skill-name skill-name
```

Read [analysis.md](references/analysis.md) for the analyst pass. Call out non-discriminating assertions, high variance, regressions hidden by averages, and time/token tradeoffs.

## Review qualitatively

Generate a standalone review page that works as a local file in Codex desktop:

```bash
python scripts/generate_review.py /path/to/workspace/iteration-1 \
  --skill-name skill-name \
  --benchmark /path/to/workspace/iteration-1/benchmark.json \
  --static /path/to/workspace/iteration-1/review.html
```

Show the resulting absolute file path as a clickable link. A local HTTP viewer is optional; do not launch a GUI or browser without the user's approval. Read the returned `feedback.json` or capture feedback in the conversation.

## Improve and repeat

Revise the smallest generalizable part of the skill that explains the evidence. Avoid changes that merely encode the current eval answers. Preserve a new immutable snapshot, rerun the same paired set, and add fresh held-out prompts before claiming general improvement.

For consequential or close results, read [comparison.md](references/comparison.md) and run an optional blind A/B comparison. Randomize labels, hide which output used the candidate skill, and reveal the mapping only after the judgment is saved.

## Evaluate trigger descriptions

Use `scripts/evaluate_triggers.py` only after reading [trigger-evidence.md](references/trigger-evidence.md). It runs raw implicit prompts through `codex exec --json` and reports whether emitted command-execution evidence references the candidate `SKILL.md`.

This is observational evidence, not a guaranteed Codex invocation event. A positive path observation supports that Codex consulted the skill. Absence is inconclusive because current documented JSONL events do not include a dedicated skill-activation event. Do not automatically overwrite a description from this signal alone; compare candidate descriptions on training and held-out prompts and require human review.

## Resource map

- [schemas.md](references/schemas.md): eval, grading, timing, benchmark, and feedback formats.
- [grading.md](references/grading.md): assertion grading protocol.
- [analysis.md](references/analysis.md): benchmark and variance analysis.
- [comparison.md](references/comparison.md): optional blind comparison.
- [trigger-evidence.md](references/trigger-evidence.md): Codex-native trigger harness semantics and limits.
- `scripts/run_eval.py`: controlled paired executor.
- `scripts/evaluate_triggers.py`: observational implicit-trigger evaluator.
- `scripts/aggregate_benchmark.py`: benchmark aggregation.
- `scripts/generate_review.py` and `assets/viewer.html`: review UI and static fallback.
