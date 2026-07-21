# skill-evaluator

`skill-evaluator` builds controlled, comparative evidence about whether a Codex skill actually
improves task outcomes. It runs paired Codex executions — a candidate skill against a baseline (no
skill) or against an immutable snapshot of an older version — over a user-authored eval set, grades
the saved outputs against explicit assertions, aggregates pass rates and time/token statistics,
renders a local HTML review page, and supports optional blind A/B comparison and observational
trigger-description tests. It is a Codex-native derivative of Anthropic's Apache-2.0 skill-creator
evaluator; the bundled scripts invoke only the Codex CLI. It complements, rather than replaces, the
built-in skill creator: use the creator to author and structurally validate a skill, and this skill
to measure and iterate on it.

See [skills.md](skills.md) for the full skill index.

## 1. Summary

The skill drives four bundled Python scripts and five reference documents through a fixed loop:
build an eval set, run paired `codex exec` configurations in isolated throwaway Git repositories,
grade the artifacts each run produced, aggregate the grades into a benchmark, and review the
outputs. Every run is written to an on-disk artifact tree so grading and review use saved evidence.
Each configuration spends real Codex tokens per eval per run, so expensive or externally-connected
runs require user approval.

## 2. Status

Active. Default harness mapping from
[`install.conf.sample`](../install.conf.sample):

```text
skill-evaluator         codex
```

The skill is installed for **Codex only**, not Claude Code or the neutral `~/.agents/skills` root.
The scripts assume the Codex CLI and Codex JSONL event formats.

The repository [`README.md`](../README.md) skill table also shows this Codex-only default in its
"Default roots" column; `install.conf.sample` remains the authoritative source both draw from.

Invocation: **both** model-triggered and user-invoked. The `description` frontmatter (see Triggers)
lets Codex select the skill on its own, and the bundled `agents/openai.yaml` exposes a
user-facing default prompt that invokes it explicitly:

```text
Use $skill-evaluator to compare this skill against a baseline and review the results.
```

## 3. Triggers

Per the `description` in [../skill-evaluator/SKILL.md](../skill-evaluator/SKILL.md), the skill is
meant to fire when Codex needs to:

- test whether a drafted or revised skill materially improves outcomes;
- compare skill versions;
- build an eval set;
- inspect variance or token/time tradeoffs;
- review generated artifacts; or
- tune a skill description — without replacing the built-in skill creator.

The description scopes triggering to evaluating and iterating on an *existing* skill after authoring.
It does not claim to author skills from scratch.

## 4. Prerequisites

- **Codex CLI** on `PATH` as `codex` (overridable with `--codex-bin`). The scripts call
  `codex exec --json` with the `--ephemeral`, `--ignore-user-config`, `--ignore-rules`, `--sandbox`,
  and `--cd` flags.
- **Codex authentication.** `run_eval.py` and `evaluate_triggers.py` build an isolated Codex home
  and require one of: an existing `auth.json` under `$CODEX_HOME` (default `~/.codex`), which they
  symlink into the throwaway home, or a `CODEX_API_KEY` environment variable. With neither, the run
  aborts before invoking Codex.
- **Git.** Each run initializes a fresh repository with `git init --initial-branch=main`.
- **Python 3.** The scripts use standard-library modules only (no third-party packages) and use
  builtin generic type subscripts, so a reasonably recent Python 3 is required (Python 3.9 or newer,
  as of 2026-07-21; not independently version-tested here).
- **Network and Codex account quota** for any non-`--prepare-only` run, since each run calls the
  hosted Codex model.
- **Skill creator** (the bundled `$skill-creator`) is the companion for authoring and structural
  validation; it is referenced but not required to be installed for the evaluation scripts to run.

## 5. Read/write and safety boundaries

What the scripts read:

- the candidate skill directory and, optionally, a baseline skill snapshot (read-only — the source
  skills are copied, never edited);
- the eval/trigger set JSON and any input `files` it references;
- saved run artifacts (transcripts, outputs, grading, timing) during aggregation and review.

What the scripts write — all under the workspace/artifact tree you name, plus isolated temp homes:

- isolated Git repositories per run, each with the selected skill copied into
  `.agents/skills/<name>/`;
- per-run `command.json`, `provenance.json`, `transcript.jsonl`, `stderr.txt`, `timing.json`, and a
  copied `outputs/` directory;
- aggregated `benchmark.json` / `benchmark.md`; a review `review.html` (static) or a served page;
  `feedback.json`; and trigger `observation.json` / `trigger-results.json`.

