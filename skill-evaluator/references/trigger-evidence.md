# Codex trigger-evidence semantics

The current documented `codex exec --json` stream includes thread, turn,
agent-message, reasoning, command-execution, file-change, MCP, web-search, and
plan events. It does not document a dedicated skill-activation event.

`scripts/evaluate_triggers.py` therefore uses a narrow observational signal:

- It creates a disposable Git repository.
- It copies only the candidate target skill into
  `.agents/skills/<name>/SKILL.md`.
- It runs the raw query without an explicit `$skill` mention.
- It marks `observed: true` only when a JSONL `command_execution` item
  references that exact copied `SKILL.md` path.

Interpret results conservatively:

- A positive observation is evidence that the executor consulted the skill file.
- No observed path is inconclusive. Codex could activate or load a skill through
  an event surface not exposed by this harness.
- A negative-query pass means only “the path was not observed at the selected
  threshold,” not “Codex proved the skill was inactive.”
- Event-schema changes can cause false negatives. Preserve raw `transcript.jsonl`
  and inspect it after Codex upgrades.
- Explicit skill invocation is the reliable mode for evaluating skill behavior;
  this harness is only for description-selection experiments.

For description work:

1. Draft realistic positive, negative, and near-boundary queries.
2. Split them into training and held-out sets before tuning.
3. Test the current and candidate descriptions with the same model and run count.
4. Prefer a candidate only when it improves held-out observations without obvious
   false-positive expansion.
5. Require human review before editing live frontmatter.

Do not build an automatic description-rewrite loop on this signal until Codex
documents a stable invocation event or the local event surface is independently
validated as complete.
