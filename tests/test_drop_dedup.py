#!/usr/bin/env python3
"""Unit tests for DROP ⊖ email overlap dedup."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from drop_dedup import compute_dedup, require_case  # noqa: E402
from opacite_lib import append_event, init_state_db  # noqa: E402


def _mini_registry() -> dict:
    return {
        "brokers": [
            {
                "id": "acme-data",
                "name": "Acme Data",
                "process": "email-opt-out",
                "drop_eligible": False,
                "jurisdiction": ["US"],
            },
            {
                "id": "ca-broker-a",
                "name": "CA Broker A",
                "process": "email-opt-out",
                "drop_eligible": True,
                "jurisdiction": ["US", "US-CA"],
            },
            {
                "id": "ca-broker-b",
                "name": "CA Broker B",
                "process": "direct-form",
                "drop_eligible": True,
                "jurisdiction": ["US-CA"],
            },
            {
                "id": "drop-central",
                "name": "DROP Central",
                "process": "drop-centralized",
                "drop_eligible": True,
                "jurisdiction": ["US-CA"],
            },
            {
                "id": "us-only",
                "name": "US Only",
                "process": "email-opt-out",
                "drop_eligible": False,
                "jurisdiction": ["US"],
            },
        ],
        "count": 5,
    }


class TestDropDedup(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.slug = "dedup-test"
        self.case_path = self.root / "cases" / self.slug
        self.case_path.mkdir(parents=True)
        self.registry_path = self.root / "registry.json"
        self.registry_path.write_text(json.dumps(_mini_registry()), encoding="utf-8")
        self.patches = [
            mock.patch("opacite_lib.SKILL_ROOT", self.root),
            mock.patch("opacite_lib.case_dir", lambda s: self.root / "cases" / s),
            mock.patch("drop_dedup.case_dir", lambda s: self.root / "cases" / s),
            mock.patch("drop_dedup.REGISTRY_DEFAULT", self.registry_path),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_email_only_skips_submitted(self) -> None:
        init_state_db(self.slug)
        append_event(self.slug, "acme-data", "SUBMITTED", lane="email")
        append_event(self.slug, "us-only", "SUBMITTED", lane="email")

        reg = json.loads(self.registry_path.read_text(encoding="utf-8"))
        report = compute_dedup(self.slug, reg)

        self.assertFalse(report["drop_lane_submitted"])
        self.assertEqual(report["email_submitted_count"], 2)
        self.assertEqual(set(report["skip_brokers"]), {"acme-data", "us-only"})
        self.assertEqual(report["overlap_count"], 0)

    def test_drop_submitted_skips_all_drop_eligible(self) -> None:
        init_state_db(self.slug)
        append_event(
            self.slug,
            "california-drop-registry",
            "SUBMITTED",
            lane="drop",
            meta={"registered_broker_count": 545},
        )

        reg = json.loads(self.registry_path.read_text(encoding="utf-8"))
        report = compute_dedup(self.slug, reg)

        self.assertTrue(report["drop_lane_submitted"])
        self.assertEqual(
            set(report["skip_brokers"]),
            {"ca-broker-a", "ca-broker-b", "drop-central"},
        )
        self.assertEqual(report["drop_eligible_count"], 3)

    def test_overlap_when_both_lanes(self) -> None:
        init_state_db(self.slug)
        append_event(self.slug, "ca-broker-a", "SUBMITTED", lane="email")
        append_event(self.slug, "acme-data", "SUBMITTED", lane="email")
        append_event(self.slug, "california-drop-registry", "SUBMITTED", lane="drop")

        reg = json.loads(self.registry_path.read_text(encoding="utf-8"))
        report = compute_dedup(self.slug, reg)

        self.assertEqual(report["overlap"], ["ca-broker-a"])
        self.assertEqual(
            set(report["skip_brokers"]),
            {"acme-data", "ca-broker-a", "ca-broker-b", "drop-central"},
        )

    def test_empty_state_no_skip(self) -> None:
        init_state_db(self.slug)
        reg = json.loads(self.registry_path.read_text(encoding="utf-8"))
        report = compute_dedup(self.slug, reg)

        self.assertEqual(report["skip_count"], 0)
        self.assertEqual(report["overlap_count"], 0)

    def test_require_case_missing(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            require_case("no-such-case")
        self.assertIn("not found", str(ctx.exception))


class TestDropDedupCli(unittest.TestCase):
    def test_cli_missing_case(self) -> None:
        with mock.patch("drop_dedup.REGISTRY_DEFAULT", ROOT / "localonly/registry/unified-brokers.json"):
            with mock.patch("drop_dedup.case_dir", lambda s: ROOT / "localonly/cases" / s):
                proc = __import__("subprocess").run(
                    [sys.executable, str(ROOT / "scripts/drop_dedup.py"), "--case", "no-such-case-xyz", "--dry-run"],
                    capture_output=True,
                    text=True,
                    cwd=str(ROOT),
                )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not found", proc.stderr + proc.stdout)


if __name__ == "__main__":
    unittest.main()
