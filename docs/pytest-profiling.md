# pytest-profiling

Profiles slow pytest suites, applies measured fixes one at a time, and writes a report.

## Workflow

1. Read the project's test command and configuration.
2. Run the baseline twice and keep the second result.
3. Inspect slow test phases, collection, fixtures, and CPU profiles.
4. Summarize the evidence before changing anything.
5. Review candidates for redundant tests with the user.
6. Apply one optimization at a time and remeasure.
7. Run the full suite and write the report.

## Core commands

```bash
<pytest-command> --durations=20
time <pytest-command> --collect-only
<pytest-command> --setup-show
uv run --with pyinstrument pyinstrument -m pytest
```

Profile serially when the project normally uses xdist; measure parallel wall time separately.
Changes below roughly 10% may be noise unless repeated.

## Changes and output

The workflow may edit tests, fixtures, and test configuration. Adding a dependency, deleting or
merging tests, and choosing the report location require agreement.

[`profile-test.sh`](../pytest-profiling/scripts/profile-test.sh) profiles one test. The report format
and optimization catalog remain in [`SKILL.md`](../pytest-profiling/SKILL.md).
