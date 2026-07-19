from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_publication_boundary as boundary  # noqa: E402


class PublicationBoundaryTests(unittest.TestCase):
    def test_detects_every_likely_leak_rule(self) -> None:
        private_id = "EXA" + "MPLE-TSK-private-history"
        content = "\n".join(
            (
                "/home/" + "alice/private/file.txt",
                "~/" + "dev/private-skill",
                "Work on ob" + "s:" + private_id,
                "vault=" + "alice-" + "personal",
                "CODEX_THREAD_" + "ID=00000000-0000-4000-8000-000000000000",
            )
        )
        rules = boundary.BASE_RULES + boundary.build_local_rules(
            ["EXAMPLE"], ["alice-personal"]
        )

        matches = boundary.find_matches({"sample.md": content}, rules)

        self.assertEqual(
            {match.rule for match in matches},
            {
                "personal-home",
                "tilde-dev",
                "obs-reference",
                "private-reference-id",
                "private-marker",
                "session-identity",
            },
        )

    def test_exception_is_exact_path_and_rule(self) -> None:
        reference = "ob" + "s:" + "EXA" + "MPLE-TSK-private-history"
        matches = boundary.find_matches(
            {
                "allowed.md": reference,
                "blocked.md": reference,
            },
            boundary.BASE_RULES
            + boundary.build_local_rules(["EXAMPLE"], []),
        )
        exceptions = {("allowed.md", "obs-reference"): "reviewed fixture"}

        violations, stale = boundary.audit(matches, exceptions)

        self.assertFalse(stale)
        self.assertEqual(
            {(match.path, match.rule) for match in violations},
            {
                ("allowed.md", "private-reference-id"),
                ("blocked.md", "obs-reference"),
                ("blocked.md", "private-reference-id"),
            },
        )

    def test_stale_exception_is_reported(self) -> None:
        violations, stale = boundary.audit(
            [], {("old.md", "obs-reference"): "match was removed"}
        )

        self.assertFalse(violations)
        self.assertEqual(stale, [("old.md", "obs-reference")])

    def test_inactive_local_exception_is_not_stale(self) -> None:
        violations, stale = boundary.audit(
            [],
            {("legacy.md", "private-marker"): "local rule is optional"},
            frozenset(rule.name for rule in boundary.BASE_RULES),
        )

        self.assertFalse(violations)
        self.assertFalse(stale)

    def test_missing_local_config_disables_local_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(boundary.load_local_rules(Path(directory)), ())


if __name__ == "__main__":
    unittest.main()
