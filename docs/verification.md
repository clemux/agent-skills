# Verification

This page lists every automated check that exists in this repository as of 2026-07-21: the exact
command to run each one, what it covers, and what it does not. It closes with an honest gap
statement — most skill packages have no automated coverage at all, and their `SKILL.md` guidance
is verified only by use, not by a test suite.

## Publication boundary check

```bash
python3 scripts/check_publication_boundary.py
```

Scans every file tracked by `git ls-files` (skipping binaries and symlink targets it can't decode
as UTF-8) for patterns that suggest private or backend-specific data: personal home-directory
paths, home-relative development-directory references, `obs:`-prefixed reference IDs, and
Codex/Claude session-identity environment assignments. It also loads machine-local rules from the
ignored
`.publication-boundary-local.json` (private reference-ID prefixes and private markers) when that
file is present, and cross-checks `.publication-boundary-allowlist.json` for entries that no
longer match anything (stale exceptions) or that name an untracked path.

Exit code `0` means no violations and no stale exceptions; `1` means violations or stale
allowlist entries were found (printed one per line); `2` means the allowlist or local config
itself is malformed (missing, invalid JSON, wrong shape, glob syntax in a path, duplicate
exception, or unknown rule name). See [AGENTS.md](../AGENTS.md) for the publication-boundary
policy this check enforces, and [`../.publication-boundary-allowlist.json`](../.publication-boundary-allowlist.json)
for the current reviewed exceptions.

**What it does not cover**: it is a fixed set of regex rules, not a semantic reviewer. It does not
catch every way a private identifier could be written (only the patterns above), does not inspect
binary files or git history, and does not evaluate whether an example is realistic or safe to
publish — only whether it matches a known leak pattern.

This check also runs as a pre-commit hook (id `publication-boundary`); see
[`../.pre-commit-config.yaml`](../.pre-commit-config.yaml).

## Publication boundary unit tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

As of 2026-07-21 this discovers one file, [`../tests/test_publication_boundary.py`](../tests/test_publication_boundary.py),
containing 5 tests. They exercise the checker's logic directly (`find_matches`, `audit`,
`build_local_rules`, `load_local_rules`) against synthetic in-memory fixtures, not the real repo
tree: every rule fires on a constructed sample, an allowlist exception suppresses only its exact
`(path, rule)` pair, a stale exception is reported, a local-only exception is not flagged stale
when local rules are inactive, and a missing local config file yields no local rules.

**What it does not cover**: whether the *current* tracked tree passes — that's the job of running
the checker script itself, above. These tests only confirm the checker's matching and
allowlist/staleness logic behaves as designed.

The same command also runs as the pre-commit hook `publication-boundary-tests`, pinned to
`test_publication_boundary.py` specifically (see
[`../.pre-commit-config.yaml`](../.pre-commit-config.yaml)).

## session-inspect fixture suite

```bash
python3 -m unittest discover -s session-inspect/tests -p 'test_*.py'
```

[`../session-inspect/tests/test_session_inspect.py`](../session-inspect/tests/test_session_inspect.py)
contains 22 tests (as of 2026-07-21) covering
[`../session-inspect/scripts/session_inspect.py`](../session-inspect/scripts/session_inspect.py).
It loads the script directly via `importlib` (not as an installed package) and drives it against
synthetic JSONL fixtures written to a temporary directory in `setUp`/`tearDown` — constructed
Codex rollout records (`session_meta`, `turn_context`, `response_item`, `compacted`, `event_msg`
token-count events) and constructed Claude Code transcript records. Fixtures are fabricated in the
test file itself, not captured from real sessions.

**What it does not cover**: there is no fixture corpus of real Codex or Claude Code session files,
so format drift in the actual harnesses (new event types, changed field names) is only caught if
someone updates the fixtures to match, or in practice — i.e., the parser breaking against a real
transcript. It also does not test the CLI argument-parsing surface or terminal output formatting
end-to-end; it calls the module's internal functions and inspects their return values or captured
stdout for specific inserted assertions, not a full command-line invocation in every mode
(`--insights`, `--json`, `diff`, etc. are each covered only insofar as individual tests target
them — see the file for exact coverage).

This suite is not wired into `.pre-commit-config.yaml`; it must be run explicitly.

## Shellcheck (pre-commit)

```bash
pre-commit run shellcheck --all-files
```

Configured in [`../.pre-commit-config.yaml`](../.pre-commit-config.yaml) via the
`koalaman/shellcheck-precommit` hook (pinned to `v0.11.0` as of 2026-07-21). Lints every shell
script pre-commit's file matching picks up, including [`../install.sh`](../install.sh) and any
`.sh` files bundled inside skill packages (for example
[`../pytest-profiling/scripts/profile-test.sh`](../pytest-profiling/scripts/profile-test.sh) and
the scripts under `gh-pr-review-comments/`).

