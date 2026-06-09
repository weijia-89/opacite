#!/usr/bin/env python3
"""Invoke symaira-eraseme (symeraseme) for web-form brokers; record SQLite events."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from opacite_lib import (  # noqa: E402
    append_failed_batch,
    append_submitted_batch,
    case_dir,
    init_state_db,
)

CLI_CANDIDATES = ("symeraseme", "symaira-eraseme")

# SY-01: symaira `plan create --max N` selects by campaign/jurisdiction, not opacite
# broker ids. Never call plan execute from opacite until upstream adds --broker-ids.


def find_symaira_cli() -> str | None:
    for name in CLI_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    return None


def run_web_form(
    cli: str,
    broker_id: str,
    *,
    dry_run: bool,
) -> subprocess.CompletedProcess[str]:
    cmd = [cli, "run-web-form", broker_id]
    if dry_run:
        cmd.append("--dry-run")
    return subprocess.run(cmd, capture_output=True, text=True)


def run_per_broker_batch(
    cli: str,
    broker_ids: list[str],
    *,
    dry_run: bool,
) -> tuple[list[str], list[str], list[str]]:
    """Run symeraseme run-web-form once per broker id (SY-01 safe path)."""
    log_parts: list[str] = []
    submitted: list[str] = []
    failed: list[str] = []
    for bid in broker_ids:
        proc = run_web_form(cli, bid, dry_run=dry_run)
        log_parts.append(f"$ {' '.join(proc.args)}\n{proc.stdout}")
        if proc.stderr:
            log_parts.append(proc.stderr)
        if proc.returncode == 0:
            submitted.append(bid)
        else:
            failed.append(bid)
    return submitted, failed, log_parts


def main() -> None:
    p = argparse.ArgumentParser(description="opacite → symaira web lane adapter")
    p.add_argument("--case", required=True)
    p.add_argument("--broker-ids", required=True, help="comma-separated symaira broker ids")
    p.add_argument("--campaign-id", default=None)
    p.add_argument("--lane", default="web")
    p.add_argument("--execute", action="store_true", help="run symaira for real (default: dry-run)")
    p.add_argument(
        "--per-broker",
        action="store_true",
        help="force run-web-form per id (default since SY-01: always on)",
    )
    p.add_argument(
        "--use-plan-execute",
        action="store_true",
        help="UNSAFE: plan create --max N does not honor --broker-ids (SY-01); do not use",
    )
    p.add_argument("--json", action="store_true", dest="as_json")
    args = p.parse_args()

    if args.use_plan_execute:
        raise SystemExit(
            "error: --use-plan-execute disabled (SY-01): symaira plan create selects by "
            "campaign/jurisdiction, not opacite broker ids — use run-web-form per broker"
        )

    dry_run = not args.execute
    if os.environ.get("OPACITE_SYMAIRA_EXECUTE") == "1":
        dry_run = False

    if not dry_run:
        from opacite_lib import require_mandate

        if os.environ.get("OPACITE_SKIP_MANDATE") != "1":
            require_mandate(args.case)

    cli = find_symaira_cli()
    if not cli:
        raise SystemExit(
            "error: symeraseme not in PATH — install symaira-eraseme:\n"
            "  pip install symaira-eraseme  # or clone github.com/danieljustus/symaira-eraseme"
        )

    broker_ids = [x.strip() for x in args.broker_ids.split(",") if x.strip()]
    if not broker_ids:
        raise SystemExit("error: empty --broker-ids")

    init_state_db(args.case)
    evidence_dir = case_dir(args.case) / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    campaign = args.campaign_id or "batch"

    submitted, failed, log_parts = run_per_broker_batch(cli, broker_ids, dry_run=dry_run)
    log_path = evidence_dir / f"symaira-{'dryrun' if dry_run else 'run'}-{campaign}.log"
    log_path.write_text("\n---\n".join(log_parts), encoding="utf-8")

    if dry_run:
        from opacite_lib import append_event

        for bid in submitted:
            append_event(
                args.case,
                bid,
                "APPROVED",
                lane=args.lane,
                evidence_path=str(log_path),
                meta={"campaign_id": args.campaign_id, "runner": "symaira", "dry_run": True},
            )
        for bid in failed:
            append_failed_batch(
                args.case, [bid], args.lane,
                reason="symaira dry-run failed", campaign_id=args.campaign_id,
            )
    else:
        if submitted:
            append_submitted_batch(
                args.case,
                submitted,
                args.lane,
                campaign_id=args.campaign_id,
                runner="symaira",
                evidence_path=str(log_path),
            )
        if failed:
            append_failed_batch(
                args.case, failed, args.lane,
                reason="symaira execute failed", campaign_id=args.campaign_id,
            )

    result = {
        "case": args.case,
        "lane": args.lane,
        "dry_run": dry_run,
        "cli": cli,
        "submitted": submitted,
        "failed": failed,
        "evidence_log": str(log_path),
        "cloud_llm_triage": False,
        "path": "run-web-form-per-broker",
    }
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        mode = "dry-run" if dry_run else "execute"
        print(f"symaira {mode}: {len(submitted)} ok, {len(failed)} failed → {log_path}")


if __name__ == "__main__":
    main()
