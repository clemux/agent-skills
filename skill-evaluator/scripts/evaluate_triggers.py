#!/usr/bin/env python3
"""Observe whether Codex consults a candidate skill for implicit prompts.

This file is a Codex-native replacement for Anthropic's Apache-2.0 trigger
executor. It invokes only the Codex CLI. The evidence is deliberately
conservative: it recognizes only emitted command-execution events that
reference the copied candidate SKILL.md.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from run_eval import isolated_codex_environment, parse_skill_name


def load_queries(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("queries", data.get("evals"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("Trigger set must contain a non-empty 'queries' array")
    queries: list[dict[str, Any]] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Query {index} is not an object")
        query = item.get("query", item.get("prompt"))
        if not isinstance(query, str) or not isinstance(item.get("should_trigger"), bool):
            raise ValueError(
                f"Query {index} requires string 'query' and boolean 'should_trigger'"
            )
        queries.append(
            {
                "id": item.get("id", index),
                "query": query,
                "should_trigger": item["should_trigger"],
            }
        )
    return queries


def replace_description(skill_md: Path, description: str) -> None:
    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"Missing YAML frontmatter in {skill_md}")
    try:
        frontmatter_end = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration as exc:
        raise ValueError(f"Unterminated YAML frontmatter in {skill_md}") from exc
    description_index = next(
        (
            index
            for index in range(1, frontmatter_end)
            if re.match(r"^description\s*:", lines[index])
        ),
        None,
    )
    if description_index is None:
        raise ValueError(f"Could not replace description in {skill_md}")
    description_end = description_index + 1
    current_value = lines[description_index].split(":", 1)[1].strip()
    if current_value in {"|", "|-", "|+", ">", ">-", ">+"}:
        while (
            description_end < frontmatter_end
            and (
                lines[description_end].startswith((" ", "\t"))
                or not lines[description_end].strip()
            )
        ):
            description_end += 1
    newline = "\r\n" if lines[description_index].endswith("\r\n") else "\n"
    lines[description_index:description_end] = [
        "description: " + json.dumps(description) + newline
    ]
    skill_md.write_text("".join(lines), encoding="utf-8")


def command_text(item: dict[str, Any]) -> str:
    command = item.get("command", "")
    if isinstance(command, list):
        return " ".join(str(part) for part in command)
    return str(command)


def parse_trigger_evidence(stdout: str, skill_name: str) -> list[dict[str, Any]]:
    suffixes = (
        f".agents/skills/{skill_name}/SKILL.md",
        f".agents\\skills\\{skill_name}\\SKILL.md",
    )
    evidence: list[dict[str, Any]] = []
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") not in {"item.started", "item.completed"}:
            continue
        item = event.get("item", {})
        if item.get("type") != "command_execution":
            continue
        command = command_text(item)
        if any(suffix in command for suffix in suffixes):
            evidence.append(
                {
                    "line": line_number,
                    "event_type": event.get("type"),
                    "command": command,
                }
            )
    return evidence


def run_query(
    query: dict[str, Any],
    run_number: int,
    skill_path: Path,
    skill_name: str,
    workspace: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    run_dir = workspace / f"query-{query['id']}" / f"run-{run_number}"
    run_dir.mkdir(parents=True)
    repo = run_dir / "workspace"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main"],
        cwd=repo,
        check=True,
    )
    target = repo / ".agents" / "skills" / skill_name
    target.parent.mkdir(parents=True)
    shutil.copytree(skill_path, target)
    if args.description is not None:
        replace_description(target / "SKILL.md", args.description)

    cmd = [
        args.codex_bin,
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--sandbox",
        "read-only",
        "--cd",
        str(repo),
    ]
    if args.model:
        cmd.extend(["--model", args.model])
    cmd.append(query["query"])
    (run_dir / "command.json").write_text(
        json.dumps({"argv": cmd[:-1], "prompt": query["query"]}, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.prepare_only:
        return {"observed": False, "evidence": [], "prepared_only": True}

    temp_home, env = isolated_codex_environment()
    started = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            cwd=repo,
            env=env,
            text=True,
            capture_output=True,
            timeout=args.timeout,
            check=False,
        )
    finally:
        temp_home.cleanup()
    duration = time.monotonic() - started
    (run_dir / "transcript.jsonl").write_text(result.stdout, encoding="utf-8")
    (run_dir / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    evidence = parse_trigger_evidence(result.stdout, skill_name)
    record = {
        "observed": bool(evidence),
        "evidence": evidence,
        "duration_seconds": round(duration, 3),
        "returncode": result.returncode,
    }
    (run_dir / "observation.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"codex exec failed for {run_dir} with exit {result.returncode}; "
            "see stderr.txt"
        )
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", type=Path, required=True)
    parser.add_argument("--skill-path", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--description")
    parser.add_argument("--runs-per-query", type=int, default=3)
    parser.add_argument("--trigger-threshold", type=float, default=0.5)
    parser.add_argument("--model")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()

    args.eval_set = args.eval_set.resolve()
    args.skill_path = args.skill_path.resolve()
    args.workspace = args.workspace.resolve()
    if not (args.skill_path / "SKILL.md").is_file():
        parser.error(f"Not a skill directory: {args.skill_path}")
    if args.runs_per_query < 1:
        parser.error("--runs-per-query must be at least 1")
    if not 0 <= args.trigger_threshold <= 1:
        parser.error("--trigger-threshold must be between 0 and 1")
    args.workspace.mkdir(parents=True, exist_ok=True)

    skill_name = parse_skill_name(args.skill_path)
    queries = load_queries(args.eval_set)
    results: list[dict[str, Any]] = []
    for query in queries:
        observations = []
        for run_number in range(1, args.runs_per_query + 1):
            print(
                f"Running query {query['id']} observation {run_number}",
                file=sys.stderr,
            )
            observations.append(
                run_query(
                    query,
                    run_number,
                    args.skill_path,
                    skill_name,
                    args.workspace,
                    args,
                )
            )
        observed = sum(1 for record in observations if record["observed"])
        rate = observed / len(observations)
        should_trigger = query["should_trigger"]
        passed = (
            None
            if args.prepare_only
            else (
                rate >= args.trigger_threshold
                if should_trigger
                else rate < args.trigger_threshold
            )
        )
        results.append(
            {
                "id": query["id"],
                "query": query["query"],
                "should_trigger": should_trigger,
                "observed_runs": observed,
                "total_runs": len(observations),
                "observation_rate": rate,
                "pass": passed,
                "prepared_only": args.prepare_only,
                "observations": observations,
            }
        )

    output = {
        "skill_name": skill_name,
        "description_override": args.description,
        "evidence_semantics": {
            "positive": "An emitted command_execution referenced the copied candidate SKILL.md.",
            "negative": "No such command was observed; this is inconclusive, not proof of non-activation.",
            "documented_limitation": "Codex JSONL has no documented dedicated skill-activation event.",
        },
        "results": results,
        "summary": {
            "passed": sum(1 for result in results if result["pass"] is True),
            "total": 0 if args.prepare_only else len(results),
            "prepared": len(results) if args.prepare_only else 0,
        },
    }
    output_path = args.workspace / "trigger-results.json"
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
