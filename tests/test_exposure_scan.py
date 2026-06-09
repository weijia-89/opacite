#!/usr/bin/env python3
"""exposure_scan.py — plan, report, and lane=scan SQLite events."""
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

import exposure_scan  # noqa: E402
import opacite_lib  # noqa: E402
from opacite_lib import append_event, latest_events  # noqa: E402


class _CaseIsolation:
    def __init__(self, tmp_root: Path, slug: str) -> None:
        self.tmp_root = tmp_root
        self.slug = slug
        (tmp_root / "localonly" / "cases" / slug / "exports").mkdir(parents=True)
        self._patches: list[mock._patch] = []

    def case_dir(self, s: str) -> Path:
        return self.tmp_root / "localonly" / "cases" / s

    def state_db_path(self, s: str) -> Path:
        return self.case_dir(s) / "state.sqlite"

    def __enter__(self) -> _CaseIsolation:
        self._patches.append(mock.patch.object(opacite_lib, "case_dir", self.case_dir))
        self._patches.append(
            mock.patch.object(opacite_lib, "state_db_path", self.state_db_path)
        )
        self._patches.append(mock.patch.object(exposure_scan, "SKILL_ROOT", self.tmp_root))
        for p in self._patches:
            p.__enter__()
        return self

    def __exit__(self, *args: object) -> None:
        for p in reversed(self._patches):
            p.__exit__(*args)


class TestExposureScanDryRun(unittest.TestCase):
    def test_dry_run_writes_plan_report_and_scan_lane_events(self) -> None:
        reg = ROOT / "tests/fixtures/scan-registry-mini.json"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            slug = "scan1"
            with _CaseIsolation(tmp_root, slug):
                out = exposure_scan.run_scan(
                    case=slug,
                    registry_path=reg,
                    dry_run=True,
                    delta_only=False,
                )
                self.assertTrue(Path(out["plan_path"]).is_file())
                self.assertTrue(Path(out["report_path"]).is_file())
                report = json.loads(Path(out["report_path"]).read_text())
                self.assertTrue(report["dry_run"])
                self.assertEqual(report["scan_target_count"], 2)
                events = latest_events(slug, lane="scan")
                self.assertEqual(events.get("ps1"), "APPROVED")
                self.assertEqual(events.get("ps2"), "APPROVED")

    def test_cli_dry_run_subprocess(self) -> None:
        import subprocess

        reg = ROOT / "tests/fixtures/scan-registry-mini.json"
        slug = "scan-cli2"
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/exposure_scan.py"),
                "--case",
                slug,
                "--dry-run",
                "--registry",
                str(reg),
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("exposure_report.json", proc.stdout)
        report = ROOT / "localonly" / "cases" / slug / "exports" / "exposure_report.json"
        self.assertTrue(report.is_file())


class TestExposureScanExecute(unittest.TestCase):
    def test_execute_without_vanish_records_manual_required(self) -> None:
        reg = ROOT / "tests/fixtures/scan-registry-mini.json"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            slug = "scan-live"
            with _CaseIsolation(tmp_root, slug):
                with mock.patch.dict(
                    os.environ, {"OPACITE_EXPOSURE_EXECUTE": "1"}, clear=False
                ):
                    with mock.patch.object(
                        exposure_scan, "vanish_installed", return_value=False
                    ):
                        out = exposure_scan.run_scan(
                            case=slug,
                            registry_path=reg,
                            dry_run=False,
                            delta_only=False,
                        )
                report = out["report"]
                self.assertFalse(report["dry_run"])
                self.assertGreater(report["manual_required_count"], 0)
                events = latest_events(slug, lane="scan")
                self.assertEqual(events.get("ps1"), "MANUAL_REQUIRED")

    def test_execute_delegates_vanish_when_installed(self) -> None:
        reg = ROOT / "tests/fixtures/scan-registry-mini.json"
        fake_result = {
            "exit_code": 0,
            "stdout": json.dumps({"submitted": ["ps1"], "evidence_log": "/tmp/x.log"}),
            "stderr": "",
            "result": {"submitted": ["ps1"], "evidence_log": "/tmp/x.log"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            slug = "scan-vanish"
            with _CaseIsolation(tmp_root, slug):
                with mock.patch.dict(
                    os.environ, {"OPACITE_EXPOSURE_EXECUTE": "1"}, clear=False
                ):
                    with mock.patch.object(
                        exposure_scan, "vanish_installed", return_value=True
                    ):
                        with mock.patch.object(
                            exposure_scan,
                            "delegate_vanish_scan",
                            return_value=fake_result,
                        ) as deleg:
                            exposure_scan.run_scan(
                                case=slug,
                                registry_path=reg,
                                dry_run=False,
                                delta_only=False,
                            )
                            deleg.assert_called_once()
                            call_ids = deleg.call_args[0][1]
                            self.assertEqual(call_ids, ["ps1"])

    def test_live_without_execute_env_exits(self) -> None:
        reg = ROOT / "tests/fixtures/scan-registry-mini.json"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            with _CaseIsolation(tmp_root, "x"):
                with mock.patch.dict(os.environ, {}, clear=True):
                    with self.assertRaises(SystemExit) as ctx:
                        exposure_scan.run_scan(
                            case="x",
                            registry_path=reg,
                            dry_run=False,
                            delta_only=False,
                        )
                    self.assertIn("OPACITE_EXPOSURE_EXECUTE", str(ctx.exception))


class TestExposureScanDelta(unittest.TestCase):
    def test_delta_only_filters_relisted(self) -> None:
        reg = ROOT / "tests/fixtures/scan-registry-mini.json"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            slug = "scan-delta"
            with _CaseIsolation(tmp_root, slug):
                append_event(slug, "ps1", "RE_LISTED", lane="scan")
                out = exposure_scan.run_scan(
                    case=slug,
                    registry_path=reg,
                    dry_run=True,
                    delta_only=True,
                )
                self.assertEqual(out["scan_target_count"], 1)


if __name__ == "__main__":
    unittest.main()
