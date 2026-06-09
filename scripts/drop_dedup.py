#!/usr/bin/env python3
"""DROP ⊖ email overlap dedup — brokers to skip on the next email batch."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from opacite_lib import (  # noqa: E402
    REGISTRY_DEFAULT,
    case_dir,
    init_state_db,
    latest_events,
    load_registry,
)


def drop_eligible_ids(registry: dict[str, Any]) -> set[str]:
    return {
        str(b["id"])
        for b in registry.get("brokers", [])
        if b.get("id") and (b.get("drop_eligible") or b.get("process") == "drop-centralized")
    }


def email_submitted_ids(slug: str) -> set[str]:
    return {
        bid
        for bid, event in latest_events(slug, lane="email").items()
        if event == "SUBMITTED"
    }


def drop_lane_submitted(slug: str) -> tuple[bool, set[str]]:
    """True when any broker has SUBMITTED on lane=drop; also returns those broker ids."""
    by_broker = latest_events(slug, lane="drop")
    submitted = {bid for bid, event in by_broker.items() if event == "SUBMITTED"}
    return bool(submitted), submitted


def compute_dedup(
    slug: str,
    registry: dict[str, Any],
) -> dict[str, Any]:
    """Return skip list and overlap stats for next email batch planning."""
    eligible = drop_eligible_ids(registry)
    emailed = email_submitted_ids(slug)
    drop_active, drop_brokers = drop_lane_submitted(slug)

    overlap = eligible & emailed
    skip: set[str] = set(emailed)
    if drop_active:
        skip |= eligible

    return {
        "case": slug,
        "drop_lane_submitted": drop_active,
        "drop_lane_brokers": sorted(drop_brokers),
        "email_submitted_count": len(emailed),
        "email_submitted": sorted(emailed),
        "drop_eligible_count": len(eligible),
        "overlap_count": len(overlap),
        "overlap": sorted(overlap),
        "skip_count": len(skip),
        "skip_brokers": sorted(skip),
    }


def require_case(slug: str) -> Path:
    root = case_dir(slug)
    if not root.is_dir():
        raise SystemExit(
            f"error: case {slug!r} not found at {root}\n"
            f"  run: bash scripts/bootstrap_case.sh --slug {slug}"
        )
    return root


def main() -> None:
    p = argparse.ArgumentParser(
        description="List brokers to skip on the next email batch (DROP vs email overlap)",
    )
    p.add_argument("--case", required=True, help="case slug (localonly/cases/<slug>)")
    p.add_argument(
        "--registry",
        type=Path,
        default=REGISTRY_DEFAULT,
        help="unified broker registry JSON",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="read-only report (default; no SQLite writes)",
    )
    p.add_argument("--json", action="store_true", dest="as_json", help="JSON output")
    args = p.parse_args()

    require_case(args.case)
    if not args.registry.is_file():
        raise SystemExit(
            f"error: registry missing: {args.registry}\n"
            "  run: bash scripts/registry_sync.sh"
        )

    init_state_db(args.case)
    registry = load_registry(args.registry)
    report = compute_dedup(args.case, registry)
    report["dry_run"] = bool(args.dry_run)

    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"=== DROP dedup — case {args.case} ===")
        print(f"DROP lane submitted: {report['drop_lane_submitted']}")
        print(f"Email SUBMITTED:     {report['email_submitted_count']}")
        print(f"DROP-eligible:       {report['drop_eligible_count']}")
        print(f"Overlap (eligible ∩ emailed): {report['overlap_count']}")
        print(f"Skip on next email:  {report['skip_count']} broker(s)")
        if report["overlap"]:
            print("Overlap ids:", ", ".join(report["overlap"][:12]), end="")
            if report["overlap_count"] > 12:
                print(f" … +{report['overlap_count'] - 12} more", end="")
            print()
        if report["skip_brokers"]:
            preview = ", ".join(report["skip_brokers"][:12])
            suffix = ""
            if report["skip_count"] > 12:
                suffix = f" … +{report['skip_count'] - 12} more"
            print(f"Skip ids: {preview}{suffix}")
        if args.dry_run:
            print("(dry-run — no state changes)")


if __name__ == "__main__":
    main()
