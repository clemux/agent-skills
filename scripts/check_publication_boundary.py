#!/usr/bin/env python3
"""Reject likely private or backend-specific data in tracked repository text."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ALLOWLIST_NAME = ".publication-boundary-allowlist.json"
PRIVATE_PREFIXES = ("AGT", "OAW", "PMX", "FAB", "CDX", "SR")
PRIVATE_MARKERS = ("cle" + "mux-personal", "cle" + "mux", "Plant" + "Mux")


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class Match:
    path: str
    line: int
    rule: str
    excerpt: str


RULES = (
    Rule(
        "personal-home",
        re.compile(r"/home/(?!<(?:user|username)>/)(?!user/)(?!example/)[A-Za-z0-9._-]+/"),
    ),
    Rule("tilde-dev", re.compile(r"~/" + r"dev(?:/|\b)")),
    Rule("obs-reference", re.compile(r"\bobs:[A-Za-z0-9][A-Za-z0-9-]*\b")),
    Rule(
        "private-reference-id",
        re.compile(rf"\b(?:{'|'.join(PRIVATE_PREFIXES)})-[A-Z0-9][A-Za-z0-9-]*\b"),
    ),
    Rule(
        "private-marker",
        re.compile(rf"\b(?:{'|'.join(re.escape(value) for value in PRIVATE_MARKERS)})\b"),
    ),
    Rule(
        "session-identity",
        re.compile(
            r"\b(?:CODEX_THREAD_ID|CLAUDE_CODE_SESSION_ID|CLAUDE_SESSION_ID)\s*=\s*"
            r"[0-9a-f]{8}-[0-9a-f-]{20,}\b",
            re.IGNORECASE,
        ),
    ),
)
RULE_NAMES = frozenset(rule.name for rule in RULES)


class BoundaryError(ValueError):
    """Raised for malformed publication-boundary configuration."""


def repository_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return Path(result.stdout.strip())


def tracked_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [os.fsdecode(value) for value in result.stdout.split(b"\0") if value]


def tracked_text(root: Path, paths: Iterable[str]) -> dict[str, str]:
    files: dict[str, str] = {}
    for relative in paths:
        path = root / relative
        try:
            if path.is_symlink():
                files[relative] = os.readlink(path)
                continue
            raw = path.read_bytes()
        except (FileNotFoundError, IsADirectoryError):
            continue
        if b"\0" in raw:
            continue
        try:
            files[relative] = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
    return files


def find_matches(files: dict[str, str]) -> list[Match]:
    matches: list[Match] = []
    for path, content in sorted(files.items()):
        for line_number, line in enumerate(content.splitlines(), start=1):
            for rule in RULES:
                if rule.pattern.search(line):
                    matches.append(Match(path, line_number, rule.name, line.strip()[:200]))
    return matches


def load_exceptions(root: Path) -> dict[tuple[str, str], str]:
    path = root / ALLOWLIST_NAME
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise BoundaryError(f"missing {ALLOWLIST_NAME}") from error
    except json.JSONDecodeError as error:
        raise BoundaryError(f"invalid {ALLOWLIST_NAME}: {error}") from error

    if not isinstance(data, dict) or data.get("version") != 1:
        raise BoundaryError(f"{ALLOWLIST_NAME} must be an object with version 1")
    entries = data.get("exceptions")
    if not isinstance(entries, list):
        raise BoundaryError(f"{ALLOWLIST_NAME} exceptions must be a list")

    exceptions: dict[tuple[str, str], str] = {}
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise BoundaryError(f"exception {index} must be an object")
        relative = entry.get("path")
        rules = entry.get("rules")
        reason = entry.get("reason")
        if not isinstance(relative, str) or not relative or any(c in relative for c in "*?[]"):
            raise BoundaryError(f"exception {index} must name one exact path without glob syntax")
        if relative.startswith("/") or ".." in Path(relative).parts:
            raise BoundaryError(f"exception {index} path must stay repository-relative")
        if not isinstance(rules, list) or not rules or not all(isinstance(rule, str) for rule in rules):
            raise BoundaryError(f"exception {index} must contain a non-empty rules list")
        if not isinstance(reason, str) or not reason.strip():
            raise BoundaryError(f"exception {index} must contain a non-empty reason")
        unknown = sorted(set(rules) - RULE_NAMES)
        if unknown:
            raise BoundaryError(f"exception {index} names unknown rules: {', '.join(unknown)}")
        for rule in rules:
            key = (relative, rule)
            if key in exceptions:
                raise BoundaryError(f"duplicate exception for {relative} ({rule})")
            exceptions[key] = reason.strip()
    return exceptions


def audit(
    matches: Iterable[Match], exceptions: dict[tuple[str, str], str]
) -> tuple[list[Match], list[tuple[str, str]]]:
    used: set[tuple[str, str]] = set()
    violations: list[Match] = []
    for match in matches:
        key = (match.path, match.rule)
        if key in exceptions:
            used.add(key)
        else:
            violations.append(match)
    stale = sorted(set(exceptions) - used)
    return violations, stale


def main() -> int:
    try:
        root = repository_root()
        paths = tracked_paths(root)
        files = tracked_text(root, paths)
        exceptions = load_exceptions(root)
        missing_paths = sorted({path for path, _ in exceptions if path not in paths})
        if missing_paths:
            raise BoundaryError(
                "allowlist paths are not tracked: " + ", ".join(missing_paths)
            )
        violations, stale = audit(find_matches(files), exceptions)
    except (BoundaryError, subprocess.CalledProcessError) as error:
        print(f"publication-boundary: configuration error: {error}", file=sys.stderr)
        return 2

    for match in violations:
        print(f"{match.path}:{match.line}: {match.rule}: {match.excerpt}")
    for path, rule in stale:
        print(f"{ALLOWLIST_NAME}: stale exception: {path} ({rule})")
    if violations or stale:
        print(
            "publication-boundary: failed; redact the match or add one reviewed exact-file exception",
            file=sys.stderr,
        )
        return 1

    print(f"publication-boundary: passed ({len(files)} tracked text files scanned)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
