# session-inspect

`session-inspect` is a read-only Python inspector for local Codex rollout and Claude Code JSONL
session transcripts. It requires no network access and does not write to transcripts. It extracts
model and effort,
duration, compaction count, token usage (direct, child, inclusive, and per-model), input/output and
cache breakdowns, tool and command activity, files and skills read, child-session lineage, and
Codex delegation provenance without loading the raw transcript into context. All figures are
heuristic measurements from evolving on-disk formats, not billing-authoritative (see
[Limitations](#limitations)).

## Status

Active. Its default harness mapping in
[`install.conf.sample`](../install.conf.sample) is:

```text
session-inspect         claude codex agents
```

It is linked by default into Claude Code (`~/.claude/skills`), Codex (`~/.codex/skills`), and the
neutral shared root (`~/.agents/skills`). The neutral installation gives the SKILL.md a
harness-independent script path.

The `description` frontmatter triggers it for session summaries and diffs; users can invoke it
directly through the bundled Codex `agents/openai.yaml` `default_prompt`. It wraps a CLI, not an
interactive agent.

## Triggers

Use it to inspect a past local coding-agent session for:

- commands run, or compaction counts;
- token usage in any breakdown — direct, child, inclusive, total, or per-model;
- input/output and cache breakdowns;
- files or skills read during the session;
- child-session lineage;
- delegated Codex model/effort provenance;
- session metadata; or
- a compact diff between two past sessions.

It inspects existing local artifacts without network access or transcript writes; it does not
capture, export, or mutate them.

## Prerequisites

- **Python 3** with the standard library. The Codex-config fallback reads TOML via `tomllib`, which
  requires Python 3.11 or newer; without it, config-derived model/effort simply reports as
  unavailable rather than failing.
- **No network, no auth, no third-party packages.** The script imports only `argparse`, `json`,
  `os`, `re`, `shlex`, `sys`, `typing`, `collections`, `datetime`, and `pathlib`.
- **Local session artifacts** to read: Codex rollouts under `~/.codex/sessions` and Claude Code
  transcripts under `~/.claude/projects` by default (override with the root options below).
- No dependency on other skills.

`ccusage` appears only as an external point of comparison in the worked example below; it is
**not** required to run `session-inspect`.

## Read/write and safety boundaries

**Reads only.** The inspector opens session transcripts, nested child transcripts, Claude
`subagents/` and `codex-runner` artifact files, matching Codex rollouts, and optionally
`~/.codex/config.toml` — all for reading. It has no export, copy, snapshot, or mutation code and
makes no model calls.

**Writes nothing**; output goes to stdout and diagnostics to stderr. The SKILL.md keeps inspection
separate from export, copy, snapshot, and mutation steps unless the user explicitly requests a
separate write operation.

**Human-facing / external:** the printed summary is the only output. Nothing is sent anywhere; the
relevant caution is privacy, not mutation.

### Privacy

Default compact output is bounded and omits path and list values, but richer output can reproduce
sensitive strings that live in the source transcripts. Depending on the mode, the output can surface:

- file paths — including paths leaked inside error messages, the session `cwd`, and skill/read paths
  reconstructed from shell commands;
- exact command bodies (with `--full-commands`) and repository or project names embedded in them;
- delegation metadata (delegated Codex model/effort, thread IDs, agent descriptions);
- config-derived model and reasoning-effort values;
- session IDs and parent/child session IDs; and
- child transcript data pulled in from nested subagent and `codex-runner` sessions.

Review verbose, `--all`, `--full-commands`, and `--json` output before sharing. To reduce exposure,
inspect an explicit transcript path or point root options at a temporary or archival directory
rather than live session roots (see [Compatibility](#compatibility-and-version-notes)).

## Typical workflow

1. Start with one session's compact summary. Preserve reported values and distinguish script output
   from interpretation; present raw output verbatim when requested or reformat it when useful.
2. Add `--insights` when deterministic diagnostics (child-token share, cache-read ratio,
   unresolved-child impact, unavailable counters, Codex snapshot stability) would help. These are
   mechanical observations; label any causal interpretation you add separately.
3. Use `--verbose` for capped per-model detail and command/read/skill lists; use `--all` or
   `--full-commands` only when caps or command truncation matter.
4. Use `diff` to compare two past sessions when the question is about what changed between them.
5. Use `--json` for structured downstream processing and filter it (for example with `jq`) before
   returning it to model context.

### Command and option reference

Invoke the bundled script directly. The neutral installation provides a stable cross-harness path:

```bash
INSPECT="$HOME/.agents/skills/session-inspect/scripts/session_inspect.py"
python3 "$INSPECT" inspect <target>
python3 "$INSPECT" diff <target-a> <target-b>
```

**Subcommands and arity.** There are two subcommands. `inspect` takes exactly **one** target;
`diff` takes exactly **two**. A subcommand is required — running with none exits non-zero.

**Global-option placement.** `--codex-root`, `--claude-root`, and `--codex-home` are defined on the
top-level parser, so they must appear **before** the subcommand name, not after the targets:

```bash
python3 "$INSPECT" --codex-root ./fixtures/codex --claude-root ./fixtures/claude inspect <target>
```

**Target forms.** A target is one of:

- a path to a `.jsonl` transcript file (used directly);
- a bare session ID or substring, resolved by searching the Codex root (`*<target>*.jsonl`) and the
  Claude root (`<target>.jsonl`); or
- a harness-prefixed form, `codex:<id-or-path>` or `claude:<id-or-path>`, to restrict resolution to
  one harness.

If a bare target matches more than one session, or matches none, resolution fails (see
[exit codes](#exit-codes-and-errors)).

**Per-subcommand options** (apply to both `inspect` and `diff` unless noted):

| Option | Effect |
| --- | --- |
| `--json` | Emit the structured result as sorted, indented JSON instead of text. |
| `--insights` | *(inspect only)* Append deterministic token/lineage/availability/snapshot diagnostics. |
| `-v`, `--verbose` | Show capped detailed output (per-model usage, command/read/skill lists, deltas). |
| `--all` | Imply verbose **and** remove item caps (uncapped lists; JSON expands to full schema). |
| `--full-commands` | Preserve multiline command bodies instead of flattening and truncating them. |
| `--max-items N` | Cap list length (default 10); must be ≥ 1. |
| `--command-chars N` | Truncate flattened commands to N chars (default 200); must be ≥ 20. |

**How verbosity, `--all`, and `--full-commands` interact.** Compact output prints a four-line
summary plus optional lines for children, skipped invalid JSON, and token-snapshot regressions.
`--verbose` switches to the detailed renderer with lists and per-model tables, still capped at
`--max-items` and with commands flattened and truncated to `--command-chars`. `--all` implies
verbose and lifts the caps. `--full-commands` is orthogonal: it stops command flattening/truncation
so exact bodies (including newlines) are shown — wherever command bodies are rendered at all,
which means verbose/`--all` output (and `inspect --json`); the compact renderers print no command
bodies for it to affect.

**Output caps.** List fields (commands, read paths, skills, delegations, child sessions, unresolved
children) are truncated to `--max-items` unless `--all` is given; omitted counts are reported so you
know to rerun with `--all`. Command text is truncated to `--command-chars` unless `--full-commands`
is set.

**JSON behavior.** `--json` prints the result dict with `sort_keys=True` and two-space indentation.
For `inspect`, it keeps the same **capped** schema as text output unless combined with `--all`;
`--insights` adds an `insights` key. For `diff`, `--json` emits the raw, uncapped diff structure
regardless of `--all` or `--max-items`. Filter JSON at the command boundary before it enters model
context rather than dumping the full structure.

### Exit codes and errors

The tool exits with code **2** on ambiguity and error conditions — an unresolved or ambiguous
target, an unreadable/empty or unsupported JSONL file, an OS error, or invalid options such as
`--max-items` below 1 or `--command-chars` below 20. Ambiguous matches print the candidate
harness/path list so the caller can disambiguate with a prefix or explicit path. Successful runs
exit 0.

## Bundled resources

- [`scripts/session_inspect.py`](../session-inspect/scripts/session_inspect.py) — the entire
  inspector: harness detection, target resolution, Codex and Claude parsers, child-lineage
  resolution, delegation provenance, the compact/verbose/JSON renderers, insights, and diff. This is
  the only executable; the SKILL.md wraps it directly.
- [`references/formats.md`](../session-inspect/references/formats.md) — the parser contract:
  which record types each harness contributes, the monotonic high-water token policy, per-model
  attribution rules, child-lineage and shell-launch detection, and the output-economy rules. Read it
  only when extending or debugging a parser.
- [`agents/openai.yaml`](../session-inspect/agents/openai.yaml) — Codex interface metadata
  (`display_name`, `short_description`, `default_prompt`) so the skill is user-invocable in that
  harness.
- `tests/test_session_inspect.py` — the automated test suite.

## Limitations

- **Heuristic, not billing-authoritative.** The token figures are the inspector's own reconstruction
  from on-disk snapshots and per-model delta attribution; they are not an authoritative bill. The
  worked comparison below makes this concrete: reading the *same* long Codex session concurrently,
  `session-inspect` reported roughly 22.86M direct / 24.38M inclusive tokens while `ccusage 20.0.17`
  reported 23,499,677 total tokens for the matching parent. The two tools disagree because their
  snapshot and child-aggregation rules differ; treat any inspector's numbers as tool-specific
  measurements, not interchangeable ground truth.
- **High-water snapshot rules (Codex).** Codex cumulative `total_token_usage` snapshots are accepted
  into a monotonic high-water; a snapshot in which any cumulative field drops below the accepted
  high-water is rejected, the last coherent value is held, and a warning is emitted (even without
  `--insights`). A later snapshot is accepted only after all its present fields recover. Reported
  totals therefore reflect the stable high-water, which can lag the latest raw snapshot.
- **Best-effort child lineage.** Native Codex children (via `sub_agent_activity`), Claude
  `subagents/` transcripts, and shell-launched Codex/Claude sessions are resolved only when a
  durable ID and its artifact can be found; a spawn with no start record, an uncaptured session ID,
  or a rollout that cannot be located is reported as *unresolved* and excluded from inclusive
  totals rather than guessed at.
- **Best-effort per-model attribution.** Codex per-model usage attributes each inter-snapshot delta
  to the `turn_context.model` active at the time; Claude groups by the deduplicated message's
  `message.model`. Attribution is approximate when the model changes between accounting points.
- **Unavailable fields.** Codex does not record cache-**write** tokens, so that field is always
  unavailable for Codex. Claude transcripts currently do not separate reasoning from normal output,
  so both are reported unavailable unless a usage record explicitly carries a reasoning/thinking
  counter. Any aggregate stays unavailable if a contributing session lacks that counter — unavailable
  is never silently treated as zero.
- **Read-path and command heuristics.** Read paths and skills are reconstructed conservatively from
  a fixed set of shell readers/searchers and from `Read`/`Skill`/`view_image` calls; commands inside
  heredoc bodies are stripped, and unusual command shapes may be missed. Skills are additionally
  inferred from any read path ending in `SKILL.md`.
- **Parser limits tied to evolving formats.** The parser depends on current Codex and Claude Code
  artifact schemas (record types, field names, delegation layout) and needs updates as those
  harnesses change. Invalid JSON lines are counted and skipped.
- **Neutral-path assumption.** The documented invocation path resolves only where the skill is
  installed to the `~/.agents/skills` root; a machine whose local `install.conf` drops `agents`
  would need a harness-specific path instead.

## Compatibility and version notes

- **Artifact formats.** The Codex parser keys on `session_meta`, `turn_context`, `response_item`,
  `event_msg` (`token_count`, `sub_agent_activity`), and top-level `compacted` records; the Claude
  parser keys on `assistant`/`user`/`system` records, `message.usage`, and
  `subtype: compact_boundary`. These reflect the harnesses' current on-disk formats and are subject
  to change.
- **Comparison figures.** The `ccusage` example is pinned to `ccusage 20.0.17` and the model
  `gpt-5.6-sol`; the specific token totals are a one-off concurrent capture, not a stable benchmark.
- **Default roots and overrides.** Defaults are `~/.codex/sessions`, `~/.claude/projects`, and
  `~/.codex` (config home). Override with `--codex-root` / `--claude-root` / `--codex-home`, or the
  environment variables `SESSION_INSPECT_CODEX_ROOT`, `SESSION_INSPECT_CLAUDE_ROOT`, and
  `CODEX_HOME`.
- **Default caps.** `--max-items` defaults to 10 and `--command-chars` to 200.
- **Python floor.** The config-fallback path needs `tomllib` (Python 3.11+); on older interpreters
  config-derived model/effort degrades to unavailable.

## Example

This **illustrative** compact summary uses placeholder data. It shows default output: header,
direct/child/inclusive tokens, input/output cache breakdown, activity, and child lineage.

```text
codex <session-id> | <model>/<effort> | 1h04m | compactions=1
tokens direct=8.20M child=0 inclusive=8.20M
input uncached=250.0K cache-read=7.90M cache-write=unavailable | output=40.0K reasoning=18.0K
activity messages=20/48 tools=95 commands=70 reads=22 skills=6
children resolved=0 (native=0 shell=0) unresolved=0
```

### Real comparison against `ccusage`

These outputs were captured concurrently from a long Codex session. The `session-inspect` session
ID and identifying fields from the matching `ccusage` record were omitted.

`session-inspect` compact output:

```text
codex <session-id> | gpt-5.6-sol/high | 2h31m | compactions=1
tokens direct=22.86M child=1.51M inclusive=24.38M
input uncached=715.3K cache-read=22.06M cache-write=unavailable | output=86.3K reasoning=42.8K
activity messages=36/85 tools=181 commands=135 reads=35 skills=16
children resolved=10 (native=10 shell=0) unresolved=0
```

The matching `ccusage 20.0.17` record, selected from:

```bash
ccusage codex session --json --offline --no-cost
```

```json
{
  "inputTokens": 727279,
  "cacheReadTokens": 22681856,
  "cacheCreationTokens": 0,
  "outputTokens": 90542,
  "reasoningOutputTokens": 44854,
  "totalTokens": 23499677,
  "models": {
    "gpt-5.6-sol": {
      "cacheCreationTokens": 0,
      "cacheReadTokens": 22681856,
      "inputTokens": 727279,
      "isFallback": false,
      "outputTokens": 90542,
      "reasoningOutputTokens": 44854,
      "totalTokens": 23499677
    }
  }
}
```

The totals disagree even though the reads were concurrent: `session-inspect` reported about 22.86M
direct tokens and 24.38M inclusive tokens, while `ccusage` reported 23,499,677 tokens for the
matching parent session. Treat figures from different inspectors as tool-specific measurements;
their snapshot and child-session aggregation rules are not interchangeable.

## Tests

`tests/test_session_inspect.py` uses synthetic fixtures to test parsing, target resolution,
rendering, diffs, and delegation metadata.
