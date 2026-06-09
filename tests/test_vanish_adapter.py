#!/usr/bin/env python3
"""vanish_adapter: scan-only Phase 3 stub."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import opacite_lib  # noqa: E402
import vanish_adapter  # noqa: E402
from opacite_lib import latest_events  # noqa: E402


class _CaseIsolation:
    def __init__(self, tmp_root: Path, slug: str) -> None:
        self.tmp_root = tmp_root
        (tmp_root / "localonly" / "cases" / slug).mkdir(parents=True, exist_ok=True)
        self._patches: list[mock._patch] = []

    def case_dir(self, s: str) -> Path:
        return self.tmp_root / "localonly" / "cases" / s

    def state_db_path(self, s: str) -> Path:
        return self.case_dir(s) / "state.sqlite"

    def __enter__(self) -> _CaseIsolation:
        self._patches.append(
            mock.patch.object(opacite_lib, "case_dir", self.case_dir)
        )
        self._patches.append(
            mock.patch.object(opacite_lib, "state_db_path", self.state_db_path)
        )
        self._patches.append(
            mock.patch.object(vanish_adapter, "case_dir", self.case_dir)
        )
        for p in self._patches:
            p.__enter__()
        return self

    def __exit__(self, *args: object) -> None:
        for p in reversed(self._patches):
            p.__exit__(*args)


class TestVanishDiscovery(unittest.TestCase):
    def test_missing_vanish_exits_with_hint(self) -> None:
        with mock.patch.object(vanish_adapter, "find_vanish", return_value=None):
            with mock.patch.object(sys, "argv", [
                "vanish_adapter.py",
                "--case", "c1",
                "--broker-ids", "foo",
                "--json",
            ]):
                with self.assertRaises(SystemExit) as ctx:
                    vanish_adapter.main()
                self.assertIn("vanish not found", str(ctx.exception))


class TestVanishBlockedActions(unittest.TestCase):
    def test_opt_out_blocked_records_manual_required(self) -> None:
        with mock.patch.object(vanish_adapter, "find_vanish", return_value=["/bin/vanish"]):
            with tempfile.TemporaryDirectory() as tmp:
                tmp_root = Path(tmp)
                with _CaseIsolation(tmp_root, "c1"):
                    with mock.patch.object(sys, "argv", [
                        "vanish_adapter.py",
                        "--case", "c1",
                        "--broker-ids", "spokeo,whitepages",
                        "--action", "opt-out",
                    ]):
                        with self.assertRaises(SystemExit) as ctx:
                            vanish_adapter.main()
                        self.assertIn("consent gate", str(ctx.exception))
                    events = latest_events("c1", lane="vanish")
                    self.assertEqual(events.get("spokeo"), "MANUAL_REQUIRED")
                    self.assertEqual(events.get("whitepages"), "MANUAL_REQUIRED")

    def test_llm_memory_check_blocked(self) -> None:
        with mock.patch.object(vanish_adapter, "find_vanish", return_value=["/bin/vanish"]):
            with mock.patch.object(sys, "argv", [
                "vanish_adapter.py",
                "--case", "c1",
                "--broker-ids", "foo",
                "--action", "llm-memory-check",
            ]):
                with self.assertRaises(SystemExit) as ctx:
                    vanish_adapter.main()
                self.assertIn("consent gate", str(ctx.exception))


class TestVanishScanDryRun(unittest.TestCase):
    def test_scan_dry_run_records_approved_without_subprocess(self) -> None:
        calls: list[list[str]] = []

        def fake_run(cmd: list[str], **kwargs: object) -> mock.Mock:
            calls.append(cmd)
            raise AssertionError("subprocess should not run in scan dry-run")

        profile = {
            "legal_name": {"first": "Test", "last": "User"},
            "emails": ["test@example.com"],
        }

        with mock.patch.object(vanish_adapter, "find_vanish", return_value=["/bin/vanish"]):
            with mock.patch.object(vanish_adapter, "load_profile", return_value=profile):
                with mock.patch.object(vanish_adapter.subprocess, "run", side_effect=fake_run):
                    with tempfile.TemporaryDirectory() as tmp:
                        tmp_root = Path(tmp)
                        with _CaseIsolation(tmp_root, "c1"):
                            with mock.patch.object(
                                vanish_adapter,
                                "REGISTRY_DEFAULT",
                                ROOT / "tests" / "fixtures" / "optery-mini.json",
                            ):
                                with mock.patch.object(sys, "argv", [
                                    "vanish_adapter.py",
                                    "--case", "c1",
                                    "--broker-ids", "broker-a,broker-b",
                                    "--json",
                                ]):
                                    vanish_adapter.main()
                            self.assertEqual(calls, [])
                            events = latest_events("c1", lane="vanish")
                            self.assertEqual(events.get("broker-a"), "APPROVED")
                            self.assertEqual(events.get("broker-b"), "APPROVED")


class TestVanishScanExecute(unittest.TestCase):
    def test_scan_execute_invokes_vanish_scan(self) -> None:
        calls: list[list[str]] = []

        def fake_run(cmd: list[str], **kwargs: object) -> mock.Mock:
            calls.append(cmd)
            m = mock.Mock()
            m.returncode = 0
            m.stdout = json.dumps({"score": 42})
            m.stderr = ""
            return m

        profile = {
            "legal_name": {"first": "Test", "last": "User"},
            "emails": ["test@example.com"],
        }

        with mock.patch.dict(os.environ, {"OPACITE_VANISH_EXECUTE": "1"}, clear=False):
            with mock.patch.object(vanish_adapter, "find_vanish", return_value=["/bin/vanish"]):
                with mock.patch.object(vanish_adapter, "load_profile", return_value=profile):
                    with mock.patch.object(
                        vanish_adapter,
                        "run_vanish_subprocess",
                        side_effect=lambda cmd, **kw: fake_run(cmd),
                    ):
                        with tempfile.TemporaryDirectory() as tmp:
                            tmp_root = Path(tmp)
                            with _CaseIsolation(tmp_root, "c1"):
                                with mock.patch.object(
                                    vanish_adapter,
                                    "REGISTRY_DEFAULT",
                                    ROOT / "tests" / "fixtures" / "optery-mini.json",
                                ):
                                    with mock.patch.object(sys, "argv", [
                                        "vanish_adapter.py",
                                        "--case", "c1",
                                        "--broker-ids", "broker-a",
                                        "--execute",
                                        "--json",
                                    ]):
                                        vanish_adapter.main()
                                self.assertEqual(len(calls), 1)
                                self.assertEqual(calls[0][0:2], ["/bin/vanish", "scan"])
                                self.assertIn("--name", calls[0])
                                self.assertIn("Test User", calls[0])
                                events = latest_events("c1", lane="vanish")
                                self.assertEqual(events.get("broker-a"), "SUBMITTED")


class TestVanishVerify(unittest.TestCase):
    def test_verify_dry_run_uses_no_fetch(self) -> None:
        calls: list[list[str]] = []

        def fake_run(cmd: list[str], **kwargs: object) -> mock.Mock:
            calls.append(cmd)
            m = mock.Mock()
            m.returncode = 0
            m.stdout = "ok"
            m.stderr = ""
            return m

        profile = {
            "legal_name": {"first": "Test", "last": "User"},
            "emails": ["test@example.com"],
        }

        with mock.patch.object(vanish_adapter, "find_vanish", return_value=["/bin/vanish"]):
            with mock.patch.object(vanish_adapter, "load_profile", return_value=profile):
                with mock.patch.object(
                    vanish_adapter,
                    "run_vanish_subprocess",
                    side_effect=lambda cmd, **kw: fake_run(cmd),
                ):
                    with tempfile.TemporaryDirectory() as tmp:
                        tmp_root = Path(tmp)
                        with _CaseIsolation(tmp_root, "c1"):
                            with mock.patch.object(
                                vanish_adapter,
                                "REGISTRY_DEFAULT",
                                ROOT / "tests" / "fixtures" / "optery-mini.json",
                            ):
                                with mock.patch.object(sys, "argv", [
                                    "vanish_adapter.py",
                                    "--case", "c1",
                                    "--broker-ids", "broker-a",
                                    "--action", "verify",
                                    "--json",
                                ]):
                                    vanish_adapter.main()
                            self.assertIn("--no-fetch", calls[0])
                            events = latest_events("c1", lane="vanish")
                            self.assertEqual(events.get("broker-a"), "APPROVED")


if __name__ == "__main__":
    unittest.main()
