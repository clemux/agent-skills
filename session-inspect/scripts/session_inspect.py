#!/usr/bin/env python3
"""Compact, read-only inspection of Codex and Claude Code JSONL sessions."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
HEREDOC_RE = re.compile(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?")
JS_CMD_RE = re.compile(r"(?:\bcmd|\"cmd\")\s*:\s*(\"(?:\\.|[^\"\\])*\")", re.S)
THREAD_CONTEXT_RE = re.compile(
    r"(?:CODEX_THREAD_ID|thread[_ ]id|session)\s*[=:]\s*[\\\"']?"
    r"([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})",
    re.I,
)


class InspectError(RuntimeError):
    pass


def iter_jsonl(path: Path) -> Iterable[tuple[dict[str, Any], int]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                yield {"_invalid_json": True}, number
                continue
            if isinstance(value, dict):
                yield value, number


def ordered_add(items: list[str], seen: set[str], value: Any) -> None:
    if value is None:
        return
    text = str(value).strip()
    if text and text not in seen:
        seen.add(text)
        items.append(text)


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def duration_seconds(first: datetime | None, last: datetime | None) -> float | None:
    if first is None or last is None:
        return None
    return max(0.0, (last - first).total_seconds())


def update_times(
    first: datetime | None, last: datetime | None, value: Any
) -> tuple[datetime | None, datetime | None]:
    current = parse_time(value)
    if current is None:
        return first, last
    return current if first is None or current < first else first, current if last is None or current > last else last


def decode_json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    try:
        result = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return result if isinstance(result, dict) else {}


def value_bytes(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        return len(value.encode("utf-8"))
    return len(json.dumps(value, ensure_ascii=False).encode("utf-8"))


def usage_delta(current: dict[str, Any], previous: dict[str, Any]) -> dict[str, int]:
    delta: dict[str, int] = {}
    for key, value in current.items():
        if not isinstance(value, (int, float)):
            continue
        difference = int(value) - int(previous.get(key, 0) or 0)
        delta[key] = difference if difference >= 0 else int(value)
    return delta


def normalized_model_tokens(
    usage: dict[str, int], *, harness: str, available: set[str]
) -> dict[str, int | None]:
    provider_input = int(usage.get("input_tokens", 0))
    output = int(usage.get("output_tokens", 0))
    reasoning_key = "reasoning_output_tokens"
    reasoning = int(usage.get(reasoning_key, 0)) if reasoning_key in available else None
    normal_output = max(0, output - reasoning) if reasoning is not None else None
    if harness == "codex":
        cache_read = int(usage.get("cached_input_tokens", 0)) if "cached_input_tokens" in available else None
        cache_write = None
        uncached_input = max(0, provider_input - cache_read) if cache_read is not None else None
    else:
        cache_read = int(usage.get("cache_read_input_tokens", 0))
        cache_write = int(usage.get("cache_creation_input_tokens", 0))
        uncached_input = provider_input
    return {
        "input_tokens": provider_input,
        "uncached_input_tokens": uncached_input,
        "cache_read_tokens": cache_read,
        "cache_write_tokens": cache_write,
        "output_tokens": output,
        "normal_output_tokens": normal_output,
        "reasoning_output_tokens": reasoning,
        "total_tokens": int(usage.get("total_tokens", 0)),
    }


def commands_from_js(value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    commands: list[str] = []
    for match in JS_CMD_RE.finditer(value):
        try:
            decoded = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(decoded, str):
            commands.append(decoded)
    return commands


def shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, comments=False, posix=True)
    except ValueError:
        return []


def shell_segments(command: str) -> list[list[str]]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return []
    segments: list[list[str]] = [[]]
    for token in tokens:
        if token and set(token) <= set(";&|"):
            if segments[-1]:
                segments.append([])
            continue
        segments[-1].append(token)
    return [segment for segment in segments if segment]


def clean_path_token(token: str) -> str:
    return token.strip("'\";,(){}[]")


def pathish(token: str, allow_glob: bool = False) -> bool:
    value = clean_path_token(token)
    forbidden = "<>" if allow_glob else "*?[<>"
    if not value or value in {"-", ".", ".."} or any(char in value for char in forbidden):
        return False
    if "$" in value or ("=" in value and not value.startswith(("./", "../"))):
        return False
    return (
        value.startswith(("/", "~/", "./", "../"))
        or "/" in value
        or value.endswith((".md", ".json", ".jsonl", ".toml", ".yaml", ".yml", ".py", ".sh"))
    )


def read_paths_from_command(command: str) -> list[str]:
    """Conservatively find explicit inputs to common read-only shell commands."""
    found: list[str] = []
    readers = {"cat", "less", "more", "head", "tail", "wc", "readlink"}
    searchers = {"rg", "grep", "jq", "sed", "find"}
    variables: dict[str, str] = {"HOME": str(Path.home())}
    command_without_heredocs = "\n".join(strip_heredoc_bodies(command))
    for match in re.finditer(r"(?:^|[;\n])\s*for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+([^;\n]+)", command_without_heredocs):
        values = shell_tokens(match.group(2))
        if len(values) == 1:
            variables[match.group(1)] = values[0]
    for segment in shell_segments(command_without_heredocs.replace("\n", ";")):
        for token in segment:
            assignment = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)=(.+)", token)
            if assignment:
                variables[assignment.group(1)] = assignment.group(2)
        index = next(
            (position for position, token in enumerate(segment) if Path(token).name in readers | searchers),
            None,
        )
        if index is None:
            continue
        base = Path(segment[index]).name
        tail = segment[index + 1 :]

        def resolved(item: str) -> str:
            def replace(match: re.Match[str]) -> str:
                name = match.group(1) or match.group(2)
                return variables.get(name, match.group(0))

            value = item
            for _ in range(3):
                expanded = re.sub(
                    r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))",
                    replace,
                    value,
                )
                if expanded == value:
                    break
                value = expanded
            return value

        candidates: list[str] = []
        if base in readers:
            candidates = [item for item in tail if not item.startswith("-")]
        elif base == "find":
            candidates = tail[:1]
        elif base in {"jq", "sed"}:
            non_options = [item for item in tail if not item.startswith("-")]
            candidates = non_options[1:] if len(non_options) > 1 else []
        elif base in {"rg", "grep"}:
            options_with_values = {"-g", "--glob", "-t", "--type", "-e", "--regexp", "-f", "--file", "--iglob", "--include", "--exclude"}
            positionals: list[str] = []
            skip_next = False
            for item in tail:
                if skip_next:
                    skip_next = False
                    continue
                if item in options_with_values:
                    skip_next = True
                    continue
                if item.startswith("-"):
                    continue
                positionals.append(item)
            candidates = positionals if "--files" in tail else positionals[1:]
        for candidate in candidates:
            candidate = resolved(candidate)
            if pathish(candidate, allow_glob=True):
                found.append(clean_path_token(candidate))
    return found


def base_result(path: Path, harness: str) -> dict[str, Any]:
    return {
        "harness": harness,
        "session_id": None,
        "parent_session_id": None,
        "session_source": None,
        "path": str(path),
        "cwd": None,
        "model": None,
        "effort": None,
        "started_at": None,
        "ended_at": None,
        "duration_seconds": None,
        "messages": {"user": 0, "assistant": 0},
        "tokens": {},
        "tokens_by_model": {},
        "tool_counts": {},
        "tool_output_bytes": 0,
        "max_tool_output_bytes": 0,
        "commands": [],
        "read_paths": [],
        "skills": [],
        "delegations": [],
        "invalid_json_lines": 0,
    }


def inspect_codex(path: Path) -> dict[str, Any]:
    result = base_result(path, "codex")
    commands: list[str] = []
    command_seen: set[str] = set()
    read_paths: list[str] = []
    path_seen: set[str] = set()
    tools: Counter[str] = Counter()
    calls_seen: set[str] = set()
    messages_seen: set[str] = set()
    first: datetime | None = None
    last: datetime | None = None
    latest_tokens: dict[str, Any] = {}
    previous_tokens: dict[str, Any] = {}
    current_model = "unavailable"
    tokens_by_model: dict[str, Counter[str]] = {}
    token_fields_by_model: dict[str, set[str]] = {}

    def attribute_model_epoch() -> None:
        nonlocal previous_tokens
        if not latest_tokens:
            return
        numeric_keys = {
            key for key, value in latest_tokens.items() if isinstance(value, (int, float))
        }
        if any(
            int(latest_tokens.get(key, 0) or 0) < int(previous_tokens.get(key, 0) or 0)
            for key in numeric_keys
        ):
            tokens_by_model.clear()
            token_fields_by_model.clear()
            previous_tokens = {}
        delta = usage_delta(latest_tokens, previous_tokens)
        tokens_by_model.setdefault(current_model, Counter()).update(delta)
        token_fields_by_model.setdefault(current_model, set()).update(latest_tokens)
        previous_tokens = dict(latest_tokens)

    for record, _ in iter_jsonl(path):
        if record.get("_invalid_json"):
            result["invalid_json_lines"] += 1
            continue
        first, last = update_times(first, last, record.get("timestamp"))
        record_type = record.get("type")
        payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
        if record_type == "session_meta":
            result["session_id"] = payload.get("id") or payload.get("session_id")
            result["parent_session_id"] = payload.get("parent_thread_id") or payload.get("forked_from_id")
            result["session_source"] = payload.get("thread_source")
            result["cwd"] = payload.get("cwd")
            first, last = update_times(first, last, payload.get("timestamp"))
        elif record_type == "turn_context":
            next_model = str(payload.get("model") or current_model)
            if next_model != current_model:
                attribute_model_epoch()
            result["model"] = payload.get("model") or result["model"]
            result["effort"] = payload.get("effort") or payload.get("reasoning_effort") or result["effort"]
            current_model = next_model
        elif record_type == "event_msg" and payload.get("type") == "token_count":
            info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
            usage = info.get("total_token_usage")
            if isinstance(usage, dict):
                latest_tokens = usage
        elif record_type == "response_item":
            item_type = payload.get("type")
            if item_type == "message":
                role = payload.get("role")
                key = str(payload.get("id") or record.get("timestamp") or id(payload))
                marker = f"{role}:{key}"
                if role in {"user", "assistant"} and marker not in messages_seen:
                    messages_seen.add(marker)
                    result["messages"][role] += 1
            if item_type in {"function_call", "custom_tool_call"}:
                call_id = str(payload.get("call_id") or payload.get("id") or "")
                if call_id and call_id in calls_seen:
                    continue
                if call_id:
                    calls_seen.add(call_id)
                name = str(payload.get("name") or "unknown")
                tools[name] += 1
                arguments = decode_json_object(payload.get("arguments"))
                extracted: list[str] = []
                if name in {"exec_command", "shell_command"}:
                    command = arguments.get("cmd") or arguments.get("command")
                    if isinstance(command, str):
                        extracted.append(command)
                elif name == "exec":
                    extracted.extend(commands_from_js(payload.get("input")))
                if name == "view_image" and isinstance(arguments.get("path"), str):
                    ordered_add(read_paths, path_seen, arguments["path"])
                for command in extracted:
                    ordered_add(commands, command_seen, command)
                    for read_path in read_paths_from_command(command):
                        ordered_add(read_paths, path_seen, read_path)
            elif item_type in {"function_call_output", "custom_tool_call_output"}:
                output = payload.get("output")
                size = value_bytes(output)
                result["tool_output_bytes"] += size
                result["max_tool_output_bytes"] = max(result["max_tool_output_bytes"], size)

    attribute_model_epoch()
    result["commands"] = commands
    result["read_paths"] = read_paths
    result["skills"] = [path for path in read_paths if path.endswith("SKILL.md")]
    result["tool_counts"] = dict(sorted(tools.items()))
    result["tokens"] = latest_tokens
    result["tokens_by_model"] = {
        model: normalized_model_tokens(
            dict(usage), harness="codex", available=token_fields_by_model.get(model, set())
        )
        for model, usage in sorted(tokens_by_model.items())
        if usage.get("total_tokens", 0) > 0
    }
    result["started_at"] = first.isoformat() if first else None
    result["ended_at"] = last.isoformat() if last else None
    result["duration_seconds"] = duration_seconds(first, last)
    return result


def claude_usage(message: dict[str, Any]) -> dict[str, int]:
    usage = message.get("usage") if isinstance(message.get("usage"), dict) else {}
    keys = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
    result = {key: int(usage.get(key) or 0) for key in keys}
    for optional in ("reasoning_output_tokens", "thinking_tokens"):
        if optional in usage:
            result["reasoning_output_tokens"] = int(usage.get(optional) or 0)
            break
    return result


def inspect_claude(path: Path, codex_root: Path, codex_home: Path, include_delegations: bool = True) -> dict[str, Any]:
    result = base_result(path, "claude")
    commands: list[str] = []
    command_seen: set[str] = set()
    read_paths: list[str] = []
    path_seen: set[str] = set()
    skills: list[str] = []
    skill_seen: set[str] = set()
    tools: Counter[str] = Counter()
    tool_seen: set[str] = set()
    user_seen: set[str] = set()
    tool_results_seen: set[str] = set()
    usage_by_message: dict[str, tuple[str, dict[str, int]]] = {}
    assistant_seen: set[str] = set()
    first: datetime | None = None
    last: datetime | None = None

    for record, _ in iter_jsonl(path):
        if record.get("_invalid_json"):
            result["invalid_json_lines"] += 1
            continue
        first, last = update_times(first, last, record.get("timestamp"))
        result["session_id"] = record.get("sessionId") or record.get("session_id") or result["session_id"]
        result["cwd"] = record.get("cwd") or result["cwd"]
        record_type = record.get("type")
        if record_type == "user":
            key = str(record.get("uuid") or record.get("message", {}).get("id") or record.get("timestamp"))
            message = record.get("message") if isinstance(record.get("message"), dict) else {}
            content = message.get("content")
            blocks = content if isinstance(content, list) else []
            has_tool_result = False
            has_human_content = isinstance(content, str) and bool(content.strip())
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_result":
                    has_tool_result = True
                    tool_result_id = str(block.get("tool_use_id") or f"{key}:{len(tool_results_seen)}")
                    if tool_result_id not in tool_results_seen:
                        tool_results_seen.add(tool_result_id)
                        size = value_bytes(block.get("content"))
                        result["tool_output_bytes"] += size
                        result["max_tool_output_bytes"] = max(result["max_tool_output_bytes"], size)
                elif block.get("type") == "text" and str(block.get("text") or "").strip():
                    has_human_content = True
            if has_human_content or not has_tool_result:
                user_seen.add(key)
        if record_type != "assistant" or not isinstance(record.get("message"), dict):
            continue
        message = record["message"]
        message_id = str(message.get("id") or record.get("uuid") or record.get("timestamp"))
        assistant_seen.add(message_id)
        message_model = str(message.get("model") or "unavailable")
        usage_by_message[message_id] = (message_model, claude_usage(message))
        result["model"] = message.get("model") or result["model"]
        content = message.get("content") if isinstance(message.get("content"), list) else []
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            tool_id = str(block.get("id") or f"{message_id}:{block.get('name')}:{json.dumps(block.get('input'), sort_keys=True)}")
            if tool_id in tool_seen:
                continue
            tool_seen.add(tool_id)
            name = str(block.get("name") or "unknown")
            tools[name] += 1
            tool_input = block.get("input") if isinstance(block.get("input"), dict) else {}
            if name == "Bash" and isinstance(tool_input.get("command"), str):
                command = tool_input["command"]
                ordered_add(commands, command_seen, command)
                for read_path in read_paths_from_command(command):
                    ordered_add(read_paths, path_seen, read_path)
            elif name == "Read" and isinstance(tool_input.get("file_path"), str):
                ordered_add(read_paths, path_seen, tool_input["file_path"])
            elif name == "Skill":
                skill = tool_input.get("skill") or tool_input.get("name")
                ordered_add(skills, skill_seen, skill)

    totals: Counter[str] = Counter()
    tokens_by_model: dict[str, Counter[str]] = {}
    token_fields_by_model: dict[str, set[str]] = {}
    for model, usage in usage_by_message.values():
        totals.update(usage)
        tokens_by_model.setdefault(model, Counter()).update(usage)
        token_fields_by_model.setdefault(model, set()).update(usage)
    totals["total_tokens"] = sum(totals[key] for key in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))
    for usage in tokens_by_model.values():
        usage["total_tokens"] = sum(
            usage[key]
            for key in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
        )
    result["messages"] = {"user": len(user_seen), "assistant": len(assistant_seen), "tool_results": len(tool_results_seen)}
    result["commands"] = commands
    result["read_paths"] = read_paths
    for read_path in read_paths:
        if read_path.endswith("SKILL.md"):
            ordered_add(skills, skill_seen, read_path)
    result["skills"] = skills
    result["tool_counts"] = dict(sorted(tools.items()))
    result["tokens"] = dict(totals)
    result["tokens_by_model"] = {
        model: normalized_model_tokens(
            dict(usage), harness="claude", available=token_fields_by_model.get(model, set())
        )
        for model, usage in sorted(tokens_by_model.items())
        if usage.get("total_tokens", 0) > 0
    }
    result["started_at"] = first.isoformat() if first else None
    result["ended_at"] = last.isoformat() if last else None
    result["duration_seconds"] = duration_seconds(first, last)
    if include_delegations:
        result["delegations"] = inspect_delegations(path, codex_root, codex_home)
    return result


def strip_heredoc_bodies(command: str) -> list[str]:
    output: list[str] = []
    delimiter: str | None = None
    allow_tabs = False
    for line in command.splitlines():
        if delimiter is not None:
            candidate = line.lstrip("\t") if allow_tabs else line
            if candidate.strip() == delimiter:
                delimiter = None
                allow_tabs = False
            continue
        output.append(line)
        match = HEREDOC_RE.search(line)
        if match:
            delimiter = match.group(1)
            allow_tabs = "<<-" in match.group(0)
    return output


def flag_value(tokens: list[str], names: set[str]) -> str | None:
    for index, token in enumerate(tokens):
        if token in names and index + 1 < len(tokens):
            return tokens[index + 1].strip("'\"")
        for name in names:
            if token.startswith(name + "="):
                return token.split("=", 1)[1].strip("'\"")
    return None


def parse_codex_invocations(command: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in strip_heredoc_bodies(command):
        if "codex" not in line:
            continue
        tokens = shell_tokens(line)
        if not tokens:
            continue
        codex_index = next((index for index, token in enumerate(tokens) if Path(token).name == "codex"), None)
        companion_index = next((index for index, token in enumerate(tokens) if Path(token).name == "codex-companion.mjs"), None)
        if codex_index is None and companion_index is None:
            continue
        if codex_index is not None:
            args = tokens[codex_index + 1 :]
            if "exec" not in args and "resume" not in args:
                continue
            model = flag_value(args, {"-m", "--model"})
            effort = None
            for index, token in enumerate(args):
                config = args[index + 1] if token in {"-c", "--config"} and index + 1 < len(args) else token.split("=", 1)[1] if token.startswith(("-c=", "--config=")) else None
                if config and config.startswith("model_reasoning_effort="):
                    effort = config.split("=", 1)[1].strip("'\"")
            mode = "resume" if "resume" in args else "exec"
        else:
            args = tokens[companion_index + 1 :]
            model = flag_value(args, {"--model"})
            effort = flag_value(args, {"--effort"})
            mode = args[0] if args else "legacy"
        thread_id = next((match.group(0) for token in args for match in [UUID_RE.search(token)] if match), None)
        rows.append({
            "mode": mode,
            "invocation": line.strip(),
            "model": model,
            "model_source": "explicit" if model else None,
            "effort": effort,
            "effort_source": "explicit" if effort else None,
            "thread_id": thread_id,
        })
    return rows


def recover_thread_id(path: Path) -> str | None:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = THREAD_CONTEXT_RE.search(line)
            if match:
                return match.group(1)
    return None


def rollout_for_thread(thread_id: str, root: Path) -> Path | None:
    matches = list(root.rglob(f"*{thread_id}*.jsonl")) if root.is_dir() else []
    return matches[0] if len(matches) == 1 else None


def rollout_settings(path: Path) -> tuple[str | None, str | None]:
    model: str | None = None
    effort: str | None = None
    for record, _ in iter_jsonl(path):
        if record.get("type") != "turn_context":
            continue
        payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
        model = payload.get("model") or model
        effort = payload.get("effort") or payload.get("reasoning_effort") or effort
        if model and effort:
            break
    return model, effort


def current_codex_settings(codex_home: Path) -> tuple[str | None, str | None]:
    path = codex_home / "config.toml"
    if not path.is_file():
        return None, None
    try:
        import tomllib

        with path.open("rb") as handle:
            config = tomllib.load(handle)
    except (OSError, ValueError):
        return None, None
    model = config.get("model") if isinstance(config.get("model"), str) else None
    effort = config.get("model_reasoning_effort") if isinstance(config.get("model_reasoning_effort"), str) else None
    return model, effort


def inspect_delegations(parent: Path, codex_root: Path, codex_home: Path) -> list[dict[str, Any]]:
    artifact_root = parent.with_suffix("")
    if not artifact_root.is_dir():
        return []
    config_model, config_effort = current_codex_settings(codex_home)
    rows: list[dict[str, Any]] = []
    for meta_path in sorted(artifact_root.rglob("agent-*.meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        agent_type = meta.get("agentType") or meta.get("agent_type")
        if agent_type != "codex-runner":
            continue
        transcript = meta_path.with_name(meta_path.name.replace(".meta.json", ".jsonl"))
        if not transcript.is_file():
            continue
        nested = inspect_claude(transcript, codex_root, codex_home, include_delegations=False)
        invocations = [row for command in nested["commands"] for row in parse_codex_invocations(command)]
        if not invocations:
            invocations = [{"mode": None, "invocation": None, "model": None, "model_source": None, "effort": None, "effort_source": None, "thread_id": None}]
        recovered = recover_thread_id(transcript)
        for invocation in invocations:
            thread_id = invocation.get("thread_id") or recovered
            rollout = rollout_for_thread(thread_id, codex_root) if thread_id else None
            rollout_model, rollout_effort = rollout_settings(rollout) if rollout else (None, None)
            if not invocation.get("model"):
                invocation["model"] = rollout_model or config_model
                invocation["model_source"] = "rollout" if rollout_model else "current-config" if config_model else "unavailable"
            if not invocation.get("effort"):
                invocation["effort"] = rollout_effort or config_effort
                invocation["effort_source"] = "rollout" if rollout_effort else "current-config" if config_effort else "unavailable"
            invocation.update({
                "agent_id": meta_path.name.removesuffix(".meta.json"),
                "agent_type": agent_type,
                "claude_model": nested.get("model"),
                "description": meta.get("description"),
                "thread_id": thread_id,
                "rollout_path": str(rollout) if rollout else None,
                "output_tokens": nested.get("tokens", {}).get("output_tokens", 0),
            })
            rows.append(invocation)
    return rows


def detect_harness(path: Path) -> str:
    for record, _ in iter_jsonl(path):
        if record.get("_invalid_json"):
            continue
        if record.get("type") in {"session_meta", "turn_context", "response_item", "event_msg"}:
            return "codex"
        if record.get("type") in {"assistant", "user", "system"} and ("message" in record or "sessionId" in record):
            return "claude"
    raise InspectError(f"unsupported or empty JSONL: {path}")


def resolve_target(target: str, codex_root: Path, claude_root: Path) -> tuple[Path, str]:
    requested_harness: str | None = None
    if target.startswith("codex:"):
        requested_harness, target = "codex", target[6:]
    elif target.startswith("claude:"):
        requested_harness, target = "claude", target[7:]
    candidate = Path(target).expanduser()
    if candidate.is_file():
        return candidate.resolve(), requested_harness or detect_harness(candidate)
    matches: list[tuple[Path, str]] = []
    if requested_harness in {None, "codex"} and codex_root.is_dir():
        matches.extend((path, "codex") for path in codex_root.rglob(f"*{target}*.jsonl"))
    if requested_harness in {None, "claude"} and claude_root.is_dir():
        matches.extend((path, "claude") for path in claude_root.rglob(f"{target}.jsonl"))
    unique = {(str(path.resolve()), harness): (path.resolve(), harness) for path, harness in matches}
    if not unique:
        raise InspectError(f"session not found: {target}")
    if len(unique) > 1:
        choices = "\n".join(f"- {harness}: {path}" for path, harness in unique.values())
        raise InspectError(f"session is ambiguous; use a harness prefix or path:\n{choices}")
    return next(iter(unique.values()))


def inspect_target(target: str, codex_root: Path, claude_root: Path, codex_home: Path) -> dict[str, Any]:
    path, harness = resolve_target(target, codex_root, claude_root)
    return inspect_codex(path) if harness == "codex" else inspect_claude(path, codex_root, codex_home)


def compact_command(command: str, limit: int, full: bool) -> str:
    if full:
        return command
    flattened = " ".join(command.split())
    return flattened if len(flattened) <= limit else flattened[: max(0, limit - 1)] + "…"


def capped(values: list[Any], args: argparse.Namespace, command: bool = False) -> tuple[list[Any], int]:
    selected = values if args.all else values[: args.max_items]
    if command:
        selected = [compact_command(value, args.command_chars, args.full_commands) for value in selected]
    return selected, len(values) - len(selected)


def view_result(result: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    view = dict(result)
    for key in ("commands", "read_paths", "skills", "delegations"):
        selected, omitted = capped(result.get(key, []), args, command=key == "commands")
        if key == "delegations":
            compact_rows: list[dict[str, Any]] = []
            for row in selected:
                compact_row = dict(row)
                if isinstance(compact_row.get("invocation"), str):
                    compact_row["invocation"] = compact_command(
                        compact_row["invocation"], args.command_chars, args.full_commands
                    )
                compact_rows.append(compact_row)
            selected = compact_rows
        view[key] = selected
        view[f"{key}_total"] = len(result.get(key, []))
        if omitted:
            view[f"{key}_omitted"] = omitted
    return view


def render_result(result: dict[str, Any], args: argparse.Namespace) -> str:
    view = view_result(result, args)
    lines = [
        f"{view['harness']} session {view.get('session_id') or 'unknown'}",
        f"path: {view['path']}",
        f"cwd: {view.get('cwd') or 'unavailable'}",
        f"latest model: {view.get('model') or 'unavailable'} | effort: {view.get('effort') or 'unavailable'}",
        f"time: {view.get('started_at') or 'unavailable'} -> {view.get('ended_at') or 'unavailable'} ({view.get('duration_seconds') if view.get('duration_seconds') is not None else 'unavailable'}s)",
        "messages: " + " ".join(f"{key}={value}" for key, value in view["messages"].items()),
        "tokens: " + (" ".join(f"{key}={value}" for key, value in view["tokens"].items()) or "unavailable"),
        "tools: " + (" ".join(f"{key}={value}" for key, value in view["tool_counts"].items()) or "none"),
        f"tool output: total={view['tool_output_bytes']}B max={view['max_tool_output_bytes']}B",
    ]
    if view.get("parent_session_id"):
        lines.insert(2, f"parent: {view['parent_session_id']} | source: {view.get('session_source') or 'unavailable'}")
    if view.get("tokens_by_model"):
        lines.append("tokens by model:")
        token_fields = (
            "input_tokens",
            "uncached_input_tokens",
            "cache_read_tokens",
            "cache_write_tokens",
            "output_tokens",
            "normal_output_tokens",
            "reasoning_output_tokens",
            "total_tokens",
        )
        for model, usage in view["tokens_by_model"].items():
            values = " ".join(
                f"{key.removesuffix('_tokens')}={usage.get(key) if usage.get(key) is not None else 'unavailable'}"
                for key in token_fields
            )
            lines.append(f"- {model}: {values}")
    for key, label in (("commands", "commands"), ("read_paths", "read paths"), ("skills", "skills")):
        values = view.get(key, [])
        lines.append(f"{label} ({len(result.get(key, []))}):")
        lines.extend(f"- {value}" for value in values)
        if view.get(f"{key}_omitted"):
            lines.append(f"- … {view[key + '_omitted']} omitted; rerun with --all")
    if result.get("delegations"):
        lines.append(f"delegated Codex runs ({len(result['delegations'])}):")
        for row in view["delegations"]:
            lines.append(
                f"- {row.get('agent_id')}: model={row.get('model') or 'unavailable'} ({row.get('model_source')}) "
                f"effort={row.get('effort') or 'unavailable'} ({row.get('effort_source')}) "
                f"thread={row.get('thread_id') or 'unavailable'} output={row.get('output_tokens', 0)}"
            )
        if view.get("delegations_omitted"):
            lines.append(f"- … {view['delegations_omitted']} omitted; rerun with --all")
    if result.get("invalid_json_lines"):
        lines.append(f"warning: skipped {result['invalid_json_lines']} invalid JSON line(s)")
    return "\n".join(lines)


def diff_results(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    def changes(key: str) -> dict[str, list[Any]]:
        left_values = left.get(key, [])
        right_values = right.get(key, [])
        return {
            "removed": [item for item in left_values if item not in right_values],
            "added": [item for item in right_values if item not in left_values],
        }

    token_keys = sorted(set(left.get("tokens", {})) | set(right.get("tokens", {})))
    left_models = left.get("tokens_by_model", {})
    right_models = right.get("tokens_by_model", {})
    token_delta_by_model: dict[str, dict[str, int | None]] = {}
    for model in sorted(set(left_models) | set(right_models)):
        left_usage = left_models.get(model, {})
        right_usage = right_models.get(model, {})
        model_keys = sorted(set(left_usage) | set(right_usage))
        token_delta_by_model[model] = {}
        for key in model_keys:
            left_value = left_usage.get(key, 0)
            right_value = right_usage.get(key, 0)
            token_delta_by_model[model][key] = (
                None if left_value is None or right_value is None else int(right_value) - int(left_value)
            )
    return {
        "left": {key: left.get(key) for key in ("harness", "session_id", "model", "effort", "duration_seconds")},
        "right": {key: right.get(key) for key in ("harness", "session_id", "model", "effort", "duration_seconds")},
        "token_delta": {key: int(right.get("tokens", {}).get(key, 0)) - int(left.get("tokens", {}).get(key, 0)) for key in token_keys},
        "token_delta_by_model": token_delta_by_model,
        "commands": changes("commands"),
        "read_paths": changes("read_paths"),
        "skills": changes("skills"),
    }


def render_diff(diff: dict[str, Any], args: argparse.Namespace) -> str:
    lines = [
        f"left: {diff['left']['harness']} {diff['left'].get('session_id') or 'unknown'} model={diff['left'].get('model') or 'unavailable'} effort={diff['left'].get('effort') or 'unavailable'}",
        f"right: {diff['right']['harness']} {diff['right'].get('session_id') or 'unknown'} model={diff['right'].get('model') or 'unavailable'} effort={diff['right'].get('effort') or 'unavailable'}",
        "token delta (right-left): " + (" ".join(f"{key}={value:+d}" for key, value in diff["token_delta"].items()) or "unavailable"),
    ]
    if diff.get("token_delta_by_model"):
        lines.append("token delta by model (right-left):")
        for model, usage in diff["token_delta_by_model"].items():
            values = " ".join(
                f"{key.removesuffix('_tokens')}={value:+d}"
                if value is not None
                else f"{key.removesuffix('_tokens')}=unavailable"
                for key, value in usage.items()
            )
            lines.append(f"- {model}: {values}")
    for key in ("commands", "read_paths", "skills"):
        lines.append(f"{key.replace('_', ' ')}:")
        for direction, prefix in (("removed", "-"), ("added", "+")):
            values, omitted = capped(diff[key][direction], args, command=key == "commands")
            lines.extend(f"{prefix} {value}" for value in values)
            if omitted:
                lines.append(f"{prefix} … {omitted} omitted; rerun with --all")
        if not diff[key]["removed"] and not diff[key]["added"]:
            lines.append("  unchanged")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-root", type=Path, default=Path(os.environ.get("SESSION_INSPECT_CODEX_ROOT", "~/.codex/sessions")).expanduser())
    parser.add_argument("--claude-root", type=Path, default=Path(os.environ.get("SESSION_INSPECT_CLAUDE_ROOT", "~/.claude/projects")).expanduser())
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser())
    subparsers = parser.add_subparsers(dest="action", required=True)
    for name in ("inspect", "diff"):
        child = subparsers.add_parser(name)
        child.add_argument("targets", nargs=1 if name == "inspect" else 2)
        child.add_argument("--json", action="store_true")
        child.add_argument("--all", action="store_true", help="show every list item")
        child.add_argument("--full-commands", action="store_true", help="preserve multiline command bodies")
        child.add_argument("--max-items", type=int, default=10)
        child.add_argument("--command-chars", type=int, default=200)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_items < 1 or args.command_chars < 20:
        raise InspectError("--max-items must be positive and --command-chars must be at least 20")
    try:
        results = [inspect_target(target, args.codex_root, args.claude_root, args.codex_home) for target in args.targets]
    except (InspectError, OSError) as exc:
        print(f"session-inspect: {exc}", file=sys.stderr)
        return 2
    if args.action == "inspect":
        output: Any = view_result(results[0], args) if args.json else render_result(results[0], args)
    else:
        diff = diff_results(results[0], results[1])
        output = diff if args.json else render_diff(diff, args)
    print(json.dumps(output, indent=2, sort_keys=True) if args.json else output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InspectError as exc:
        print(f"session-inspect: {exc}", file=sys.stderr)
        raise SystemExit(2)
