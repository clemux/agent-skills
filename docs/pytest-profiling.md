# pytest-profiling

`pytest-profiling` is a workflow skill for diagnosing slow Python/pytest test suites: it measures
where a suite spends time (baseline timing, collection/import cost, fixture setup/teardown chains,
and CPU call trees via Pyinstrument), analyzes the bottlenecks, optionally consolidates redundant
tests, applies fixes one at a time while re-measuring, and — when the user grants the scope — commits
each change and writes a report. Its central discipline is "measure first, optimize on data, never
guess," and every action that mutates the project (installing tools, editing test infrastructure,
merging tests, committing, writing a report) is gated on explicit user scope. See the canonical
[SKILL.md](../pytest-profiling/SKILL.md) for the full procedure.

## Status

Active. Default harness mapping in [`install.conf.sample`](../install.conf.sample):

```text
pytest-profiling        claude codex agents
```

It is installed on all three roots (Claude Code, Codex, and the neutral `~/.agents/skills` root).

The skill is primarily **model-triggered**: its `description` frontmatter lists natural-language
phrases that fire it automatically. It is equally usable when a user invokes it by name. Either way
it runs as an in-context procedure the agent follows, not as a standalone CLI.

## Triggers

Per the `description` frontmatter, the skill fires when the user asks to "speed up tests", "profile
tests", "diagnose slow tests", "why are tests slow", "optimize test suite", or mentions "test
performance", "tests take too long in CI", or slow pytest runs generally. It is scoped to Python
test suites run under pytest.

## Prerequisites

