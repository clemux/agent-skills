#!/usr/bin/env python3
"""Run controlled paired Codex skill evaluations.

This file is a Codex-native replacement for Anthropic's Apache-2.0
skill-creator executor. It was written for this derivative bundle and invokes
only the Codex CLI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


def parse_skill_name(skill_path: Path) -> str:
    text = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"(?m)^name:\s*[\"']?([^\n\"']+)", text)
    if not match:
        raise ValueError(f"No name field found in {skill_path / 'SKILL.md'}")
    name = match.group(1).strip()
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        raise ValueError(f"Unsupported skill name: {name!r}")
    return name


def slugify(value: object) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return slug[:60] or "case"


def load_eval_set(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    evals = data.get("evals")
    if not isinstance(evals, list) or not evals:
        raise ValueError("Eval set must contain a non-empty 'evals' array")
    for index, item in enumerate(evals, start=1):
        if not isinstance(item, dict) or not isinstance(item.get("prompt"), str):
            raise ValueError(f"Eval {index} must be an object with a string 'prompt'")
        item.setdefault("id", index)
        item.setdefault("name", slugify(item["id"]))
        item.setdefault("files", [])
        item.setdefault("assertions", [])
    return evals


def copy_inputs(eval_item: dict[str, Any], eval_set_path: Path, repo: Path) -> list[str]:
    copied: list[str] = []
    inputs_dir = repo / "inputs"
    inputs_dir.mkdir()
    for raw in eval_item.get("files", []):
        if not isinstance(raw, str):
            raise ValueError("Eval 'files' entries must be path strings")
        source = Path(raw)
        if not source.is_absolute():
            source = eval_set_path.parent / source
        source = source.resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        target = inputs_dir / source.name
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
        copied.append(str(target.relative_to(repo)))
    return copied


def install_skill(skill_path: Path, repo: Path) -> str:
    name = parse_skill_name(skill_path)
    target = repo / ".agents" / "skills" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill_path.resolve(), target, symlinks=False)
    return name


def build_prompt(
    raw_prompt: str,
    skill_name: str | None,
    copied_inputs: list[str],
) -> str:
    invocation = f"Use ${skill_name} to execute this task." if skill_name else "Execute this task."
    inputs = ", ".join(copied_inputs) if copied_inputs else "none"
    return (
        f"{invocation}\n"
        "Act as the end user requested; do not discuss the evaluation harness. "
        "Write requested artifacts under outputs/. If no artifact is requested, "
        "return the answer normally.\n\n"
        f"Task:\n{raw_prompt}\n\nInput files: {inputs}"
    )


def isolated_codex_environment() -> tuple[tempfile.TemporaryDirectory[str], dict[str, str]]:
    temp_home = tempfile.TemporaryDirectory(prefix="skill-evaluator-codex-home-")
    home = Path(temp_home.name)
    home.chmod(0o700)
    env = os.environ.copy()
    source_codex_home = Path(env.get("CODEX_HOME", Path.home() / ".codex"))
    auth = source_codex_home / "auth.json"
    if auth.exists():
        (home / "auth.json").symlink_to(auth)
    elif not env.get("CODEX_API_KEY"):
        temp_home.cleanup()
        raise RuntimeError(
            "Codex authentication unavailable: expected CODEX_API_KEY or "
            f"{auth}"
        )
    env["HOME"] = str(home)
    env["CODEX_HOME"] = str(home)
    return temp_home, env


def parse_events(stdout: str) -> tuple[str, dict[str, int]]:
    final_message = ""
    usage: dict[str, int] = {}
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                final_message = str(item.get("text", ""))
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = {
                str(key): int(value)
                for key, value in event["usage"].items()
                if isinstance(value, (int, float))
            }
    return final_message, usage


def run_codex(
    repo: Path,
    prompt: str,
    run_dir: Path,
    args: argparse.Namespace,
) -> None:
    cmd = [
        args.codex_bin,
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--sandbox",
        args.sandbox,
        "--cd",
        str(repo),
    ]
    if args.model:
        cmd.extend(["--model", args.model])
    cmd.append(prompt)
    (run_dir / "command.json").write_text(
        json.dumps({"argv": cmd[:-1], "prompt": prompt}, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.prepare_only:
        return

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
    final_message, usage = parse_events(result.stdout)

    outputs = run_dir / "outputs"
    generated = repo / "outputs"
    if generated.is_dir():
        shutil.copytree(generated, outputs)
    else:
        outputs.mkdir()
    if final_message:
        (outputs / "final.md").write_text(final_message + "\n", encoding="utf-8")

    total_tokens = sum(
        usage.get(key, 0)
        for key in ("input_tokens", "output_tokens", "reasoning_output_tokens")
    )
    timing = {
        "total_tokens": total_tokens,
        "total_duration_seconds": round(duration, 3),
        "duration_ms": round(duration * 1000),
        "usage": usage,
        "returncode": result.returncode,
    }
    (run_dir / "timing.json").write_text(
        json.dumps(timing, indent=2) + "\n", encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"codex exec failed for {run_dir} with exit {result.returncode}; "
            "see stderr.txt"
        )


def prepare_run(
    eval_item: dict[str, Any],
    eval_set_path: Path,
    skill_path: Path | None,
    config_name: str,
    run_number: int,
    workspace: Path,
    args: argparse.Namespace,
) -> None:
    eval_id = eval_item["id"]
    eval_name = slugify(eval_item.get("name") or eval_item["prompt"][:40])
    eval_dir = workspace / f"eval-{eval_id}-{eval_name}"
    eval_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "eval_id": eval_id,
        "eval_name": eval_name,
        "prompt": eval_item["prompt"],
        "expected_output": eval_item.get("expected_output", ""),
        "assertions": eval_item.get("assertions", []),
    }
    (eval_dir / "eval_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )

    run_dir = eval_dir / config_name / f"run-{run_number}"
    run_dir.mkdir(parents=True)
    repo = run_dir / "workspace"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main"],
        cwd=repo,
        check=True,
    )
    copied_inputs = copy_inputs(eval_item, eval_set_path, repo)
    skill_name = install_skill(skill_path, repo) if skill_path else None
    prompt = build_prompt(eval_item["prompt"], skill_name, copied_inputs)
    provenance = {
        "configuration": config_name,
        "skill_path": str(skill_path.resolve()) if skill_path else None,
        "skill_name": skill_name,
        "model": args.model,
        "sandbox": args.sandbox,
        "raw_prompt_sha256": hashlib.sha256(eval_item["prompt"].encode()).hexdigest(),
    }
    (run_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    run_codex(repo, prompt, run_dir, args)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", type=Path, required=True)
    parser.add_argument("--skill-path", type=Path, required=True)
    parser.add_argument("--baseline-skill", type=Path)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--runs-per-config", type=int, default=1)
    parser.add_argument("--model")
    parser.add_argument(
        "--sandbox",
        choices=("read-only", "workspace-write"),
        default="workspace-write",
    )
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Create isolated run directories and command manifests without invoking Codex",
    )
    args = parser.parse_args()

    args.eval_set = args.eval_set.resolve()
    args.skill_path = args.skill_path.resolve()
    args.workspace = args.workspace.resolve()
    if args.baseline_skill:
        args.baseline_skill = args.baseline_skill.resolve()
    for path in [args.skill_path, args.baseline_skill]:
        if path and not (path / "SKILL.md").is_file():
            parser.error(f"Not a skill directory: {path}")
    if args.runs_per_config < 1:
        parser.error("--runs-per-config must be at least 1")
    args.workspace.mkdir(parents=True, exist_ok=True)

    evals = load_eval_set(args.eval_set)
    baseline_name = "old_skill" if args.baseline_skill else "without_skill"
    configs = [
        ("with_skill", args.skill_path),
        (baseline_name, args.baseline_skill),
    ]
    for eval_item in evals:
        for config_name, skill_path in configs:
            for run_number in range(1, args.runs_per_config + 1):
                print(
                    f"Preparing eval {eval_item['id']} {config_name} run {run_number}",
                    file=sys.stderr,
                )
                prepare_run(
                    eval_item,
                    args.eval_set,
                    skill_path,
                    config_name,
                    run_number,
                    args.workspace,
                    args,
                )
    print(json.dumps({"workspace": str(args.workspace), "evals": len(evals)}))


if __name__ == "__main__":
    main()
