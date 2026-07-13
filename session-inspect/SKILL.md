---
name: session-inspect
description: Inspect and compare local Codex rollout and Claude Code JSONL sessions without network access or transcript writes. Use when an agent needs commands, compaction counts, direct, child, inclusive, total, or per-model token usage, input/output and cache breakdowns, files or skills read, child-session lineage, delegated Codex model/effort provenance, session metadata, or a compact diff between past coding-agent sessions.
---

# Session Inspect

Use the bundled read-only inspector instead of loading raw transcripts into context:

```bash
INSPECT="$HOME/.agents/skills/session-inspect/scripts/session_inspect.py"
python3 "$INSPECT" inspect <session-id-or-jsonl-path>
python3 "$INSPECT" diff <session-a> <session-b>
```

The neutral path works for every harness after installation. The command searches
`~/.codex/sessions` and `~/.claude/projects`; use `--codex-root` or `--claude-root`
for fixtures or archives.

Default human output is a four- or five-line summary designed to be relayed
directly without reformatting. Start with it. Use `--verbose` only when capped
per-model details and command/read/skill lists are needed. `--all` implies
verbose output and removes those caps; use `--full-commands` only when exact
command bodies are necessary.

Use `--json` only for structured downstream processing. It keeps the existing
capped schema unless combined with `--all`; when only a few fields are needed,
filter at the command boundary (for example with `jq`) before returning output
to model context. Do not load verbose or JSON output merely to rewrite the
compact report in prose.

Compact session diffs report direct, child, and inclusive token deltas plus
counts of command, read-path, and skill changes. Use `--verbose` for per-model
deltas and the changed values themselves.

Direct-session fields keep their original meaning. Native Codex subagents,
Claude `subagents/` transcripts, and shell-launched Codex/Claude sessions are
reported separately as `child_sessions`, `child_tokens`, and `inclusive_tokens`;
unresolved child launches remain visible. The compact report adds only a one-line
child summary when lineage exists; use verbose or JSON output to inspect lineage
records.

Inspection is strictly local and read-only. Do not combine it with export, copy,
snapshot, or mutation steps unless the user explicitly requests a separate write
operation.

Read [formats.md](references/formats.md) only when extending or debugging a parser.