- A Python project using pytest (any runner: `uv run pytest`, `poetry run pytest`, plain `pytest`,
  `make test`, etc. — the skill detects the project's actual command and refers to it as `<pytest>`).
- **Pyinstrument** for CPU profiling (Phase 1, Step 4). The skill prefers running it without touching
  project dependencies (`uv run --with pyinstrument …`). If the project already declares Pyinstrument
  it is used directly; adding it as a dev dependency happens **only if the user agrees**.
- No network or authentication is required by the skill itself. (The *tests under measurement* may
  need whatever they normally need — databases, services, network.)
- No dependency on other skills.

## Read/write and safety boundaries

Phase 1 (Measure) is described as read-only with respect to project source: it does not change code.
That is not the same as side-effect-free. Running a test suite executes the suite, and **test suites
may mutate databases, services, caches, or files** as a normal part of running. "Read-only
measurement" means the skill does not edit your code to measure it — it does not mean the measurement
runs are guaranteed free of side effects. Treat measurement runs against shared or stateful
environments accordingly.

Every project-mutating action is gated on user-granted scope:

- **Installing Pyinstrument as a dependency** — only if the user agrees; the default path avoids any
  dependency change.
- **Mutating code or test infrastructure** — fixes go in test infrastructure only; production code is
  kept unchanged (a stated key principle). Fixes are applied one at a time.
- **Consolidating or deleting tests** (Phase 2.5) — changes coverage and how failures read, so the
  skill presents candidate groups and its reasoning and gets agreement **before** merging or deleting
  any test.
- **Committing** (Phase 4) — commits happen as part of the workflow; the skill uses conventional
  commit prefixes (`perf:` for fixes, `docs:` for the report).
- **Writing the report** (Phase 5) — written to a location the user chooses.

Test-architecture changes (for example converting subprocess-per-test CLI suites to in-process
calls) change what a test verifies and are proposed per-test with user sign-off, not applied
mechanically.

## Typical workflow

1. **Before starting** — read project conventions (`AGENTS.md`, `CLAUDE.md`, `pyproject.toml`,
   `pytest.ini`, `tox.ini`, `Makefile`) to learn the test directories and the real test command;
   audit `addopts` and the active plugin list (`<pytest> --version`); ask the user which
   directory/marker to profile and where to write the report; check for Pyinstrument without mutating
   dependencies.
2. **Phase 1 — Measure** (read-only w.r.t. code):
   - Baseline timing and slowest phases: `<pytest> <test_dir> --durations=20 -q`.
   - Collection/import time: `time <pytest> <test_dir> --collect-only -q`, then `python -X importtime`
     on suspect modules.
   - Fixture setup/teardown chains on the slowest tests: `--setup-show`.
   - CPU profiling with Pyinstrument on the slowest tests (see the bundled wrapper below).
   - Optional micro-benchmarks only when comparing specific alternatives.
3. **Phase 2 — Analyze** — categorize where time goes (collection/import, fixture setup, test body,
   teardown), list expensive fixtures and per-call cost, identify dominant bottlenecks, and estimate
   `per-call cost × number of calls`.
4. **Phase 2.5 — Test hygiene** — identify redundant tests that could be consolidated (same setup /
   different assertions, one atomic function tested step-by-step, identical fixture with different
   inputs → `parametrize`); propose to the user before changing anything.
5. **Phase 3 — Optimize** — apply one targeted fix at a time and re-measure after each. "Nothing to
   fix" is a valid, explicitly-reported outcome. Levers needing a new dependency can be measured with
   an ephemeral `uv run --with …` run before being proposed, so the recommendation carries a real
   number.
6. **Phase 4 — Commit** — each optimization as its own `perf(tests): …` commit with before/after
   timings.
7. **Phase 5 — Report** — write the report using the template in the SKILL, committed separately as
   `docs:`.

### xdist (parallel) rules

As of 2026-07-21 the skill's rule is: **profile serially for attribution.** If the project's
`addopts` includes `-n auto` (pytest-xdist), append `-n 0` to every measurement command —
`--durations` and Pyinstrument numbers are misleading under parallel workers because worker time is
invisible to the main-process sampler. The **parallel wall time is recorded separately** as the
user-facing headline number, but all cost attribution comes from serial runs. Pyinstrument
specifically samples the main process, so xdist must be disabled while profiling (`-p no:xdist` or
dropping `-n`). Parallelism is also treated as an optimization lever (Phase 3), applied *after*
per-test fixes, since session-scoped fixtures run once per worker and shared global state breaks
under parallel workers.

### Baseline and repetition guidance

Run the baseline **twice and use the second run** — the first pays one-time costs (bytecode
compilation, cold caches) that would otherwise inflate later "savings." Timing noise is real: the
skill treats deltas under ~10% as noise, not signal, unless repeated runs agree. Re-profiling after a
fix is a first-class step, not a formality, because a fix can expose overhead the previous bottleneck
masked. If coverage is in `addopts`, time a `--no-cov` run too — the delta is the coverage tax.

### Fixture phase attribution

`--durations` output distinguishes **setup**, **call**, and **teardown** phases; noting which phase
dominates determines where to dig. `--durations` hides phases under 0.005s, so
`--durations=0 --durations-min=0.05` is used when the top 20 don't explain most of the wall time. For
`unittest.TestCase`-style or xunit `setup_method` classes, `--setup-show` prints only an opaque
`_xunit_setup_method_fixture_*` line, so the skill reads the `setup_method`/`teardown_method` source
directly instead.

## Bundled resources

- **[`scripts/profile-test.sh`](../pytest-profiling/scripts/profile-test.sh)** — a wrapper around
  Pyinstrument for pytest. It runs, in effect:

  ```bash
  ${RUNNER:-uv run --with pyinstrument} pyinstrument -r text -m pytest "$@" -q
  ```

  Usage: `[RUNNER="uv run --with pyinstrument"] profile-test.sh <test_dir> [-k "filter"] [extra
  pytest args...]`. `RUNNER` is the project's command prefix for running Python tools and defaults to
  `uv run --with pyinstrument` (works in uv projects without touching dependencies); set `RUNNER=""`
  if `pyinstrument` is on `PATH`, `RUNNER="poetry run"` for poetry, etc. All positional arguments pass
  through to pytest. The plain command it wraps is `pyinstrument -r text -m pytest <args> -q`.

No `references/` or `agents/` directories are bundled — the SKILL.md carries all of the reference
material (hotspot catalog, common fixes, and the report template) inline.

## Limitations

- **Pyinstrument is a sampling profiler** — very short calls may not appear; what it reports as
  dominant is reliable, but absence is not proof.
- Under **pytest-xdist**, `--durations` and Pyinstrument are misleading; serial runs are required for
  attribution (see the xdist rules above).
- "Read-only measurement" does **not** guarantee side-effect-free runs — the suite under test may
  mutate databases, services, caches, or files.
- The common-fix examples (bcrypt, SQLAlchemy `create_all`, PostgreSQL `TRUNCATE`, ASGI `TestClient`,
  RSA key generation, subprocess-per-test CLI suites) come from a hotspot catalog that states their
  timing figures as concrete numbers. Treat them as starting points to confirm by measurement on the
  target project, not guaranteed characteristics — this caution is this page's, and is consistent
  with the skill's own measure-first discipline.
- "Nothing to fix" is a legitimate result; the skill declines to force a low-value change just to
  produce a commit.
- Consolidating tests changes coverage, so it cannot proceed without user agreement — a deliberate
  gate, not an automation gap.

## Compatibility and version notes

- Verified against the sources as of **2026-07-21** (the day SKILL.md was last updated).
- The default Pyinstrument invocation assumes `uv` is available (`uv run --with pyinstrument`);
  non-uv projects must set `RUNNER` or supply Pyinstrument on `PATH`. The skill's prose otherwise
  detects the project's real runner and does not hard-require `uv` for running the tests themselves.
- Third-party timing figures in the SKILL (for example "~200ms per bcrypt call at 12 rounds", "~300ms
  for `TRUNCATE … CASCADE`", "~50–100ms subprocess startup") are stated there as plain figures.
  They are release/environment-specific; re-verify against the target project rather than quoting
  them as fixed (this page's caution, not SKILL.md wording).
- The README previously carried `pytest-profiling` portability notes that predated the current
  SKILL.md; they were removed in favor of this page. Where any older copy of them resurfaces,
  SKILL.md is authoritative.

## Verification status

- **Automated:** the bundled shell script is subject to the repo's `shellcheck` pre-commit hook; the
  publication-boundary check (`scripts/check_publication_boundary.py`) scans tracked text. There are
  no automated tests exercising the profiling workflow end to end.
- **Manually verified against sources (2026-07-21):** the harness mapping, the trigger phrases, the
  wrapper command and the plain command it wraps, the xdist `-n 0`/parallel-wall-time rules, the
  twice-run baseline and ~10% noise threshold, the phase-attribution guidance, and the user-scope
  gates on installing Pyinstrument, mutating test infrastructure, consolidating tests, committing, and
  reporting.
- **Untested:** the actual speed-up figures and the effectiveness of each "common fix" — these are
  scenario-dependent examples, not measured guarantees, and the skill itself instructs the agent to
  measure rather than trust them.

## Example

Illustrative command sequence with placeholder data — not a real capture:

```bash
# Detect the runner and active plugins first.
<pytest> --version

# Baseline twice; use the second run. Suite defaults to xdist, so pin -n 0 for attribution.
<pytest> tests/unit --durations=20 -q -n 0

# Collection/import overhead.
time <pytest> tests/unit --collect-only -q

# CPU call tree on one slow test, via the bundled wrapper.
RUNNER="uv run --with pyinstrument" \
  ~/path/to/agent-skills/pytest-profiling/scripts/profile-test.sh tests/unit -k "test_slow_thing"

# Record the parallel wall time separately as the user-facing number.
<pytest> tests/unit -q -n auto
```

Related: see [skills.md](skills.md) for the full skill index.
