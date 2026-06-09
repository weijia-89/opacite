#!/usr/bin/env python3
"""Rescan cadence planner — 60d people-search / 90d private DB (Incogni Q2)."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from opacite_lib import case_dir, init_state_db, state_db_path  # noqa: E402

PEOPLE_SEARCH_DAYS = 60
PRIVATE_DB_DAYS = 90


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_report_timestamp(case: str) -> datetime | None:
    path = case_dir(case) / "exports" / "exposure_report.json"
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    ts = data.get("generated_at")
    if not ts:
        return None
    return parse_ts(ts)


def last_lane_timestamp(case: str, lane: str) -> datetime | None:
    init_state_db(case)
    db = state_db_path(case)
    if not db.is_file():
        return None
    conn = sqlite3.connect(db)
    try:
        row = conn.execute(
            """
            SELECT MAX(ts) FROM broker_events
            WHERE case_slug = ? AND COALESCE(lane, '') = ?
            """,
            (case, lane),
        ).fetchone()
        if row and row[0]:
            return parse_ts(str(row[0]))
    finally:
        conn.close()
    return None


def bucket_schedule(
    *,
    name: str,
    last: datetime | None,
    interval_days: int,
    now: datetime,
) -> dict[str, Any]:
    if last is None:
        return {
            "bucket": name,
            "interval_days": interval_days,
            "last_activity": None,
            "next_due": None,
            "days_until_due": 0,
            "overdue": True,
            "never_run": True,
        }
    next_due = last + timedelta(days=interval_days)
    days_until = (next_due.date() - now.date()).days
    return {
        "bucket": name,
        "interval_days": interval_days,
        "last_activity": last.isoformat(),
        "next_due": next_due.isoformat(),
        "days_until_due": days_until,
        "overdue": days_until <= 0,
        "never_run": False,
    }


def build_schedule(case: str, *, now: datetime | None = None) -> dict[str, Any]:
    now = now or utc_now()
    people_last = load_report_timestamp(case) or last_lane_timestamp(case, "scan")
    private_last = last_lane_timestamp(case, "email")

    people = bucket_schedule(
        name="people-search",
        last=people_last,
        interval_days=PEOPLE_SEARCH_DAYS,
        now=now,
    )
    private = bucket_schedule(
        name="private-db",
        last=private_last,
        interval_days=PRIVATE_DB_DAYS,
        now=now,
    )

    suggestions: list[str] = []
    if people["overdue"]:
        suggestions.append(
            f"bash scripts/exposure_scan.sh --case {case} --dry-run"
        )
        suggestions.append(
            f"bash scripts/optout_runner.sh --case {case} --lane scan --confirm"
        )
    if private["overdue"]:
        suggestions.append(
            f"bash scripts/optout_runner.sh --case {case} --plan --lane email --max 50"
        )

    return {
        "generated_at": now.isoformat(),
        "case": case,
        "dry_run": True,
        "cadence_days": {
            "people_search": PEOPLE_SEARCH_DAYS,
            "private_db": PRIVATE_DB_DAYS,
        },
        "buckets": [people, private],
        "suggested_commands": suggestions,
        "note": "dry-run: prints schedule only; operator runs suggested commands manually",
    }


def format_human(schedule: dict[str, Any]) -> str:
    lines = [
        f"rescan schedule: case={schedule['case']} (dry-run, no network)",
        f"  cadence: people-search={schedule['cadence_days']['people_search']}d, "
        f"private-db={schedule['cadence_days']['private_db']}d",
    ]
    for b in schedule["buckets"]:
        last = b["last_activity"] or "never"
        nxt = b["next_due"] or "now (no baseline)"
        flag = "OVERDUE" if b["overdue"] else f"due in {b['days_until_due']}d"
        lines.append(
            f"  {b['bucket']} ({b['interval_days']}d): last={last} "
            f"next={nxt} [{flag}]"
        )
    if schedule["suggested_commands"]:
        lines.append("  suggested (operator runs manually):")
        for cmd in schedule["suggested_commands"]:
            lines.append(f"    {cmd}")
    else:
        lines.append("  suggested: none — nothing overdue")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(
        description="opacite rescan cadence (60d people-search / 90d private DB)"
    )
    p.add_argument("--case", required=True)
    p.add_argument("--dry-run", action="store_true", default=True)
    p.add_argument("--json", action="store_true", dest="as_json")
    args = p.parse_args()

    schedule = build_schedule(args.case)
    out_path = case_dir(args.case) / "exports" / "rescan_schedule.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(schedule, f, indent=2)
        f.write("\n")

    if args.as_json:
        print(json.dumps(schedule, indent=2))
    else:
        print(format_human(schedule))
        print(f"\nwritten: {out_path}")


if __name__ == "__main__":
    main()
