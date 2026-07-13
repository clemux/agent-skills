import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "session_inspect.py"
SPEC = importlib.util.spec_from_file_location("session_inspect", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


class SessionInspectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.codex_root = self.root / "codex"
        self.claude_root = self.root / "claude"
        self.codex_home = self.root / "codex-home"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_codex_stream_uses_latest_cumulative_tokens_and_extracts_reads(self) -> None:
        thread = "019f0000-0000-7000-8000-000000000001"
        rollout = self.codex_root / f"rollout-{thread}.jsonl"
        write_jsonl(
            rollout,
            [
                {"timestamp": "2026-01-01T00:00:00Z", "type": "session_meta", "payload": {"id": thread, "cwd": "/repo"}},
                {"timestamp": "2026-01-01T00:00:01Z", "type": "turn_context", "payload": {"model": "gpt-5.6-terra", "effort": "medium"}},
                {"timestamp": "2026-01-01T00:00:02Z", "type": "response_item", "payload": {"type": "function_call", "call_id": "call-1", "name": "exec_command", "arguments": json.dumps({"cmd": "cat /repo/AGENTS.md; sed -n '1,20p' /repo/demo.py"})}},
                {"timestamp": "2026-01-01T00:00:03Z", "type": "response_item", "payload": {"type": "function_call_output", "output": "abc"}},
                {"timestamp": "2026-01-01T00:00:04Z", "type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 100, "output_tokens": 10, "total_tokens": 110}}}},
                {"timestamp": "2026-01-01T00:00:05Z", "type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 140, "output_tokens": 20, "total_tokens": 160}}}},
            ],
        )
        result = MODULE.inspect_codex(rollout)
        self.assertEqual(result["session_id"], thread)
        self.assertEqual(result["tokens"]["total_tokens"], 160)
        self.assertEqual(result["tool_output_bytes"], 3)
        self.assertIn("/repo/AGENTS.md", result["read_paths"])
        self.assertIn("/repo/demo.py", result["read_paths"])

    def test_current_codex_js_exec_is_decoded(self) -> None:
        thread = "019f0000-0000-7000-8000-000000000002"
        rollout = self.codex_root / f"rollout-{thread}.jsonl"
        js = 'const r = await tools.exec_command({cmd:"cat /repo/SKILL.md",workdir:"/repo"}); text(r.output);'
        write_jsonl(
            rollout,
            [
                {"type": "session_meta", "payload": {"id": thread}},
                {"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": "call-2", "name": "exec", "input": js}},
            ],
        )
        result = MODULE.inspect_codex(rollout)
        self.assertEqual(result["commands"], ["cat /repo/SKILL.md"])
        self.assertEqual(result["skills"], ["/repo/SKILL.md"])

    def test_json_shaped_js_exec_and_fork_identity_are_supported(self) -> None:
        child = "019f0000-0000-7000-8000-000000000004"
        parent = "019f0000-0000-7000-8000-000000000005"
        rollout = self.codex_root / f"rollout-{child}.jsonl"
        js = 'const r = await tools.exec_command({"cmd":"cat /repo/child.md","workdir":"/repo"}); text(r.output);'
        write_jsonl(
            rollout,
            [
                {"type": "session_meta", "payload": {"id": child, "session_id": parent, "parent_thread_id": parent, "thread_source": "subagent"}},
                {"type": "response_item", "payload": {"type": "custom_tool_call", "call_id": "call-json", "name": "exec", "input": js}},
            ],
        )
        result = MODULE.inspect_codex(rollout)
        self.assertEqual(result["session_id"], child)
        self.assertEqual(result["parent_session_id"], parent)
        self.assertEqual(result["commands"], ["cat /repo/child.md"])

    def test_chained_commands_do_not_overattribute_later_arguments(self) -> None:
        command = (
            "R=/sessions/example.jsonl; jq -r '.type' \"$R\" | sort; "
            "python /tools/init_skill.py session-inspect --path /repo; "
            "rg --files -g 'SKILL.md' -g '*.py'"
        )
        self.assertEqual(MODULE.read_paths_from_command(command), ["/sessions/example.jsonl"])

    def test_redirections_and_later_lines_are_not_read_paths(self) -> None:
        command = "grep needle /repo/input.md 2>/dev/null\necho 'docs: add CLAUDE.md'\ncat /repo/actual.md"
        self.assertEqual(
            MODULE.read_paths_from_command(command),
            ["/repo/input.md", "/repo/actual.md"],
        )

    def test_loop_and_glob_inputs_are_preserved(self) -> None:
        command = "for f in content/chapters/*.md; do sed -n '1,20p' \"$f\"; done"
        self.assertEqual(
            MODULE.read_paths_from_command(command),
            ["content/chapters/*.md"],
        )

    def test_read_glob_and_loop_variable_are_reported(self) -> None:
        command = "V=/repo; for f in $V/content/*.md; do cat \"$f\"; done"
        self.assertEqual(MODULE.read_paths_from_command(command), ["/repo/content/*.md"])

    def test_unresolved_and_parameter_expansion_paths_are_omitted(self) -> None:
        command = (
            "for a in first second; do cat /repo/agent-$a.jsonl; done; "
            "for meta in /repo/*.meta.json; do cat \"${meta%.meta.json}.jsonl\"; done; "
            "cat \"$HOME/known.md\""
        )
        self.assertEqual(
            MODULE.read_paths_from_command(command),
            [str(Path.home() / "known.md")],
        )

    def test_claude_deduplicates_message_snapshots_and_tool_ids(self) -> None:
        session = "aaaaaaaa-1111-4222-8333-bbbbbbbbbbbb"
        transcript = self.claude_root / "project" / f"{session}.jsonl"
        message = {
            "id": "msg-1",
            "model": "claude-sonnet-4-6",
            "usage": {"input_tokens": 10, "cache_read_input_tokens": 20, "output_tokens": 3},
            "content": [
                {"type": "tool_use", "id": "tool-1", "name": "Bash", "input": {"command": "cat /repo/one.md"}},
                {"type": "tool_use", "id": "tool-2", "name": "Read", "input": {"file_path": "/repo/two.py"}},
                {"type": "tool_use", "id": "tool-3", "name": "Skill", "input": {"skill": "retro"}},
            ],
        }
        write_jsonl(
            transcript,
            [
                {"type": "user", "uuid": "u-1", "sessionId": session, "cwd": "/repo", "timestamp": "2026-01-01T00:00:00Z"},
                {"type": "assistant", "uuid": "a-1", "sessionId": session, "timestamp": "2026-01-01T00:00:01Z", "message": message},
                {"type": "assistant", "uuid": "a-2", "sessionId": session, "timestamp": "2026-01-01T00:00:02Z", "message": message},
                {"type": "user", "uuid": "u-tool", "sessionId": session, "timestamp": "2026-01-01T00:00:03Z", "message": {"content": [{"type": "tool_result", "tool_use_id": "tool-1", "content": "result bytes"}]}},
            ],
        )
        result = MODULE.inspect_claude(transcript, self.codex_root, self.codex_home)
        self.assertEqual(result["messages"], {"user": 1, "assistant": 1, "tool_results": 1})
        self.assertEqual(result["tokens"]["total_tokens"], 33)
        self.assertEqual(result["tool_counts"], {"Bash": 1, "Read": 1, "Skill": 1})
        self.assertEqual(result["skills"], ["retro"])
        self.assertEqual(result["tool_output_bytes"], 12)

    def test_heredoc_decoy_does_not_override_raw_exec_flags(self) -> None:
        command = """prompt=$(cat <<'PROMPT'
Do not mistake this -m pytest marker for a model.
PROMPT
)
codex exec -m gpt-5.6-terra -c model_reasoning_effort=medium \"$prompt\"
"""
        rows = MODULE.parse_codex_invocations(command)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["model"], "gpt-5.6-terra")
        self.assertEqual(rows[0]["effort"], "medium")
        self.assertEqual(rows[0]["model_source"], "explicit")

    def test_legacy_companion_flags_are_supported(self) -> None:
        rows = MODULE.parse_codex_invocations(
            "node /plugin/codex-companion.mjs task --model gpt-5.5 --effort high --prompt hello"
        )
        self.assertEqual(rows[0]["model"], "gpt-5.5")
        self.assertEqual(rows[0]["effort"], "high")
        self.assertEqual(rows[0]["mode"], "task")

    def test_resume_inherits_historical_rollout_context(self) -> None:
        parent_id = "cccccccc-1111-4222-8333-dddddddddddd"
        thread = "019f0000-0000-7000-8000-000000000003"
        parent = self.claude_root / "project" / f"{parent_id}.jsonl"
        write_jsonl(parent, [{"type": "user", "sessionId": parent_id, "message": {}}])
        artifact = parent.with_suffix("") / "subagents" / "workflows" / "wf-1"
        meta = artifact / "agent-abc.meta.json"
        meta.parent.mkdir(parents=True, exist_ok=True)
        meta.write_text(json.dumps({"agentType": "codex-runner", "description": "resume test"}), encoding="utf-8")
        nested = artifact / "agent-abc.jsonl"
        write_jsonl(
            nested,
            [
                {"type": "assistant", "sessionId": parent_id, "message": {"id": "m", "model": "claude-sonnet-4-6", "usage": {"output_tokens": 5}, "content": [{"type": "tool_use", "id": "t", "name": "Bash", "input": {"command": f"codex exec resume {thread}"}}]}},
            ],
        )
        rollout = self.codex_root / f"rollout-{thread}.jsonl"
        write_jsonl(rollout, [{"type": "turn_context", "payload": {"model": "gpt-5.6-luna", "effort": "low"}}])
        rows = MODULE.inspect_delegations(parent, self.codex_root, self.codex_home)
        self.assertEqual(rows[0]["thread_id"], thread)
        self.assertEqual(rows[0]["model"], "gpt-5.6-luna")
        self.assertEqual(rows[0]["model_source"], "rollout")
        self.assertEqual(rows[0]["effort"], "low")
        self.assertEqual(rows[0]["effort_source"], "rollout")

    def test_diff_reports_added_commands_and_token_delta(self) -> None:
        left = {"tokens": {"total_tokens": 10}, "commands": ["one"], "read_paths": [], "skills": []}
        right = {"tokens": {"total_tokens": 15}, "commands": ["one", "two"], "read_paths": [], "skills": []}
        diff = MODULE.diff_results(left, right)
        self.assertEqual(diff["token_delta"]["total_tokens"], 5)
        self.assertEqual(diff["commands"]["added"], ["two"])


if __name__ == "__main__":
    unittest.main()
