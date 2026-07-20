---
name: pytest-profiling
description: Diagnose slow Python test suites, identify bottlenecks, apply fixes, and produce a written report. Use when the user asks to "speed up tests", "profile tests", "diagnose slow tests", "why are tests slow", "optimize test suite", "test performance", or mentions slow pytest runs.
---

# Pytest Profiling & Optimization

Systematic workflow for diagnosing, fixing, and reporting on slow Python/pytest test suites. Measure first, optimize based on data, never guess.

## Before Starting

1. **Read project conventions** — Check `AGENTS.md`, `CLAUDE.md`, or `pyproject.toml` to understand:
   - Which test directories exist (unit, integration, e2e)
   - How to run tests (`uv run pytest`, `pytest`, `make test`, etc.)
   - Test database setup and fixture patterns

2. **Ask the user:**
   - Which test directory or marker to profile (or profile the full suite)
   - Where to write the report file

3. **Check for pyinstrument** — If not installed, ask the user before adding it:
   ```bash
   uv pip list | grep pyinstrument
   # If missing, ask before running: uv add --dev pyinstrument
   ```

## Phase 1: Measure

All steps are read-only. No code changes.

**Profile serially when xdist is the default.** If the project's `addopts` includes `-n auto`
(pytest-xdist), append `-n 0` to every measurement command in this skill: `--durations` and
pyinstrument numbers are misleading under parallel workers. Report the parallel wall time
separately as the user-facing number, but attribute costs from serial runs only. Re-profiling
after a fix can expose overhead the previous bottleneck masked (e.g. per-call framework setup
hidden inside subprocess spawn cost) — treat the post-fix measurement as a first-class step,
not a formality.

### Step 1 — Baseline timing + slowest tests

```bash
uv run pytest <test_dir> --durations=20 -q
```

Record:
- Total wall time
- Number of tests (passed, failed, skipped)
- Top 20 slowest phases (setup, call, teardown)

Note whether the slowest items are **setup**, **call**, or **teardown** — this determines where to dig.

### Step 2 — Fixture setup/teardown chains

Pick 2-3 of the slowest tests and run:

```bash
uv run pytest <test_dir> -k "name_of_slow_test" -q --setup-show
```

This shows the full fixture dependency chain. Look for:
- Function-scoped fixtures that could be session-scoped
- Expensive fixtures called repeatedly (DB setup, app creation, crypto)
- Long teardown sequences

### Step 3 — CPU profiling with pyinstrument

```bash
uv run pyinstrument -r text -m pytest <test_dir> -k "name_of_slow_test" -q
```

`scripts/profile-test.sh` in this skill's directory wraps exactly that command if you prefer to
invoke it by path.

The call tree shows exactly where CPU time is spent. Repeat for 2-3 of the slowest tests to find common patterns.

**Common hotspots to look for:**
- `bcrypt.hashpw` / `bcrypt.gensalt` — password hashing (~200ms per call at default 12 rounds)
- `MetaData.create_all` — SQLAlchemy table creation
- `TRUNCATE ... CASCADE` — PostgreSQL lock acquisition
- `TestClient(app)` — ASGI lifespan enter/exit
- Module imports — heavy libraries loaded at import time (matplotlib, boto3, numpy)
- RSA key generation — `rsa.generate_private_key()`
- Network connections — Redis/Valkey, external services

### Step 4 — Micro-benchmarks (optional)

Only use micro-benchmarks when you need to compare specific alternatives (e.g., TRUNCATE vs DELETE, file-based vs `:memory:` SQLite). pyinstrument usually provides enough data — skip this step unless a targeted comparison is needed.

If a specific operation is suspect, isolate and measure it by writing a temporary benchmark script:

1. Use the **Write** tool to create a benchmark script (e.g., `/tmp/bench_<name>.py`):
```python
import time

# ... setup code ...

times = []
for i in range(10):
    start = time.time()
    # ... the suspect operation ...
    times.append(time.time() - start)
print(f"avg: {sum(times)/len(times)*1000:.1f}ms")
```

2. Run it:
```bash
uv run python /tmp/bench_<name>.py
```

Writing a file (via the Write tool) avoids the permission overhead of inline `python -c` and makes the benchmark inspectable.

## Phase 2: Analyze

Summarize findings before touching any code:

1. **Where is time spent?** — Categorize by fixture setup, test body, teardown
2. **Which fixtures are expensive?** — List per-call cost and how many tests use them
3. **Is there a common bottleneck?** — One or two things that dominate across all tests
4. **Estimate total impact** — `(per-call cost) × (number of calls) = total savings`

## Phase 2.5: Test Hygiene

Before optimizing slow tests for speed, check whether each slow test is worth keeping. Eliminating or consolidating redundant tests is the cheapest optimization — it removes setup cost entirely.

### Consolidation patterns

Look for these in the `--durations` output and the test source:

1. **Same setup, different assertions** — Multiple tests that call the same endpoint / function with the same inputs, each checking one HTML element, one field, or one side-effect. Consolidate into a single test. The assertions are independent reads of the same result — splitting them across tests only multiplies fixture setup cost.

