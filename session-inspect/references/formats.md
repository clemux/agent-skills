# Supported session formats

## Codex

Search root: `~/.codex/sessions`.

The inspector streams rollout JSONL and recognizes:

- `session_meta` for the thread ID, working directory, and initial timestamp.
- `turn_context` for effective model and reasoning effort.
- `response_item` function/custom tool calls for commands and output sizes.
- `event_msg` `token_count` records; the latest cumulative
  `total_token_usage` snapshot is authoritative and must not be summed.

Both direct `exec_command` calls and current JavaScript-orchestrated `exec` calls
are supported.

## Claude Code

Search root: `~/.claude/projects`.

Claude transcripts may repeat evolving snapshots of the same assistant message.
Deduplicate usage by `message.id` and tool calls by tool-use ID before summing.
Recognize `Bash`, `Read`, and `Skill` tool blocks for commands, read paths, and
skills.

For nested `codex-runner` agents, discover `agent-*.meta.json` beside the parent
session's artifact directory. Parse only the actual Codex invocation line from
the runner's Bash commands; ignore heredoc bodies. Explicit `-m`/`--model`,
`-c model_reasoning_effort=...`, and legacy `--effort` flags take precedence.
For resumes or inherited values, use the matching Codex rollout's
`turn_context`; current config is only a clearly labeled fallback when no rollout
is available.

## Safety and output economy

The script opens transcripts and optional Codex config only for reading. It has
no network or export code. Default human and JSON output cap lists and command
lengths, report omitted counts, and require explicit flags for expansion.