Isolation and human-facing surfaces:

- Codex runs in the **least permissive practical sandbox**: `evaluate_triggers.py` forces
  `--sandbox read-only`; `run_eval.py` defaults to `--sandbox workspace-write` (choices:
  `read-only`, `workspace-write`) and confines writes to the per-run throwaway repository. Runs also
  pass `--ephemeral`, `--ignore-user-config`, and `--ignore-rules`, and execute inside a temporary
  `HOME`/`CODEX_HOME` so the user's real Codex config and history are not touched.
- The SKILL.md workflow requires explicit user approval **before** any potentially slow, costly, or
  externally-connected run: the agent must show the prompts, configurations, model, run count, and
  sandbox first.
- The review server binds to `127.0.0.1` only, and the skill instructs the agent **not** to launch a
  GUI or browser without approval. `generate_review.py --open` (which opens the default browser) and
  starting the HTTP server are the human-facing actions that need consent; prefer `--static` to
  write a file and hand back its path.
- Integrity guardrails (from SKILL.md): keep prompts, inputs, and assertions independent from the
  candidate skill; never put expected answers or rubrics in executor prompts; snapshot an old skill
  before editing; and never let evaluators mutate live repositories or production systems.

## 6. Typical workflow

1. **Choose the comparison.** New skill → `with_skill` vs `without_skill`. Revised skill →
   `with_skill` vs an immutable `old_skill` snapshot. See
   [../skill-evaluator/references/comparison.md](../skill-evaluator/references/comparison.md) for the
   blind-comparison variant.
2. **Build the eval set** in `evals/evals.json` using the schema in
   [../skill-evaluator/references/schemas.md](../skill-evaluator/references/schemas.md); draft
   assertions after the prompts are fixed, and explain them to the user before using them to drive
   revisions.
3. **Run paired evaluations** with `run_eval.py` (or paired subagents when appropriate).
4. **Grade** each run from saved outputs per
   [../skill-evaluator/references/grading.md](../skill-evaluator/references/grading.md), writing a
   `grading.json` beside each run.
5. **Aggregate** with `aggregate_benchmark.py`, then analyze per
   [../skill-evaluator/references/analysis.md](../skill-evaluator/references/analysis.md).
6. **Review** the outputs with `generate_review.py` and capture feedback.
7. **Improve and repeat:** revise the smallest generalizable part of the skill, snapshot it again,
   rerun the same paired set, and add held-out prompts before claiming general improvement.

## 7. Bundled resources

Canonical files live in the skill package.

### Scripts and CLI contracts

All four scripts are stdlib-only Python. Because `evaluate_triggers.py` imports from `run_eval.py`,
run the scripts from the package `scripts/` directory (or with it on `sys.path`) as shown in
SKILL.md.

**`scripts/run_eval.py`** — controlled paired executor. Creates isolated Git repos, installs only
the selected skill in each, invokes it explicitly for skill-bearing configurations, captures Codex
JSONL, and saves outputs, usage, and provenance. It never edits the source skill.

- `--eval-set PATH` (required) — eval set JSON.
- `--skill-path PATH` (required) — candidate skill directory (must contain `SKILL.md`).
- `--baseline-skill PATH` (optional) — old-skill snapshot; its presence names the baseline
  configuration `old_skill` instead of `without_skill`.
- `--workspace PATH` (required) — artifact tree root.
- `--runs-per-config N` (default 1), `--model NAME`, `--sandbox {read-only,workspace-write}`
  (default `workspace-write`), `--timeout SECONDS` (default 900), `--codex-bin NAME` (default
  `codex`), `--prepare-only` (build run dirs and `command.json` manifests without invoking Codex).
- Outputs: the artifact tree in Section "Artifact tree layout"; prints a JSON line with the
  workspace path and eval count.

**`scripts/aggregate_benchmark.py`** — benchmark aggregation.

- Positional `benchmark_dir` (required). Supports both the workspace layout (eval dirs directly under
  the directory) and a legacy `runs/` layout.
- `--skill-name`, `--skill-path`, `--output/-o PATH` (default `<benchmark_dir>/benchmark.json`).
- Outputs `benchmark.json` and a sibling `benchmark.md` with per-configuration mean/stddev/min/max
  for pass rate, time, and tokens, plus a delta between the first two configurations. Prints a
  short pass-rate summary.