2. **One atomic function, many tests** — A function that does steps A→B→C→D in sequence, with separate tests for each step's output. If the function is atomic (all-or-nothing), one comprehensive test covers the same contract. If any assertion fails, pytest shows the exact failing line — diagnosability is preserved.

3. **Identical fixture, different input values** — Tests that differ only by input parameters should use `pytest.mark.parametrize` instead of separate functions.

### How to evaluate

For each group of slow tests sharing the same setup:
- Read the function/endpoint under test
- List what each test asserts
- Ask: "Do these test distinct behavioral contracts, or different observations of the same behavior?"
- If the latter → consolidate, then measure

### What NOT to consolidate

- Tests with different setup (different fixture state, different preconditions)
- Tests that exercise genuinely different code paths (error vs success, different inputs triggering different branches)
- Tests where one failure would mask another (e.g., test A mutates state that test B depends on)

## Phase 3: Optimize

Design targeted fixes based on the profiling data. Apply one fix at a time and measure after each.

### Common fixes

#### Slow bcrypt hashing
Patch `bcrypt.gensalt` to use minimum rounds (4) in tests via a session-scoped autouse fixture in the root `tests/conftest.py`:

```python
@pytest.fixture(autouse=True, scope="session")
def _fast_bcrypt():
    original_gensalt = bcrypt.gensalt
    def fast_gensalt(rounds=4, prefix=b"2b"):
        return original_gensalt(rounds=4, prefix=prefix)
    with patch("bcrypt.gensalt", fast_gensalt):
        yield
```

#### Slow TRUNCATE teardown
Replace `TRUNCATE ... CASCADE` with `DELETE FROM` in reverse FK order. TRUNCATE acquires ACCESS EXCLUSIVE locks (~300ms even on empty tables). DELETE with row-level locks takes ~2ms for small row counts.

#### Expensive function-scoped fixtures
If a fixture is pure setup with no per-test state, consider widening its scope:
- `scope="module"` — shared within one test file
- `scope="session"` — shared across the entire run

Only do this if tests don't mutate the fixture's state.

#### Expensive app/framework setup per test
Web framework test clients (FastAPI `TestClient`, Django `Client`, Flask `test_client`) often recreate the app per test. If the app object is stateless and test isolation comes from swapping the backing service/session/DB, split the fixture:

1. **Module-scoped** fixture creates the app once (route registration, middleware, etc.)
2. **Function-scoped** fixture injects a fresh service/session/DB into the app and resets mutable state (settings files, caches)

This pattern works when the app captures dependencies by reference (e.g., a session holder that can be swapped). It does NOT work when dependency state is copied at app creation time.

#### Slow RSA key generation
Cache a test keypair as a session-scoped fixture instead of generating per-test.

#### Slow module imports
These are one-time costs and generally not worth optimizing. Note them in the report but don't act on them unless they dominate.

### Measurement after each fix

After each optimization:
1. Run the full suite: `uv run pytest <test_dir> -q --tb=no`
2. Record the new wall time
3. Calculate delta from previous state

## Phase 4: Commit

Commit each optimization as a separate commit with measured timings in the message:

```
perf(tests): <what changed>

<Why it helps.>

<previous>s → <new>s (saved ~<delta>s)
```

Use conventional commits (`perf:` prefix for performance improvements).

## Phase 5: Report

Write a report to the location chosen by the user. The report must include all of the following sections:

### Report template

```markdown
# Test Suite Performance: Analysis & Fixes

**Date:** YYYY-MM-DD
**Result:** <before>s → <after>s (<speedup>x faster)

## Baseline

- Test command: `<exact command>`
- Total tests: X passed, Y failed (pre-existing), Z skipped
- Wall time: Xs

## Methodology

1. `pytest --durations=20` — identify slowest test phases
2. `pytest --setup-show` — trace fixture setup chains
3. `pyinstrument` — CPU call trees on slowest tests

## Profiling Findings

| Component | Time | Scope | Notes |
|---|---|---|---|
| ... | ... | ... | ... |

## Bottleneck Breakdown (estimated)

- **<bottleneck 1>:** N calls × Xms = ~Ys (Z%)
- **<bottleneck 2>:** N calls × Xms = ~Ys (Z%)
- **Actual test work:** ~Ys (Z%)

## Fixes

### Fix N: <title>

**Commit:** `<commit message>`
**File:** `<path>`
**Time saved:** <before>s → <after>s (**-Xs**)

<Description of what changed and why.>

### Combined Result

| State | Wall time | Delta |
|---|---|---|
| Baseline | Xs | — |
| + fix 1 | Xs | -Xs |
| + fix 2 | Xs | -Xs |
| **Total saved** | | **-Xs (Nx)** |

## Remaining Slow Tests

| Test | Time | Reason |
|---|---|---|
| ... | ... | ... |
```

Commit the report as a separate `docs:` commit after all optimization commits.

## Key Principles

- **Measure before optimizing** — never guess where time is spent
- **One fix at a time** — measure after each change to attribute savings accurately
- **Don't optimize genuine workload** — raster I/O, large batch operations, etc. are expected costs
- **Test correctness first** — verify the same tests pass/fail before and after each fix
- **Keep production code unchanged** — all optimizations go in test infrastructure only
