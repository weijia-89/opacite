#!/usr/bin/env python3
"""Lane filter rules for optout_runner (SY-02 web vs vanish)."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from opacite_lib import broker_matches_lane  # noqa: E402


class TestBrokerMatchesLane(unittest.TestCase):
    def test_web_excludes_vanish_runner(self) -> None:
        b = {
            "id": "spokeo",
            "process": "search-for-removal",
            "runner": "vanish",
        }
        self.assertFalse(broker_matches_lane(b, "web"))
        self.assertTrue(broker_matches_lane(b, "vanish"))

    def test_web_includes_symaira_direct_form(self) -> None:
        b = {"id": "x", "process": "direct-form", "runner": "symaira"}
        self.assertTrue(broker_matches_lane(b, "web"))
        self.assertFalse(broker_matches_lane(b, "vanish"))

    def test_email_lane(self) -> None:
        self.assertTrue(
            broker_matches_lane({"process": "email-opt-out", "runner": "eraser"}, "email")
        )

    def test_scan_lane_people_search_only(self) -> None:
        self.assertTrue(
            broker_matches_lane(
                {"broker_class": "people-search", "process": "direct-form"},
                "scan",
            )
        )
        self.assertFalse(
            broker_matches_lane(
                {"broker_class": "marketing-data", "process": "email-opt-out"},
                "scan",
            )
        )


class TestOptoutRunnerHelp(unittest.TestCase):
    def test_help_lists_vanish_lane(self) -> None:
        proc = subprocess.run(
            ["bash", str(ROOT / "scripts/optout_runner.sh"), "--help"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("vanish", proc.stdout)

    def test_help_documents_scan_confirm(self) -> None:
        proc = subprocess.run(
            ["bash", str(ROOT / "scripts/optout_runner.sh"), "--help"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("scan", proc.stdout)
        self.assertIn("exposure_scan.sh", proc.stdout)
        self.assertIn("OPACITE_EXPOSURE_EXECUTE", proc.stdout)


class TestScanLaneConfirm(unittest.TestCase):
    def test_scan_confirm_dispatches_exposure_scan(self) -> None:
        reg = ROOT / "tests/fixtures/scan-registry-mini.json"
        with tempfile.TemporaryDirectory():
            slug = "scan-ci"
            proc = subprocess.run(
                [
                    "bash",
                    str(ROOT / "scripts/optout_runner.sh"),
                    "--case",
                    slug,
                    "--lane",
                    "scan",
                    "--confirm",
                    "--max",
                    "10",
                    "--registry",
                    str(reg),
                    "--skip-health-filter",
                ],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            self.assertIn("exposure_scan.sh", proc.stderr)
            self.assertIn("--registry", proc.stderr)
            self.assertIn("executing:", proc.stderr)
            plan = ROOT / "localonly" / "cases" / slug / "exports" / "exposure_plan.json"
            self.assertTrue(plan.is_file(), f"missing {plan}")


if __name__ == "__main__":
    unittest.main()
