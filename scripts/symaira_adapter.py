#!/usr/bin/env python3
"""Invoke symaira-eraseme (symeraseme) for web-form brokers; record SQLite events."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from opacite_lib import (  # noqa: E402
    append_event,
    append_failed_batch,
    append_submitted_batch,
    case_dir,
    init_state_db,
)

CLI_CANDIDATES = ("symeraseme", "symaira-eraseme")


def find_symaira_cli() -> str | None:
    for name in CLI_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    return None


def run_symaira(
    cli: str,
    broker_ids: list[str],
    *,
    dry_run: bool,
    campaign: str,
    batch_size: int,
    delay: int,
) -> subprocess.CompletedProcess[str]:
    """Run symeraseme plan create + execute for explicit broker ids (best-effort)."""
    # symaira selects by campaign/jurisdiction; we filter via --broker-id when available
    cmds: list[list[str]] = []
    plan = f"opacite-{campaign}"
    cmds.append([cli, "plan", "create", "--campaign", plan, "--max", str(len(broker_ids))])
    for bid in broker_ids:
        cmds.append([cli, "brokers", "show", bid])
    exec_cmd = [
        cli, "plan", "execute",
        "--campaign", plan,
        "--batch-size", str(batch_size),
        "--delay", str(delay),
    ]
    if dry_run:
        exec_cmd.append("--dry-run")
    else:
        exec_cmd.append("--yes")
    cmds.append(exec_cmd)

    combined_out: list[str] = []
    combined_err: list[str] = []
    rc = 0
    for cmd in cmds:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        combined_out.append(f"$ {' '.join(cmd)}\n{proc.stdout}")
        if proc.stderr:
            combined_err.append(proc.stderr)
        if proc.returncode != 0:
            rc = proc.returncode
            break
    return subprocess.CompletedProcess(
        args=exec_cmd,
        returncode=rc,
        stdout="\n".join(combined_out),
        stderr="\n".join(combined_err),
    )


def run_web_form_fallback(
    cli: str,
    broker_id: str,
    *,
    dry_run: bool,
) -> subprocess.CompletedProcess[str]:
    cmd = [cli, "run-web-form", broker_id]
    if dry_run:
        cmd.append("--dry-run")
    return subprocess.run(cmd, capture_output=True, text=True)


def main() -> None:
    p = argparse.ArgumentParser(description="opacite → symaira web lane adapter")
    p.add_argument("--case", required=True)
    p.add_argument("--broker-ids", required=True, help="comma-separated symaira broker ids")
    p.add_argument("--campaign-id", default=None)
    p.add_argument("--lane", default="web")
    p.add_argument("--execute", action="store_true", help="run symaira for real (default: dry-run)")
    p.add_argument("--per-broker", action="store_true", help="use run-web-form per id instead of plan execute")
    p.add_argument("--json", action="store_true", dest="as_json")
    args = p.parse_args()

    dry_run = not args.execute
    if os.environ.get("OPACITE_SYMAIRA_EXECUTE") == "1":
        dry_run = False

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

    submitted: list[str] = []
    failed: list[str] = []

    if args.per_broker or len(broker_ids) <= 3:
        log_parts: list[str] = []
        for bid in broker_ids:
            proc = run_web_form_fallback(cli, bid, dry_run=dry_run)
            log_parts.append(proc.stdout + proc.stderr)
            if proc.returncode == 0:
                submitted.append(bid)
            else:
                failed.append(bid)
        log_path = evidence_dir / f"symaira-{'dryrun' if dry_run else 'run'}-{campaign}.log"
        log_path.write_text("\n---\n".join(log_parts), encoding="utf-8")
    else:
        with tempfile.TemporaryDirectory(prefix="opacite-symaira-") as tmp:
            proc = run_symaira(
                cli, broker_ids, dry_run=dry_run, campaign=campaign, batch_size=5, delay=30
            )
            log_path = evidence_dir / f"symaira-{'dryrun' if dry_run else 'run'}-{campaign}.log"
            log_path.write_text(
                proc.stdout + ("\n--- stderr ---\n" + proc.stderr if proc.stderr else ""),
                encoding="utf-8",
            )
            if proc.returncode != 0:
                failed = list(broker_ids)
            else:
                submitted = list(broker_ids)

    event = "APPROVED" if dry_run else "SUBMITTED"
    if dry_run:
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
    }
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        mode = "dry-run" if dry_run else "execute"
        print(f"symaira {mode}: {len(submitted)} ok, {len(failed)} failed → {log_path}")


if __name__ == "__main__":
    main()