**What it does not cover**: shellcheck is static analysis — it does not execute any script, so it
cannot catch a script that is syntactically clean but behaviorally wrong (wrong flag order, wrong
harness path, logic errors). It also only covers `.sh` files; Python scripts (e.g.
`check_publication_boundary.py`, `session_inspect.py`) are not linted by this hook.

Running the full pre-commit suite (`pre-commit run --all-files`) executes shellcheck and both
publication-boundary hooks together; running `pre-commit` with no arguments (as a git hook) only
checks staged files.

## `install.sh --dry-run`

```bash
./install.sh --dry-run
```

Reads the machine-local `install.conf` manifest (see
[`../install.conf.sample`](../install.conf.sample)) and reports, without writing anything, what
each skill's symlink state is: correctly linked, would-be-linked, would-be-removed, or — most
importantly — a **detached copy**: a real directory or file sitting at a harness path instead of a
symlink back into this repo. Detached copies are the drift condition [AGENTS.md](../AGENTS.md)
exists to prevent.

**What it does not cover**: it requires a local `install.conf` to exist (copied from
`install.conf.sample` and edited per machine) and inspects only the current machine's harness
directories — it says nothing about another machine's install state, and it does not validate
skill content, only linkage. It is not run in CI or pre-commit; it is a manual, per-machine
diagnostic.

## What "verified" means for claims on this docs site

A behavior statement on any page in `docs/` is "verified" when it was checked directly against a
primary source — the relevant `SKILL.md`, a bundled script, a test file, or a config file such as
`install.conf.sample` or `.pre-commit-config.yaml` — by an agent reading that source, dated to
2026-07-21. It does not mean the behavior was exercised end-to-end by running the skill in a live
harness. Where a docs page could not confirm a claim against a source, it says so explicitly
("unverified") rather than repeating it as fact. Where sources disagreed with each other, the
higher-fidelity source — code and test files over prose such as [`../README.md`](../README.md) —
was preferred, and the disagreement is noted on the relevant page.

## Coverage gap: most skills have no automated tests

Automated coverage in this repository is narrow. As of 2026-07-21, exactly two packages ship a
test suite:

| Package | Tests | What's tested |
| --- | --- | --- |
| repo-level publication boundary (`scripts/check_publication_boundary.py`) | 5 (`tests/test_publication_boundary.py`) | Rule matching, allowlist/staleness logic — synthetic fixtures only |
| `session-inspect` | 22 (`session-inspect/tests/test_session_inspect.py`) | Codex/Claude JSONL parsing, token accounting, child-session lineage — synthetic fixtures only |

Every other skill package in this repository — including `braindump-intake`, `gh-issues`,
`git-gtr-worktrees`, `gpt-5.6-prompting`, `obsidian-personal`, `pytest-profiling`, `retro`,
`workflow-fanout-checklist`, and the packages marked historical in
[`../README.md`](../README.md) (`accessibility-testing`, `gh-pr-review-comments`,
`plan-mode-tdd`, `s3-troubleshooting`) — has no `tests/` directory and no automated check of its
own. See [`../install.conf.sample`](../install.conf.sample) for the full skill list and
[skills.md](skills.md) for what each one does.

For these skills, `SKILL.md` is prescriptive guidance for an agent to follow, not code with a
test suite behind it. The `pytest-profiling` scripts (`../pytest-profiling/scripts/`) are shell
and Python tooling that shellcheck lints syntactically (see above) but that has no unit or
integration tests of its own. Whether the guidance in an untested `SKILL.md` produces correct
agent behavior is verified only by using the skill and observing the outcome — there is no
command that checks it mechanically. Treat instructions in an untested skill package as unverified
in the sense used on this page: read from source, not exercised by a test.

## Example: running everything locally

Illustrative — placeholders stand in for a real checkout path and skill name.

```bash
cd ~/path/to/agent-skills

# 1. Publication boundary: does the tracked tree leak private data?
python3 scripts/check_publication_boundary.py

# 2. Publication boundary checker's own unit tests
python3 -m unittest discover -s tests -p 'test_*.py'

# 3. session-inspect parser tests
python3 -m unittest discover -s session-inspect/tests -p 'test_*.py'

# 4. Shell script lint
pre-commit run shellcheck --all-files

# 5. Symlink/drift state for this machine (requires install.conf)
./install.sh --dry-run
```

A clean run of 1–4 plus no detached copies in 5 is the full extent of what "checks pass" means in
this repository. It does not mean every `SKILL.md` in `<skill-name>/SKILL.md` has been exercised —
see the coverage gap above.
