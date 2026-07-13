# Supported session formats

## Codex

Search root: `~/.codex/sessions`.

The inspector streams rollout JSONL and recognizes:

- `session_meta` for the thread ID, working directory, and initial timestamp.
- `turn_context` for effective model and reasoning effort.
- `response_item` function/custom tool calls for commands and output sizes.
- Top-level `compacted` records for full context-compaction count. The paired
  `event_msg` `context_compacted` notification is not counted again.
- `event_msg` `token_count` records; the latest cumulative
  `total_token_usage` snapshot is authoritative and must not be summed.

For per-model usage, attribute the delta between consecutive cumulative token
snapshots to the active `turn_context.model`. Codex records cached input reads
as a subset of native `input_tokens`, and separates reasoning from total output;
it does not record cache writes. `uncached_input_tokens` subtracts cache reads
from native input so uncached input + cache reads + output reconciles to total.

Both direct `exec_command` calls and current JavaScript-orchestrated `exec` calls
are supported.

Native Codex child lineage comes from `sub_agent_activity` records with
`kind: started`, linked back to the corresponding `spawn_agent` call by
`event_id`. Resolve the durable `agent_thread_id` to its rollout and verify
descendants recursively. A spawn with no start record or a start whose rollout
cannot be found is reported as unresolved rather than included in token totals.

For shell-launched agents, require launch provenance from the command and a
durable ID from either an explicit session/resume argument or captured output.
Codex `--json` emits `thread.started`; Claude JSON/stream output emits a `system`
`init` object with `session_id`. Long-running Codex tools may return a cell ID and
deliver that output through a later `wait`, so preserve the launch-call → cell →
wait-call chain. Do not infer children from arbitrary UUIDs printed later.

## Claude Code

Search root: `~/.claude/projects`.

Claude transcripts may repeat evolving snapshots of the same assistant message.
Deduplicate usage by `message.id` and tool calls by tool-use ID before summing.
Recognize `Bash`, `Read`, and `Skill` tool blocks for commands, read paths, and
skills.

Count `system` records with `subtype: compact_boundary` as full context
compactions. Do not double-count `isCompactSummary` user records or include
`microcompact_boundary` maintenance events in this count.

Group token usage by the deduplicated message's `message.model`. Claude records
cache reads and cache-creation writes separately from native input, so
`uncached_input_tokens` equals native input. Current transcripts do not separate
reasoning from normal output; report both subfields as unavailable unless a
usage record explicitly provides a reasoning/thinking counter.

Omit all-zero model buckets such as Claude API error messages labeled
`<synthetic>`. The top-level model is the latest observed model, not necessarily
the only model used in the session.

Native Claude subagents live below the parent transcript's artifact directory at
`<session>/subagents/agent-*.jsonl`. Their embedded `sessionId` may equal the
parent ID, so use the artifact filename as the child ID. Inspect and aggregate
these transcripts separately; do not mutate the parent's direct counters.

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
Session diffs include both aggregate and per-model token deltas. Missing models
compare against zero, while provider counters recorded as unavailable remain
unavailable rather than being treated as zero.

`tokens` and `tokens_by_model` are always direct-session values. Child and
inclusive aggregates use normalized uncached-input, cache-read, cache-write,
output, reasoning/normal-output, and total fields. Any aggregate component stays
unavailable when one contributing session does not expose that counter.
Diff JSON provides direct, child-only, and inclusive deltas separately; compact
human output keeps the existing direct delta and adds one child/inclusive line
only when either session has child lineage.
