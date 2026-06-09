#!/usr/bin/env python3
"""Lane filter rules for optout_runner (SY-02 web vs vanish)."""
from __future__ import annotations

import subprocess
import sys
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


if __name__ == "__main__":
    unittest.main()
