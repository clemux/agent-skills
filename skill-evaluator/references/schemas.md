<!--
Schema concepts adapted from Anthropic's Apache-2.0 skill-creator bundle at
commit 06a4dfeffbfee567b419357dbb693ecbd4ff740a. Modified for Codex JSONL.
-->

# Evaluation schemas

## Contents

- Eval set
- Per-eval metadata
- Run provenance and timing
- Grading
- Benchmark
- Review feedback
- Trigger set

## Eval set

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "name": "descriptive-case-name",
      "prompt": "A realistic end-user task.",
      "expected_output": "A description used by reviewers, never executors.",
      "files": ["fixtures/input.csv"],
      "assertions": [
        "The output CSV contains a total column.",
        "Every source row is represented exactly once."
      ]
    }
  ]
}
```

- Resolve relative `files` paths from the eval-set directory.
- Keep `expected_output` and `assertions` out of executor prompts.
- Use stable IDs and descriptive names so results remain comparable.

## Per-eval metadata

`eval_metadata.json` lives in each `eval-<id>-<name>/` directory:

```json
{
  "eval_id": 1,
  "eval_name": "descriptive-case-name",
  "prompt": "A realistic end-user task.",
  "expected_output": "Reviewer-only description.",
  "assertions": ["The expected file exists."]
}
```

## Run provenance and timing

`provenance.json` records configuration, source skill path, skill name, model,
sandbox, and the raw-prompt hash. `timing.json` uses:

```json
{
  "total_tokens": 12450,
  "total_duration_seconds": 31.42,
  "duration_ms": 31420,
  "usage": {
    "input_tokens": 11000,
    "cached_input_tokens": 9000,
    "output_tokens": 1400,
    "reasoning_output_tokens": 50
  },
  "returncode": 0
}
```

Only record metrics emitted by the actual platform event stream. Do not
estimate missing token or duration values.

## Grading

`grading.json` lives beside `timing.json`:

```json
{
  "expectations": [
    {
      "text": "The output CSV contains a total column.",
      "passed": true,
      "evidence": "outputs/result.csv header contains total"
    }
  ],
  "summary": {
    "passed": 1,
    "failed": 0,
    "total": 1,
    "pass_rate": 1.0
  },
  "execution_metrics": {
    "total_tool_calls": 4,
    "errors_encountered": 0,
    "output_chars": 820
  },
  "user_notes_summary": {
    "uncertainties": [],
    "needs_review": [],
    "workarounds": []
  }
}
```

The review UI and aggregator require each expectation to use exactly `text`,
`passed`, and `evidence`.

## Benchmark

`scripts/aggregate_benchmark.py` writes `benchmark.json` and
`benchmark.md`. The JSON contains:

- `skill_name` and `timestamp`
- `run_summary` grouped by configuration
- `delta` for configuration comparisons
- `per_eval` results and expectation evidence
- optional `analysis` added by the analyst pass

Do not hand-author benchmark statistics when the aggregator can calculate them.

## Review feedback

```json
{
  "reviews": [
    {
      "run_id": "eval-1-case-with_skill-run-1",
      "feedback": "The output is correct but the summary is too long.",
      "timestamp": "2026-01-15T10:30:00Z"
    }
  ],
  "status": "complete"
}
```

An empty feedback string means no issue was recorded; it is not a formal pass.

## Trigger set

```json
{
  "queries": [
    {
      "id": 1,
      "query": "Benchmark my revised invoice skill against its old version.",
      "should_trigger": true
    },
    {
      "id": 2,
      "query": "What is the capital of Iceland?",
      "should_trigger": false
    }
  ]
}
```

Keep a held-out subset that is not used to draft candidate descriptions.
