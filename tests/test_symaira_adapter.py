#!/usr/bin/env python3
"""symaira_adapter: SY-01 safe per-broker path."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import symaira_adapter  # noqa: E402


class TestSymairaPerBroker(unittest.TestCase):
    def test_execute_requires_mandate(self) -> None:
        with mock.patch.object(symaira_adapter, "find_symaira_cli", return_value="/bin/symeraseme"):
            with mock.patch.object(sys, "argv", [
                "symaira_adapter.py",
                "--case", "c1",
                "--broker-ids", "a",
                "--execute",
            ]):
                with mock.patch("opacite_lib.require_mandate", side_effect=SystemExit("no mandate")):
                    with self.assertRaises(SystemExit):
                        symaira_adapter.main()

    def test_use_plan_execute_rejected(self) -> None:
        with mock.patch.object(sys, "argv", [
            "symaira_adapter.py",
            "--case", "c1",
            "--broker-ids", "a,b",
            "--use-plan-execute",
        ]):
            with self.assertRaises(SystemExit) as ctx:
                symaira_adapter.main()
            self.assertIn("SY-01", str(ctx.exception))

    def test_invokes_run_web_form_per_id(self) -> None:
        calls: list[list[str]] = []

        def fake_run(cmd: list[str], **kwargs: object) -> mock.Mock:
            calls.append(cmd)
            m = mock.Mock()
            m.returncode = 0
            m.stdout = "ok"
            m.stderr = ""
            m.args = cmd
            return m

        with mock.patch.object(symaira_adapter, "find_symaira_cli", return_value="/bin/symeraseme"):
            with mock.patch.object(symaira_adapter.subprocess, "run", side_effect=fake_run):
                with mock.patch.object(symaira_adapter, "init_state_db"):
                    with tempfile.TemporaryDirectory() as tmp:
                        tmp_case = Path(tmp) / "case-slug"
                        tmp_case.mkdir()
                        with mock.patch.object(symaira_adapter, "case_dir", return_value=tmp_case):
                            with mock.patch.object(sys, "argv", [
                                "symaira_adapter.py",
                                "--case", "c1",
                                "--broker-ids", "broker-a,broker-b",
                                "--json",
                            ]):
                                symaira_adapter.main()

        self.assertEqual(len(calls), 2)
        for cmd in calls:
            self.assertEqual(cmd[0:2], ["/bin/symeraseme", "run-web-form"])
            self.assertIn("--dry-run", cmd)
        ids = {cmd[2] for cmd in calls}
        self.assertEqual(ids, {"broker-a", "broker-b"})
        plan_cmds = [c for c in calls if "plan" in c]
        self.assertEqual(plan_cmds, [])


if __name__ == "__main__":
    unittest.main()
