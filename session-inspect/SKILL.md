---
name: session-inspect
description: Inspect and compare local Codex rollout and Claude Code JSONL sessions without network access or transcript writes. Use when an agent needs commands, total or per-model token usage, input/output and cache breakdowns, files or skills read, delegated Codex model/effort provenance, session metadata, or a compact diff between past coding-agent sessions.
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

Default output is compact and clearly reports omitted items. Use `--all` to show
all items, `--full-commands` only when exact command bodies are necessary, and
`--json` for structured downstream processing.

Session diffs report aggregate and per-model token deltas alongside command,
read-path, and skill changes.

Inspection is strictly local and read-only. Do not combine it with export, copy,
snapshot, or mutation steps unless the user explicitly requests a separate write
operation.

Read [formats.md](references/formats.md) only when extending or debugging a parser.
