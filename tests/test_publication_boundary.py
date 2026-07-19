from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_publication_boundary as boundary  # noqa: E402


class PublicationBoundaryTests(unittest.TestCase):
    def test_detects_every_likely_leak_rule(self) -> None:
        content = "\n".join(
            (
                "/home/alice/private/file.txt",
                "~/dev/private-skill",
                "Work on obs:AGT-TSK-private-history",
                "vault=clemux-personal",
                "CODEX_THREAD_ID=019f79f3-3605-7723-a4c2-3ae3eb2b5989",
            )
        )

        matches = boundary.find_matches({"sample.md": content})

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
        matches = boundary.find_matches(
            {
                "allowed.md": "obs:AGT-TSK-private-history",
                "blocked.md": "obs:AGT-TSK-private-history",
            }
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


if __name__ == "__main__":
    unittest.main()
