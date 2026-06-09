#!/usr/bin/env python3
"""Exposure scan planner + vanish delegation (lane=scan)."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from opacite_lib import (  # noqa: E402
    ACTIVE_PLAN_STATES,
    REGISTRY_DEFAULT,
    append_event,
    append_failed_batch,
    broker_matches_lane,
    init_state_db,
    latest_events,
    load_registry,
)

LANE = "scan"
VANISH_INSTALL_HINT = (
    "vanish not installed — live scan recorded MANUAL_REQUIRED; "
    "install RAMBOXIE/vanish or use --dry-run"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def select_scan_targets(brokers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [b for b in brokers if broker_matches_lane(b, LANE)]


def load_prior_report(report_path: Path) -> dict[str, Any] | None:
    if not report_path.is_file():
        return None
    with report_path.open(encoding="utf-8") as f:
        return json.load(f)


def filter_delta_targets(
    slug: str,
    targets: list[dict[str, Any]],
    *,
    prior_report: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """ROADMAP 5.2: RE_LISTED plus brokers not in prior exposure_report.json."""
    current = latest_events(slug, lane=LANE)
    relisted_ids = {
        b["id"] for b in targets if current.get(b["id"]) == "RE_LISTED"
    }
    if prior_report is None:
        return [b for b in targets if b["id"] in relisted_ids]
    prior_ids = set(prior_report.get("target_broker_ids", []))
    return [
        b
        for b in targets
        if b["id"] in relisted_ids or b["id"] not in prior_ids
    ]


def target_row(b: dict[str, Any], *, action: str) -> dict[str, Any]:
    return {
        "broker_id": b["id"],
        "name": b.get("name"),
        "url": b.get("url"),
        "opt_out_url": b.get("opt_out_url"),
        "process": b.get("process"),
        "runner": b.get("runner"),
        "action": action,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")


def record_planned_batch(
    slug: str,
    targets: list[dict[str, Any]],
    *,
    campaign_id: str,
) -> int:
    current = latest_events(slug, lane=LANE)
    written = 0
    for b in targets:
        bid = b["id"]
        if current.get(bid) in ACTIVE_PLAN_STATES:
            continue
        append_event(
            slug,
            bid,
            "PLANNED",
            lane=LANE,
            meta={
                "campaign_id": campaign_id,
                "name": b.get("name"),
                "process": b.get("process"),
                "runner": b.get("runner"),
                "scan_phase": "exposure_plan",
            },
        )
        written += 1
    return written


def record_approved_batch(
    slug: str,
    broker_ids: list[str],
    *,
    campaign_id: str,
    dry_run: bool,
    evidence_path: str | None = None,
) -> None:
    for bid in broker_ids:
        append_event(
            slug,
            bid,
            "APPROVED",
            lane=LANE,
            evidence_path=evidence_path,
            meta={
                "campaign_id": campaign_id,
                "dry_run": dry_run,
                "runner": "vanish",
                "scan_phase": "exposure_execute",
            },
        )


def record_manual_required(
    slug: str,
    broker_ids: list[str],
    *,
    campaign_id: str,
    reason: str,
) -> None:
    for bid in broker_ids:
        append_event(
            slug,
            bid,
            "MANUAL_REQUIRED",
            lane=LANE,
            meta={
                "campaign_id": campaign_id,
                "reason": reason,
                "scan_phase": "exposure_execute",
            },
        )


def vanish_installed() -> bool:
    from vanish_adapter import find_vanish  # noqa: E402

    return find_vanish() is not None


def _delegate_vanish(
    case: str,
    broker_ids: list[str],
    *,
    campaign_id: str,
    execute: bool,
    registry: Path,
    action: str,
) -> dict[str, Any]:
    adapter = SKILL_ROOT / "scripts" / "vanish_adapter.py"
    cmd = [
        sys.executable,
        str(adapter),
        "--case",
        case,
        "--broker-ids",
        ",".join(broker_ids),
        "--campaign-id",
        campaign_id,
        "--lane",
        LANE,
        "--action",
        action,
        "--registry",
        str(registry),
        "--json",
    ]
    if execute:
        cmd.append("--execute")
    env = os.environ.copy()
    if execute:
        env["OPACITE_VANISH_EXECUTE"] = "1"
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
    parsed: dict[str, Any] = {}
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = {"raw_stdout": proc.stdout[:2000]}
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "result": parsed,
    }


def delegate_vanish_scan(
    case: str,
    broker_ids: list[str],
    *,
    campaign_id: str,
    execute: bool,
    registry: Path,
) -> dict[str, Any]:
    return _delegate_vanish(
        case,
        broker_ids,
        campaign_id=campaign_id,
        execute=execute,
        registry=registry,
        action="scan",
    )


def delegate_vanish_verify(
    case: str,
    broker_ids: list[str],
    *,
    campaign_id: str,
    execute: bool,
    registry: Path,
) -> dict[str, Any]:
    return _delegate_vanish(
        case,
        broker_ids,
        campaign_id=campaign_id,
        execute=execute,
        registry=registry,
        action="verify",
    )


def select_verify_targets(
    brokers: list[dict[str, Any]],
    *,
    max_n: int,
) -> list[dict[str, Any]]:
    vanish = [
        b
        for b in brokers
        if broker_matches_lane(b, LANE) and b.get("runner") == "vanish"
    ]
    return vanish[:max_n]


def run_scan(
    *,
    case: str,
    registry_path: Path,
    dry_run: bool,
    delta_only: bool,
) -> dict[str, Any]:
    data = load_registry(registry_path)
    brokers = data.get("brokers", [])
    targets = select_scan_targets(brokers)

    case_dir = SKILL_ROOT / "localonly" / "cases" / case
    exports = case_dir / "exports"
    plan_path = exports / "exposure_plan.json"
    report_path = exports / "exposure_report.json"
    prior_report = load_prior_report(report_path) if delta_only else None
    if delta_only:
        targets = filter_delta_targets(case, targets, prior_report=prior_report)

    campaign_id = str(uuid.uuid4())[:8]
    execute = (not dry_run) and os.environ.get("OPACITE_EXPOSURE_EXECUTE") == "1"
    if not dry_run and not execute:
        raise SystemExit(
            "error: live scan requires OPACITE_EXPOSURE_EXECUTE=1 "
            "(human gate; use --dry-run otherwise)"
        )

    plan_action = "plan_scan" if dry_run else "execute_scan"
    plan = {
        "generated_at": utc_now(),
        "case": case,
        "lane": LANE,
        "dry_run": dry_run,
        "delta_only": delta_only,
        "campaign_id": campaign_id,
        "registry_count": len(brokers),
        "scan_target_count": len(targets),
        "targets": [target_row(b, action=plan_action) for b in targets[:100]],
    }
    write_json(plan_path, plan)

    init_state_db(case)
    events_written = record_planned_batch(case, targets, campaign_id=campaign_id)

    vanish_targets = [b for b in targets if b.get("runner") == "vanish"]
    manual_targets = [b for b in targets if b.get("runner") != "vanish"]
    vanish_ids = [b["id"] for b in vanish_targets]
    manual_ids = [b["id"] for b in manual_targets]

    delegation: dict[str, Any] | None = None
    approved_ids: list[str] = []
    manual_required: list[dict[str, str]] = []

    if dry_run:
        for bid in vanish_ids + manual_ids:
            append_event(
                case,
                bid,
                "APPROVED",
                lane=LANE,
                meta={
                    "campaign_id": campaign_id,
                    "dry_run": True,
                    "scan_phase": "exposure_dry_run",
                },
            )
            approved_ids.append(bid)
    else:
        if vanish_ids:
            if vanish_installed():
                delegation = delegate_vanish_scan(
                    case,
                    vanish_ids,
                    campaign_id=campaign_id,
                    execute=True,
                    registry=registry_path,
                )
                if delegation["exit_code"] == 0:
                    record_approved_batch(
                        case,
                        vanish_ids,
                        campaign_id=campaign_id,
                        dry_run=False,
                        evidence_path=delegation.get("result", {}).get("evidence_log"),
                    )
                    approved_ids.extend(vanish_ids)
                else:
                    append_failed_batch(
                        case,
                        vanish_ids,
                        LANE,
                        reason=f"vanish scan exit {delegation['exit_code']}",
                        campaign_id=campaign_id,
                    )
            else:
                record_manual_required(
                    case,
                    vanish_ids,
                    campaign_id=campaign_id,
                    reason=VANISH_INSTALL_HINT,
                )
                for bid in vanish_ids:
                    manual_required.append({"broker_id": bid, "reason": VANISH_INSTALL_HINT})

        for bid in manual_ids:
            reason = "non-vanish people-search target; manual scan or Playwright deferred"
            record_manual_required(case, [bid], campaign_id=campaign_id, reason=reason)
            manual_required.append({"broker_id": bid, "reason": reason})

    report = {
        "generated_at": utc_now(),
        "case": case,
        "lane": LANE,
        "mode": "scan",
        "dry_run": dry_run,
        "execute": execute,
        "delta_only": delta_only,
        "campaign_id": campaign_id,
        "registry_path": str(registry_path),
        "scan_target_count": len(targets),
        "target_broker_ids": [b["id"] for b in targets],
        "prior_target_count": len(prior_report.get("target_broker_ids", []))
        if prior_report
        else 0,
        "events_planned_written": events_written,
        "vanish_delegated_count": len(vanish_ids) if execute else 0,
        "manual_required_count": len(manual_required),
        "approved_count": len(approved_ids),
        "delegation": delegation,
        "manual_required": manual_required,
        "matches": delegation.get("result", {}).get("submitted", []) if delegation else [],
        "plan_path": str(plan_path),
        "note": None if execute else "dry-run: no vanish subprocess for live execute",
    }
    write_json(report_path, report)

    return {
        "plan_path": str(plan_path),
        "report_path": str(report_path),
        "scan_target_count": len(targets),
        "dry_run": dry_run,
        "report": report,
    }


def run_verify(
    *,
    case: str,
    registry_path: Path,
    dry_run: bool,
    max_n: int,
) -> dict[str, Any]:
    data = load_registry(registry_path)
    brokers = data.get("brokers", [])
    targets = select_verify_targets(brokers, max_n=max_n)

    campaign_id = str(uuid.uuid4())[:8]
    execute = (not dry_run) and os.environ.get("OPACITE_EXPOSURE_EXECUTE") == "1"
    if not dry_run and not execute:
        raise SystemExit(
            "error: live verify requires OPACITE_EXPOSURE_EXECUTE=1 "
            "(human gate; use --dry-run otherwise)"
        )

    exports = (SKILL_ROOT / "localonly" / "cases" / case / "exports")
    plan_path = exports / "exposure_verify_plan.json"
    report_path = exports / "exposure_report.json"

    plan = {
        "generated_at": utc_now(),
        "case": case,
        "lane": LANE,
        "mode": "verify",
        "dry_run": dry_run,
        "campaign_id": campaign_id,
        "verify_target_count": len(targets),
        "max": max_n,
        "targets": [target_row(b, action="plan_verify") for b in targets],
    }
    write_json(plan_path, plan)

    init_state_db(case)
    broker_ids = [b["id"] for b in targets]
    delegation: dict[str, Any] | None = None
    verified: list[str] = []
    relisted: list[str] = []
    manual_required: list[dict[str, str]] = []

    if not broker_ids:
        note = "no vanish people-search targets in sample; nothing to verify"
    elif dry_run:
        delegation = delegate_vanish_verify(
            case,
            broker_ids,
            campaign_id=campaign_id,
            execute=False,
            registry=registry_path,
        )
        if delegation["exit_code"] == 0:
            verified = delegation.get("result", {}).get("submitted", broker_ids)
        else:
            manual_required.append(
                {
                    "broker_id": "batch",
                    "reason": f"vanish verify dry-run exit {delegation['exit_code']}",
                }
            )
        note = "dry-run: vanish verify delegated (CI-safe without vanish CLI)"
    else:
        if vanish_installed():
            delegation = delegate_vanish_verify(
                case,
                broker_ids,
                campaign_id=campaign_id,
                execute=True,
                registry=registry_path,
            )
            if delegation["exit_code"] == 0:
                result = delegation.get("result", {})
                verified = list(result.get("submitted", []))
                relisted = list(result.get("failed", []))
            else:
                append_failed_batch(
                    case,
                    broker_ids,
                    LANE,
                    reason=f"vanish verify exit {delegation['exit_code']}",
                    campaign_id=campaign_id,
                )
        else:
            record_manual_required(
                case,
                broker_ids,
                campaign_id=campaign_id,
                reason=VANISH_INSTALL_HINT,
            )
            for bid in broker_ids:
                manual_required.append({"broker_id": bid, "reason": VANISH_INSTALL_HINT})
        note = None if execute else "dry-run"

    report = {
        "generated_at": utc_now(),
        "case": case,
        "lane": LANE,
        "mode": "verify",
        "dry_run": dry_run,
        "execute": execute,
        "campaign_id": campaign_id,
        "registry_path": str(registry_path),
        "verify_target_count": len(targets),
        "verified_count": len(verified),
        "relisted_count": len(relisted),
        "manual_required_count": len(manual_required),
        "delegation": delegation,
        "verified": verified,
        "relisted": relisted,
        "manual_required": manual_required,
        "plan_path": str(plan_path),
        "note": note,
    }
    write_json(report_path, report)

    return {
        "plan_path": str(plan_path),
        "report_path": str(report_path),
        "verify_target_count": len(targets),
        "dry_run": dry_run,
        "report": report,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="opacite exposure scan (lane=scan)")
    p.add_argument("--case", required=True)
    p.add_argument("--registry", type=Path, default=REGISTRY_DEFAULT)
    p.add_argument("--dry-run", action="store_true", default=False)
    p.add_argument("--no-dry-run", action="store_true", dest="no_dry_run")
    p.add_argument("--delta-only", action="store_true")
    p.add_argument(
        "--verify",
        action="store_true",
        help="exposure verify pass (vanish --no-fetch dry-run; lane=scan events)",
    )
    p.add_argument(
        "--max",
        type=int,
        default=5,
        help="max vanish brokers for --verify sample (default 5)",
    )
    args = p.parse_args()

    dry_run = not args.no_dry_run
    if args.dry_run:
        dry_run = True

    if not args.registry.is_file():
        raise SystemExit(
            f"error: registry not found: {args.registry}\n"
            "hint: run registry_sync.sh first"
        )

    if args.verify:
        out = run_verify(
            case=args.case,
            registry_path=args.registry,
            dry_run=dry_run,
            max_n=args.max,
        )
        print(
            f"exposure verify: {out['verify_target_count']} targets "
            f"({'dry-run' if out['dry_run'] else 'execute'}) "
            f"→ {out['report_path']}"
        )
        if out["dry_run"]:
            print("dry-run: vanish verify without live HTTP")
        return

    out = run_scan(
        case=args.case,
        registry_path=args.registry,
        dry_run=dry_run,
        delta_only=args.delta_only,
    )
    print(
        f"exposure scan: {out['scan_target_count']} targets "
        f"({'dry-run' if out['dry_run'] else 'execute'}) "
        f"→ {out['report_path']}"
    )
    if out["dry_run"]:
        print("dry-run: no vanish live execute")


if __name__ == "__main__":
    main()