**`scripts/generate_review.py`** — qualitative review UI.

- Positional `workspace` (required) — scanned recursively for run directories containing `outputs/`.
- `--port/-p` (default 3117), `--skill-name/-n`, `--previous-workspace PATH` (shows prior outputs
  and feedback as context), `--benchmark PATH` (adds a benchmark tab), `--static/-s PATH` (write a
  standalone HTML file and exit instead of serving), `--open` (open the default browser — needs user
  consent).
- Server mode binds `127.0.0.1`, regenerates HTML per request, and saves feedback to
  `feedback.json` via a small `POST /api/feedback` endpoint. If the chosen port is taken it falls
  back to an OS-assigned free port.

**`scripts/evaluate_triggers.py`** — observational implicit-trigger evaluator. Read
[../skill-evaluator/references/trigger-evidence.md](../skill-evaluator/references/trigger-evidence.md)
first.

- `--eval-set PATH` (required, a `queries` set), `--skill-path PATH` (required),
  `--workspace PATH` (required).
- `--description TEXT` (temporarily override the copied skill's description for the test),
  `--runs-per-query N` (default 3), `--trigger-threshold FLOAT` in [0,1] (default 0.5),
  `--model NAME`, `--timeout SECONDS` (default 300), `--codex-bin NAME`, `--prepare-only`.
- Runs raw implicit prompts under `--sandbox read-only` and marks a query `observed` only when an
  emitted `command_execution` JSONL item references the copied candidate `SKILL.md`. Writes a
  per-query `observation.json` and a workspace `trigger-results.json`, and prints the results JSON.

### References

- [schemas.md](../skill-evaluator/references/schemas.md) — eval, metadata, provenance/timing,
  grading, benchmark, feedback, and trigger-set formats.
- [grading.md](../skill-evaluator/references/grading.md) — assertion grading protocol.
- [analysis.md](../skill-evaluator/references/analysis.md) — benchmark and variance analysis.
- [comparison.md](../skill-evaluator/references/comparison.md) — optional blind A/B comparison.
- [trigger-evidence.md](../skill-evaluator/references/trigger-evidence.md) — Codex trigger-harness
  semantics and limits.

### Other assets

- `assets/viewer.html` — the review-page template `generate_review.py` fills in.
- `agents/openai.yaml` — Codex interface metadata (display name, short description, default prompt).
- `LICENSE.txt` — see License and provenance.

### Artifact tree layout

`run_eval.py` writes, under `--workspace`:

```text
<workspace>/
└── eval-<id>-<name>/
    ├── eval_metadata.json
    ├── with_skill/
    │   └── run-<n>/
    │       ├── command.json        # argv + prompt actually issued
    │       ├── provenance.json     # config, skill path/name, model, sandbox, raw-prompt SHA-256
    │       ├── workspace/          # the isolated Git repo Codex ran in (skill under .agents/skills/)
    │       ├── transcript.jsonl    # raw codex exec --json stream
    │       ├── stderr.txt
    │       ├── timing.json         # tokens, duration, usage, returncode
    │       └── outputs/            # copied from the repo's outputs/, plus final.md
    └── without_skill/  (or old_skill/)
        └── run-<n>/ ...
```

Grading adds a `grading.json` beside each run; aggregation adds `benchmark.json`/`benchmark.md` at
the workspace root; review adds `review.html` (static) and/or `feedback.json`. Trigger runs use a
parallel `query-<id>/run-<n>/` layout with `observation.json` plus a workspace `trigger-results.json`.

## 8. Limitations

- **Cost and time.** Every non-`--prepare-only` run spends real Codex tokens; cost scales with
  evals × configurations × `--runs-per-config`. Expensive runs require approval. Default timeouts
  are 900 s per eval run and 300 s per trigger query (as of
  2026-07-21).
- **Grading is not automated by these scripts.** `run_eval.py` produces artifacts; `grading.json`
  is written by the grading pass (agent or check scripts), and `aggregate_benchmark.py` warns and
  skips runs whose `grading.json` is missing or malformed. A single run is directional evidence only;
  use repeats when variance or the decision matters.
- **Delta compares only the first two configurations**, by dictionary insertion order, and
  `benchmark.json` metadata records a fixed `runs_per_configuration: 3` and placeholder model names
  rather than values derived from the actual runs — read the per-run `provenance.json`/`timing.json`
  for ground truth. Compare durations and tokens only across identical model, run count, inputs, and
  sandbox.
- **Trigger observation is conservative and inconclusive on the negative side.** It recognizes only
  an emitted `command_execution` that references the copied `SKILL.md`; Codex JSONL has no documented
  dedicated skill-activation event, so an absent observation does not prove the skill was inactive.
  Do not build an automatic description-rewrite loop on this signal, and require human review before
  editing live frontmatter.
- **No package-specific automated test suite.** `skill-evaluator` ships no unit or integration tests
  for its scripts (see Verification status).

## 9. Compatibility and version notes

Dated 2026-07-21; re-verify against current Codex releases.

- The scripts depend on specific `codex exec` flags (`--json`, `--ephemeral`,
  `--ignore-user-config`, `--ignore-rules`, `--sandbox`, `--cd`) and on the Codex JSONL event schema
  (`item.completed`/`agent_message`, `turn.completed`/`usage`, `command_execution`). Both are
  version-sensitive; a Codex CLI or event-schema change can break parsing or cause trigger false
  negatives. Preserve raw `transcript.jsonl` and re-inspect after Codex upgrades.
- The auth path assumes `auth.json` under `$CODEX_HOME` (default `~/.codex`) or a `CODEX_API_KEY`
  variable.
- The review viewer (`assets/viewer.html`) references external resources — Google Fonts and a
  SheetJS CDN script — so the `--static` "standalone" page is not fully offline: fonts fall back and
  `.xlsx` previews will not render without network access. Treat it as a locally-served page rather
  than a network-free artifact.
- `generate_review.py` defaults to port 3117 and falls back to a random free port if it is taken.

## 10. Verification status

- **Automated checks:** none specific to this skill. The repository's automated tests
  (`tests/test_publication_boundary.py`) enforce the publication boundary across all tracked files,
  and shell scripts are linted by `shellcheck` via pre-commit — but `skill-evaluator` bundles no
  shell scripts and no test suite for its Python scripts, so their behavior is not covered by
  automated tests in this repo.
- **Manually verified for this page:** the CLI arguments, defaults, sandbox settings, artifact-tree
  layout, auth handling, and external-resource references were read directly from the scripts and
  `assets/viewer.html` on 2026-07-21.
- **Untested / unverified here:** end-to-end behavior against a live Codex CLI, the exact Python
  minimum version, real token/time costs, and current Codex JSONL event names were not executed or
  confirmed against a running Codex install; treat the version-sensitive notes above as
  release-specific.

## License and provenance

The skill bundles an Apache License 2.0 text at [../skill-evaluator/LICENSE.txt](../skill-evaluator/LICENSE.txt).
`aggregate_benchmark.py`, `generate_review.py`, four of the five reference documents
(`schemas.md`, `grading.md`, `analysis.md`, `comparison.md`), and `assets/viewer.html`
carry headers noting they are adapted from Anthropic's Apache-2.0 skill-creator bundle at commit
`06a4dfeffbfee567b419357dbb693ecbd4ff740a`; `references/trigger-evidence.md` is Codex-native with no
adaptation header, and `run_eval.py` and `evaluate_triggers.py` are described as Codex-native
replacements written for this derivative bundle that invoke only the Codex CLI.

## Example (illustrative)

The transcript below is ILLUSTRATIVE, uses placeholder paths, and is not a real capture.

```bash
# 1. Dry-run: build the run dirs and command manifests without spending tokens.
python scripts/run_eval.py \
  --eval-set ~/path/to/evals.json \
  --skill-path ~/path/to/<skill-name> \
  --workspace ~/path/to/workspace/iteration-1 \
  --prepare-only

# 2. After approval, run paired configs (candidate vs old snapshot), 3 runs each.
python scripts/run_eval.py \
  --eval-set ~/path/to/evals.json \
  --skill-path ~/path/to/<skill-name> \
  --baseline-skill ~/path/to/<skill-name>-old-snapshot \
  --workspace ~/path/to/workspace/iteration-1 \
  --runs-per-config 3

# 3. Grade each run (writes grading.json beside each run), then aggregate.
python scripts/aggregate_benchmark.py ~/path/to/workspace/iteration-1 \
  --skill-name <skill-name>

# 4. Write a standalone review page and hand back its path (no server, no browser).
python scripts/generate_review.py ~/path/to/workspace/iteration-1 \
  --skill-name <skill-name> \
  --benchmark ~/path/to/workspace/iteration-1/benchmark.json \
  --static ~/path/to/workspace/iteration-1/review.html
```
