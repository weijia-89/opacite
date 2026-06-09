#!/usr/bin/env python3
"""rescan_scheduler.py — cadence buckets and dry-run output."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import opacite_lib  # noqa: E402
import rescan_scheduler  # noqa: E402


class _CaseIsolation:
    def __init__(self, tmp_root: Path, slug: str) -> None:
        self.tmp_root = tmp_root
        self.slug = slug
        (tmp_root / "localonly" / "cases" / slug / "exports").mkdir(parents=True)

    def case_dir(self, s: str) -> Path:
        return self.tmp_root / "localonly" / "cases" / s

    def state_db_path(self, s: str) -> Path:
        return self.case_dir(s) / "state.sqlite"

    def __enter__(self) -> _CaseIsolation:
        self._patches = [
            mock.patch.object(opacite_lib, "case_dir", self.case_dir),
            mock.patch.object(opacite_lib, "state_db_path", self.state_db_path),
            mock.patch.object(rescan_scheduler, "case_dir", self.case_dir),
            mock.patch.object(rescan_scheduler, "SKILL_ROOT", self.tmp_root),
        ]
        for p in self._patches:
            p.__enter__()
        return self

    def __exit__(self, *args: object) -> None:
        for p in reversed(self._patches):
            p.__exit__(*args)


class TestRescanScheduler(unittest.TestCase):
    def test_never_run_buckets_overdue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            iso = _CaseIsolation(Path(tmp), "sched1")
            with iso:
                now = datetime(2026, 6, 12, tzinfo=timezone.utc)
                out = rescan_scheduler.build_schedule("sched1", now=now)
                self.assertTrue(out["buckets"][0]["overdue"])
                self.assertTrue(out["buckets"][1]["overdue"])
                self.assertGreater(len(out["suggested_commands"]), 0)

    def test_people_search_not_overdue_within_60d(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            iso = _CaseIsolation(Path(tmp), "sched2")
            with iso:
                now = datetime(2026, 6, 12, tzinfo=timezone.utc)
                recent = (now - timedelta(days=10)).isoformat()
                report = iso.case_dir("sched2") / "exports" / "exposure_report.json"
                report.write_text(
                    json.dumps({"generated_at": recent, "case": "sched2"}),
                    encoding="utf-8",
                )
                out = rescan_scheduler.build_schedule("sched2", now=now)
                people = out["buckets"][0]
                self.assertEqual(people["bucket"], "people-search")
                self.assertFalse(people["overdue"])
                self.assertGreater(people["days_until_due"], 0)

    def test_private_db_overdue_after_90d(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            iso = _CaseIsolation(Path(tmp), "sched3")
            with iso:
                now = datetime(2026, 6, 12, tzinfo=timezone.utc)
                old = datetime(2026, 1, 1, tzinfo=timezone.utc)

                def fake_last(_case: str, lane: str) -> datetime | None:
                    return old if lane == "email" else None

                with mock.patch.object(
                    rescan_scheduler, "last_lane_timestamp", side_effect=fake_last
                ):
                    out = rescan_scheduler.build_schedule("sched3", now=now)
                private = out["buckets"][1]
                self.assertTrue(private["overdue"])

    def test_cli_dry_run_subprocess(self) -> None:
        import subprocess

        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/rescan_scheduler.py"),
                "--case",
                "sched-cli2",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("people-search", proc.stdout)
        out = ROOT / "localonly/cases/sched-cli2/exports/rescan_schedule.json"
        self.assertTrue(out.is_file())


if __name__ == "__main__":
    unittest.main()
