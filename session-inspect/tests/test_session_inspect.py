import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
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
                {"timestamp": "2026-01-01T00:00:03Z", "type": "compacted", "payload": {"window_number": 1}},
                {"timestamp": "2026-01-01T00:00:03Z", "type": "event_msg", "payload": {"type": "context_compacted"}},
                {"timestamp": "2026-01-01T00:00:03Z", "type": "compacted", "payload": {"window_number": 2}},
                {"timestamp": "2026-01-01T00:00:04Z", "type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 100, "output_tokens": 10, "total_tokens": 110}}}},
                {"timestamp": "2026-01-01T00:00:05Z", "type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 140, "output_tokens": 20, "total_tokens": 160}}}},
            ],
        )
        result = MODULE.inspect_codex(rollout)
        self.assertEqual(result["session_id"], thread)
        self.assertEqual(result["tokens"]["total_tokens"], 160)
        self.assertEqual(result["compactions"], 2)
        self.assertEqual(result["tool_output_bytes"], 3)
        self.assertIn("/repo/AGENTS.md", result["read_paths"])
        self.assertIn("/repo/demo.py", result["read_paths"])

    def test_codex_tokens_are_attributed_to_active_model_from_cumulative_deltas(self) -> None:
        rollout = self.codex_root / "rollout-model-switch.jsonl"
        write_jsonl(
            rollout,
            [
                {"type": "turn_context", "payload": {"model": "gpt-5.6-terra"}},
                {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 10, "reasoning_output_tokens": 4, "total_tokens": 110}}}},
                {"type": "turn_context", "payload": {"model": "gpt-5.6-luna"}},
                {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 160, "cached_input_tokens": 70, "output_tokens": 30, "reasoning_output_tokens": 10, "total_tokens": 190}}}},
            ],
        )
        result = MODULE.inspect_codex(rollout)
        self.assertEqual(
            result["tokens_by_model"],
            {
                "gpt-5.6-luna": {
                    "input_tokens": 60,
                    "uncached_input_tokens": 30,
                    "cache_read_tokens": 30,
                    "cache_write_tokens": None,
                    "output_tokens": 20,
                    "normal_output_tokens": 14,
                    "reasoning_output_tokens": 6,
                    "total_tokens": 80,
                },
                "gpt-5.6-terra": {
                    "input_tokens": 100,
                    "uncached_input_tokens": 60,
                    "cache_read_tokens": 40,
                    "cache_write_tokens": None,
                    "output_tokens": 10,
                    "normal_output_tokens": 6,
                    "reasoning_output_tokens": 4,
                    "total_tokens": 110,
                },
            },
        )
        self.assertEqual(sum(row["total_tokens"] for row in result["tokens_by_model"].values()), 190)
        self.assertEqual(
            sum(
                row["uncached_input_tokens"] + row["cache_read_tokens"] + row["output_tokens"]
                for row in result["tokens_by_model"].values()
            ),
            190,
        )

    def test_codex_interim_counter_regressions_do_not_double_count(self) -> None:
        rollout = self.codex_root / "rollout-regression.jsonl"
        write_jsonl(
            rollout,
            [
                {"type": "turn_context", "payload": {"model": "gpt-5.6-sol"}},
                {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 100, "cached_input_tokens": 60, "output_tokens": 10, "reasoning_output_tokens": 4, "total_tokens": 110}}}},
                {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 90, "cached_input_tokens": 55, "output_tokens": 9, "reasoning_output_tokens": 3, "total_tokens": 99}}}},
                {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 120, "cached_input_tokens": 75, "output_tokens": 15, "reasoning_output_tokens": 5, "total_tokens": 135}}}},
            ],
        )
        result = MODULE.inspect_codex(rollout)
        self.assertEqual(result["tokens"]["total_tokens"], 135)
        self.assertEqual(result["tokens_by_model"]["gpt-5.6-sol"]["total_tokens"], 135)
        self.assertEqual(result["tokens_by_model"]["gpt-5.6-sol"]["cache_read_tokens"], 75)
        self.assertEqual(result["token_snapshot_stability"]["rejected_regressions"], 1)

    def test_codex_active_rollout_holds_high_water_then_accepts_recovery(self) -> None:
        rollout = self.codex_root / "rollout-live-regression.jsonl"
        records = [
            {"type": "turn_context", "payload": {"model": "gpt-5.6-sol"}},
            {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 40_000_000, "cached_input_tokens": 36_000_000, "output_tokens": 530_000, "reasoning_output_tokens": 100_000, "total_tokens": 40_530_000}}}},
            {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 7_000_000, "cached_input_tokens": 6_000_000, "output_tokens": 420_000, "reasoning_output_tokens": 80_000, "total_tokens": 7_420_000}}}},
        ]
        write_jsonl(rollout, records)

        regressed = MODULE.inspect_codex(rollout)

        self.assertEqual(regressed["tokens"]["total_tokens"], 40_530_000)
        self.assertEqual(regressed["tokens_by_model"]["gpt-5.6-sol"]["total_tokens"], 40_530_000)
        self.assertEqual(
            regressed["token_snapshot_stability"],
            {
                "policy": "monotonic-high-water",
                "observed": 2,
                "accepted": 1,
                "rejected_regressions": 1,
                "regression_fields": {
                    "cached_input_tokens": 1,
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "reasoning_output_tokens": 1,
                    "total_tokens": 1,
                },
                "stable_total_tokens": 40_530_000,
                "latest_observed_total_tokens": 7_420_000,
            },
        )
        compact_args = MODULE.build_parser().parse_args(["inspect", "unused"])
        compact = MODULE.render_result(regressed, compact_args)
        self.assertIn("tokens direct=40.53M", compact)
        self.assertIn("warning token-snapshot-regressions=1", compact)
        self.assertNotIn("\ninsights\n", compact)

        records.append(
            {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 41_000_000, "cached_input_tokens": 37_000_000, "output_tokens": 820_000, "reasoning_output_tokens": 120_000, "total_tokens": 41_820_000}}}}
        )
        write_jsonl(rollout, records)
        recovered = MODULE.inspect_target(
            str(rollout), self.codex_root, self.claude_root, self.codex_home
        )

        self.assertEqual(recovered["tokens"]["total_tokens"], 41_820_000)
        self.assertEqual(recovered["tokens_by_model"]["gpt-5.6-sol"]["total_tokens"], 41_820_000)
        self.assertEqual(recovered["token_snapshot_stability"]["accepted"], 2)
        self.assertEqual(recovered["token_snapshot_stability"]["latest_observed_total_tokens"], 41_820_000)
        insights = MODULE.build_insights(recovered)
        self.assertEqual(insights["child_token_share"]["percent"], 0.0)
        self.assertEqual(insights["cache_read_ratio"]["percent"], 90.2)
        self.assertEqual(insights["unresolved_children"]["count"], 0)
        self.assertEqual(insights["unavailable_counters"], ["direct.cache_write_tokens"])
        insight_args = MODULE.build_parser().parse_args(["inspect", "unused", "--insights"])
        rendered = MODULE.render_result(recovered, insight_args)
        self.assertIn("\ninsights\n", rendered)
        self.assertIn("- token-snapshots: policy=monotonic-high-water", rendered)

        cli_args = [
            "--codex-root",
            str(self.codex_root),
            "--claude-root",
            str(self.claude_root),
            "--codex-home",
            str(self.codex_home),
            "inspect",
            str(rollout),
            "--json",
        ]
        default_stdout = io.StringIO()
        with redirect_stdout(default_stdout):
            self.assertEqual(MODULE.main(cli_args), 0)
        self.assertNotIn("insights", json.loads(default_stdout.getvalue()))

        insight_stdout = io.StringIO()
        with redirect_stdout(insight_stdout):
            self.assertEqual(MODULE.main([*cli_args, "--insights"]), 0)
        self.assertEqual(
            json.loads(insight_stdout.getvalue())["insights"]["cache_read_ratio"]["percent"],
            90.2,
        )

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
                {"type": "system", "subtype": "compact_boundary", "sessionId": session},
                {"type": "user", "isCompactSummary": True, "sessionId": session, "message": {"content": "summary"}},
                {"type": "system", "subtype": "microcompact_boundary", "sessionId": session},
                {"type": "system", "subtype": "compact_boundary", "sessionId": session},
                {"type": "user", "uuid": "u-tool", "sessionId": session, "timestamp": "2026-01-01T00:00:03Z", "message": {"content": [{"type": "tool_result", "tool_use_id": "tool-1", "content": "result bytes"}]}},
            ],
        )
        result = MODULE.inspect_claude(transcript, self.codex_root, self.codex_home)
        self.assertEqual(result["messages"], {"user": 1, "assistant": 1, "tool_results": 1})
        self.assertEqual(result["tokens"]["total_tokens"], 33)
        self.assertEqual(result["tool_counts"], {"Bash": 1, "Read": 1, "Skill": 1})
        self.assertEqual(result["skills"], ["retro"])
        self.assertEqual(result["tool_output_bytes"], 12)
        self.assertEqual(result["compactions"], 2)
        args = MODULE.build_parser().parse_args(["inspect", "unused"])
        compact = MODULE.render_result(result, args)
        self.assertIn("compactions=2", compact)
        self.assertIn("tokens direct=33 child=0 inclusive=33", compact)
        self.assertNotIn("path:", compact)
        self.assertLessEqual(len(compact.encode()), 600)
        verbose_args = MODULE.build_parser().parse_args(["inspect", "unused", "--verbose"])
        self.assertIn("compactions: 2", MODULE.render_result(result, verbose_args))

    def test_claude_tokens_are_grouped_by_message_model_with_cache_writes(self) -> None:
        transcript = self.claude_root / "project" / "models.jsonl"
        sonnet = {
            "id": "sonnet-message",
            "model": "claude-sonnet-5",
            "usage": {
                "input_tokens": 10,
                "cache_creation_input_tokens": 4,
                "cache_read_input_tokens": 20,
                "output_tokens": 6,
            },
            "content": [],
        }
        opus = {
            "id": "opus-message",
            "model": "claude-opus-4-8",
            "usage": {
                "input_tokens": 3,
                "cache_creation_input_tokens": 5,
                "cache_read_input_tokens": 7,
                "output_tokens": 8,
                "reasoning_output_tokens": 2,
            },
            "content": [],
        }
        synthetic_error = {
            "id": "synthetic-error",
            "model": "<synthetic>",
            "usage": {
                "input_tokens": 0,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
                "output_tokens": 0,
            },
            "content": [],
        }
        write_jsonl(
            transcript,
            [
                {"type": "assistant", "message": sonnet},
                {"type": "assistant", "message": sonnet},
                {"type": "assistant", "message": synthetic_error},
                {"type": "assistant", "message": opus},
            ],
        )
        result = MODULE.inspect_claude(transcript, self.codex_root, self.codex_home)
        self.assertEqual(result["tokens"]["total_tokens"], 63)
        self.assertEqual(
            result["tokens_by_model"],
            {
                "claude-opus-4-8": {
                    "input_tokens": 3,
                    "uncached_input_tokens": 3,
                    "cache_read_tokens": 7,
                    "cache_write_tokens": 5,
                    "output_tokens": 8,
                    "normal_output_tokens": 6,
                    "reasoning_output_tokens": 2,
                    "total_tokens": 23,
                },
                "claude-sonnet-5": {
                    "input_tokens": 10,
                    "uncached_input_tokens": 10,
                    "cache_read_tokens": 20,
                    "cache_write_tokens": 4,
                    "output_tokens": 6,
                    "normal_output_tokens": None,
                    "reasoning_output_tokens": None,
                    "total_tokens": 40,
                },
            },
        )
        args = MODULE.build_parser().parse_args(["inspect", "unused", "--verbose"])
        rendered = MODULE.render_result(result, args)
        self.assertIn("latest model: claude-opus-4-8", rendered)
        self.assertNotIn("<synthetic>", rendered)

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

    def test_codex_native_children_are_additive_and_report_failed_spawns(self) -> None:
        parent_id = "019f0000-0000-7000-8000-000000000010"
        child_id = "019f0000-0000-7000-8000-000000000011"
        parent = self.codex_root / f"rollout-{parent_id}.jsonl"
        child = self.codex_root / f"rollout-{child_id}.jsonl"
        write_jsonl(
            parent,
            [
                {"type": "session_meta", "payload": {"id": parent_id}},
                {"type": "turn_context", "payload": {"model": "gpt-parent"}},
                {"type": "response_item", "payload": {"type": "function_call", "name": "spawn_agent", "call_id": "call-ok", "arguments": json.dumps({"task_name": "child", "model": "gpt-child"})}},
                {"type": "event_msg", "payload": {"type": "sub_agent_activity", "kind": "started", "event_id": "call-ok", "agent_thread_id": child_id, "agent_path": "/root/child"}},
                {"type": "response_item", "payload": {"type": "function_call", "name": "spawn_agent", "call_id": "call-failed", "arguments": json.dumps({"task_name": "failed"})}},
                {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 25, "cached_input_tokens": 10, "output_tokens": 5, "total_tokens": 30}}}},
            ],
        )
        write_jsonl(
            child,
            [
                {"type": "session_meta", "payload": {"id": child_id, "parent_thread_id": parent_id, "thread_source": "subagent"}},
                {"type": "turn_context", "payload": {"model": "gpt-child", "effort": "medium"}},
                {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 20, "cached_input_tokens": 8, "output_tokens": 5, "total_tokens": 25}}}},
            ],
        )

        result = MODULE.inspect_target(str(parent), self.codex_root, self.claude_root, self.codex_home)

        self.assertEqual(result["tokens"]["total_tokens"], 30)
        self.assertEqual(
            result["child_summary"],
            {
                "resolved": 1,
                "unresolved": 1,
                "native_resolved": 1,
                "native_unresolved": 1,
                "shell_resolved": 0,
                "shell_unresolved": 0,
            },
        )
        self.assertEqual(result["child_sessions"][0]["child_id"], child_id)
        self.assertEqual(result["child_sessions"][0]["requested"]["task_name"], "child")
        self.assertEqual(result["child_tokens"]["total_tokens"], 25)
        self.assertEqual(result["inclusive_tokens"]["total_tokens"], 55)
        compact_args = MODULE.build_parser().parse_args(["inspect", "unused"])
        compact = MODULE.render_result(result, compact_args)
        self.assertIn("tokens direct=30 child=25 inclusive=55", compact)
        self.assertIn("children resolved=1 (native=1 shell=0) unresolved=1", compact)
        args = MODULE.build_parser().parse_args(["inspect", "unused", "--verbose"])
        self.assertIn("child sessions: resolved=1 unresolved=1 child_total=25 inclusive_total=55", MODULE.render_result(result, args))
        insights = MODULE.build_insights(result)
        self.assertEqual(insights["child_token_share"]["percent"], 45.5)
        self.assertEqual(insights["cache_read_ratio"]["percent"], 40.0)
        self.assertEqual(
            insights["unresolved_children"],
            {"count": 1, "inclusive_totals_exclude_unresolved": True},
        )

    def test_json_view_remains_capped_unless_all_is_requested(self) -> None:
        result = {
            "commands": [f"command-{index}" for index in range(12)],
            "read_paths": [],
            "skills": [],
            "delegations": [],
            "child_sessions": [],
            "unresolved_children": [],
        }
        default_args = MODULE.build_parser().parse_args(["inspect", "unused", "--json"])
        verbose_args = MODULE.build_parser().parse_args(["inspect", "unused", "--json", "--verbose"])
        all_args = MODULE.build_parser().parse_args(["inspect", "unused", "--json", "--all"])

        default_view = MODULE.view_result(result, default_args)
        self.assertEqual(default_view, MODULE.view_result(result, verbose_args))
        self.assertEqual(len(default_view["commands"]), 10)
        self.assertEqual(default_view["commands_omitted"], 2)
        self.assertEqual(len(MODULE.view_result(result, all_args)["commands"]), 12)

    def test_claude_native_subagent_tokens_are_separate_from_direct_tokens(self) -> None:
        parent_id = "aaaaaaaa-1111-4222-8333-cccccccccccc"
        parent = self.claude_root / "project" / f"{parent_id}.jsonl"
        child = parent.with_suffix("") / "subagents" / "agent-child.jsonl"
        write_jsonl(
            parent,
            [{"type": "assistant", "sessionId": parent_id, "message": {"id": "parent-message", "model": "claude-sonnet", "usage": {"input_tokens": 4, "output_tokens": 6}, "content": []}}],
        )
        write_jsonl(
            child,
            [{"type": "assistant", "sessionId": parent_id, "message": {"id": "child-message", "model": "claude-sonnet", "usage": {"input_tokens": 5, "cache_read_input_tokens": 10, "output_tokens": 5}, "content": []}}],
        )

        result = MODULE.inspect_target(str(parent), self.codex_root, self.claude_root, self.codex_home)

        self.assertEqual(result["tokens"]["total_tokens"], 10)
        self.assertEqual(result["child_summary"]["resolved"], 1)
        self.assertEqual(result["child_sessions"][0]["child_id"], "agent-child")
        self.assertEqual(result["child_tokens"]["total_tokens"], 20)
        self.assertEqual(result["inclusive_tokens"]["total_tokens"], 30)

    def test_codex_shell_children_follow_deferred_cell_outputs_and_deduplicate(self) -> None:
        parent_id = "019f0000-0000-7000-8000-000000000020"
        codex_child_id = "019f0000-0000-7000-8000-000000000021"
        claude_child_id = "aaaaaaaa-1111-4222-8333-dddddddddddd"
        parent = self.codex_root / f"rollout-{parent_id}.jsonl"
        codex_child = self.codex_root / f"rollout-{codex_child_id}.jsonl"
        claude_child = self.claude_root / "project" / f"{claude_child_id}.jsonl"
        self.assertIsNone(MODULE.launch_details("codex exec --help"))
        self.assertEqual(
            MODULE.launch_details(f"claude -p --session-id {claude_child_id} prompt"),
            ("claude", claude_child_id),
        )
        write_jsonl(
            parent,
            [
                {"type": "session_meta", "payload": {"id": parent_id}},
                {"type": "custom", "payload": {}},
                {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec", "call_id": "launch-codex", "input": 'const r = await tools.exec_command({"cmd":"codex exec --json prompt"}); text(r.output);'}},
                {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "launch-codex", "output": "Script running with cell ID 75\n"}},
                {"type": "response_item", "payload": {"type": "function_call", "name": "wait", "call_id": "wait-codex", "arguments": json.dumps({"cell_id": "75"})}},
                {"type": "response_item", "payload": {"type": "function_call_output", "call_id": "wait-codex", "output": f'{{"type":"thread.started","thread_id":"{codex_child_id}"}}'}},
                {"type": "response_item", "payload": {"type": "custom_tool_call", "name": "exec", "call_id": "launch-claude", "input": 'const r = await tools.exec_command({"cmd":"claude --print --output-format json prompt"}); text(r.output);'}},
                {"type": "response_item", "payload": {"type": "custom_tool_call_output", "call_id": "launch-claude", "output": f'{{"type":"system","subtype":"init","session_id":"{claude_child_id}"}}'}},
                {"type": "response_item", "payload": {"type": "function_call", "name": "wait", "call_id": "wait-again", "arguments": json.dumps({"cell_id": "75"})}},
                {"type": "response_item", "payload": {"type": "function_call_output", "call_id": "wait-again", "output": f'{{"type":"thread.started","thread_id":"{codex_child_id}"}}'}},
            ],
        )
        write_jsonl(
            codex_child,
            [
                {"type": "session_meta", "payload": {"id": codex_child_id}},
                {"type": "turn_context", "payload": {"model": "gpt-child"}},
                {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 8, "output_tokens": 2, "total_tokens": 10}}}},
            ],
        )
        write_jsonl(
            claude_child,
            [{"type": "assistant", "sessionId": claude_child_id, "message": {"id": "m", "model": "claude-sonnet", "usage": {"input_tokens": 5, "output_tokens": 5}, "content": []}}],
        )

        result = MODULE.inspect_target(str(parent), self.codex_root, self.claude_root, self.codex_home)

        self.assertEqual(result["child_summary"]["shell_resolved"], 2)
        self.assertEqual(result["child_summary"]["shell_unresolved"], 0)
        self.assertEqual({row["child_id"] for row in result["child_sessions"]}, {codex_child_id, claude_child_id})
        self.assertEqual(result["child_tokens"]["total_tokens"], 20)

    def test_claude_bash_shell_child_is_linked_from_tool_result(self) -> None:
        parent_id = "aaaaaaaa-1111-4222-8333-eeeeeeeeeeee"
        child_id = "019f0000-0000-7000-8000-000000000030"
        parent = self.claude_root / "project" / f"{parent_id}.jsonl"
        child = self.codex_root / f"rollout-{child_id}.jsonl"
        write_jsonl(
            parent,
            [
                {"type": "assistant", "sessionId": parent_id, "message": {"id": "m1", "model": "claude-sonnet", "usage": {}, "content": [{"type": "tool_use", "id": "tool-1", "name": "Bash", "input": {"command": "codex exec --json prompt"}}]}},
                {"type": "user", "sessionId": parent_id, "message": {"content": [{"type": "tool_result", "tool_use_id": "tool-1", "content": f'{{"type":"thread.started","thread_id":"{child_id}"}}'}]}},
            ],
        )
        write_jsonl(
            child,
            [
                {"type": "session_meta", "payload": {"id": child_id}},
                {"type": "turn_context", "payload": {"model": "gpt-child"}},
                {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 7, "output_tokens": 3, "total_tokens": 10}}}},
            ],
        )

        result = MODULE.inspect_target(str(parent), self.codex_root, self.claude_root, self.codex_home)

        self.assertEqual(result["child_summary"]["shell_resolved"], 1)
        self.assertEqual(result["child_sessions"][0]["child_id"], child_id)
        self.assertEqual(result["child_sessions"][0]["relationship"], "shell")

    def test_diff_reports_added_commands_and_token_delta(self) -> None:
        left = {
            "compactions": 1,
            "child_summary": {"resolved": 1, "unresolved": 0},
            "tokens": {"total_tokens": 10},
            "child_tokens": {"total_tokens": 4},
            "inclusive_tokens": {"total_tokens": 14},
            "child_tokens_by_model": {"luna": {"total_tokens": 4}},
            "inclusive_tokens_by_model": {"luna": {"total_tokens": 4}, "terra": {"total_tokens": 10}},
            "tokens_by_model": {
                "terra": {"output_tokens": 2, "reasoning_output_tokens": None, "total_tokens": 10}
            },
            "commands": ["one"],
            "read_paths": [],
            "skills": [],
        }
        right = {
            "compactions": 3,
            "child_summary": {"resolved": 2, "unresolved": 0},
            "tokens": {"total_tokens": 15},
            "child_tokens": {"total_tokens": 9},
            "inclusive_tokens": {"total_tokens": 24},
            "child_tokens_by_model": {"luna": {"total_tokens": 9}},
            "inclusive_tokens_by_model": {"luna": {"total_tokens": 9}, "terra": {"total_tokens": 15}},
            "tokens_by_model": {
                "luna": {"output_tokens": 1, "reasoning_output_tokens": None, "total_tokens": 3},
                "terra": {"output_tokens": 3, "reasoning_output_tokens": None, "total_tokens": 12},
            },
            "commands": ["one", "two"],
            "read_paths": [],
            "skills": [],
        }
        diff = MODULE.diff_results(left, right)
        self.assertEqual(diff["token_delta"]["total_tokens"], 5)
        self.assertEqual(diff["token_delta_by_model"]["luna"]["total_tokens"], 3)
        self.assertEqual(diff["token_delta_by_model"]["terra"]["output_tokens"], 1)
        self.assertIsNone(diff["token_delta_by_model"]["terra"]["reasoning_output_tokens"])
        self.assertEqual(diff["child_token_delta"]["total_tokens"], 5)
        self.assertEqual(diff["inclusive_token_delta"]["total_tokens"], 10)
        self.assertEqual(diff["child_token_delta_by_model"]["luna"]["total_tokens"], 5)
        self.assertEqual(diff["commands"]["added"], ["two"])
        args = MODULE.build_parser().parse_args(["diff", "left", "right"])
        rendered = MODULE.render_diff(diff, args)
        self.assertIn("token delta (right-left) direct=+5 child=+5 inclusive=+10", rendered)
        self.assertIn("changes commands=+1/-0 reads=+0/-0 skills=+0/-0", rendered)
        self.assertNotIn("token delta by model", rendered)
        self.assertLessEqual(len(rendered.splitlines()), 4)
        verbose_args = MODULE.build_parser().parse_args(["diff", "left", "right", "--verbose"])
        rendered = MODULE.render_diff(diff, verbose_args)
        self.assertIn("token delta by model (right-left):", rendered)
        self.assertIn("reasoning_output=unavailable", rendered)
        self.assertIn("child_total=+5 inclusive_total=+10", rendered)
        self.assertIn("compactions=1", rendered)
        self.assertIn("compactions=3", rendered)


if __name__ == "__main__":
    unittest.main()
