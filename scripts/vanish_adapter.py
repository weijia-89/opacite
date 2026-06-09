#!/usr/bin/env python3
"""Invoke RAMBOXIE/vanish for scan + verify only; block opt-out until consent gate."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from mandate_generate import load_profile  # noqa: E402
from opacite_lib import (  # noqa: E402
    REGISTRY_DEFAULT,
    append_event,
    append_failed_batch,
    append_submitted_batch,
    case_dir,
    init_state_db,
    load_registry,
)

# Phase 3: scan + verify only. Opt-out and cloud probes blocked (Palamedes synthesis).
ALLOWED_ACTIONS = frozenset({"scan", "verify"})
BLOCKED_ACTIONS = frozenset({
    "opt-out",
    "llm-memory-check",
    "b1-live",
    "face-opt-out",
    "ai-opt-out",
    "takedown",
    "cleanup",
    "wizard",
})

DEFAULT_TIMEOUT_S = 300
INSTALL_HINT = (
    "error: vanish not found — install RAMBOXIE/vanish (Node ≥20):\n"
    "  npm install -g vanish   # or: npx --yes vanish scan --help\n"
    "  git clone https://github.com/RAMBOXIE/vanish && cd vanish && npm link\n"
    "Set VANISH_BIN=/path/to/vanish to override discovery."
)


def find_vanish() -> list[str] | None:
    """Return command prefix: ['/bin/vanish'] or ['npx', '--yes', 'vanish']."""
    env_bin = os.environ.get("VANISH_BIN")
    if env_bin and Path(env_bin).is_file():
        return [env_bin]
    direct = shutil.which("vanish")
    if direct:
        return [direct]
    npx = shutil.which("npx")
    if npx:
        return [npx, "--yes", "vanish"]
    return None


def resolve_vanish_broker_slug(
    broker_id: str,
    opacite_by_id: dict[str, dict[str, Any]],
) -> str:
    """Map opacite registry id → vanish --broker slug (best effort)."""
    ob = opacite_by_id.get(broker_id) or {}
    for key in ("vanish_id", "eraser_id", "symaira_id"):
        val = ob.get(key)
        if val:
            return str(val).strip().lower()
    name = (ob.get("name") or broker_id).strip().lower()
    return name.replace(" ", "-").replace("_", "-")


def scan_identity_args(profile: dict[str, Any]) -> dict[str, str]:
    ln = profile.get("legal_name") or {}
    first = (ln.get("first") or profile.get("first_name") or "").strip()
    last = (ln.get("last") or profile.get("last_name") or "").strip()
    full_name = f"{first} {last}".strip()
    if not full_name:
        raise SystemExit(
            "error: profile missing legal_name — fill localonly/vault/profile.yaml"
        )
    emails = profile.get("emails") or []
    email = str(emails[0]).strip() if emails else ""
    if not email:
        raise SystemExit(
            "error: profile missing emails[0] — fill localonly/vault/profile.yaml"
        )
    out: dict[str, str] = {"name": full_name, "email": email}
    phones = profile.get("phones") or []
    if phones:
        out["phone"] = str(phones[0]).strip()
    addresses = profile.get("addresses") or []
    if addresses and isinstance(addresses[0], dict):
        addr = addresses[0]
        if addr.get("city"):
            out["city"] = str(addr["city"]).strip()
        if addr.get("state"):
            out["state"] = str(addr["state"]).strip()
    return out


def build_scan_cmd(
    prefix: list[str],
    identity: dict[str, str],
    *,
    output_json: Path | None = None,
) -> list[str]:
    cmd = prefix + [
        "scan",
        "--name",
        identity["name"],
        "--email",
        identity["email"],
        "--json",
        "--no-banner",
    ]
    if identity.get("phone"):
        cmd.extend(["--phone", identity["phone"]])
    if identity.get("city"):
        cmd.extend(["--city", identity["city"]])
    if identity.get("state"):
        cmd.extend(["--state", identity["state"]])
    if output_json is not None:
        cmd.extend(["--output-json", str(output_json)])
    return cmd


def build_verify_cmd(
    prefix: list[str],
    broker_slugs: list[str],
    *,
    dry_run: bool,
) -> list[str]:
    cmd = prefix + ["verify", "--broker", ",".join(broker_slugs)]
    if dry_run:
        cmd.append("--no-fetch")
    return cmd


def run_vanish_subprocess(
    cmd: list[str],
    *,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            start_new_session=True,
        )
    except subprocess.TimeoutExpired as exc:
        if exc.pid:
            try:
                os.killpg(exc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        raise SystemExit(
            f"error: vanish timed out after {timeout_s}s: {' '.join(cmd)}"
        ) from exc


def record_blocked_optout(
    case: str,
    broker_ids: list[str],
    lane: str,
    *,
    campaign_id: str | None,
    reason: str,
) -> None:
    meta: dict[str, Any] = {
        "reason": reason,
        "runner": "vanish",
        "phase3_blocked": True,
    }
    if campaign_id:
        meta["campaign_id"] = campaign_id
    for bid in broker_ids:
        append_event(case, bid, "MANUAL_REQUIRED", lane=lane, meta=meta)


def main() -> None:
    p = argparse.ArgumentParser(
        description="opacite → vanish scan/verify lane (opt-out blocked Phase 3)"
    )
    p.add_argument("--case", required=True)
    p.add_argument("--broker-ids", required=True, help="comma-separated opacite broker ids")
    p.add_argument("--campaign-id", default=None)
    p.add_argument("--lane", default="vanish")
    p.add_argument(
        "--action",
        choices=sorted(ALLOWED_ACTIONS | BLOCKED_ACTIONS),
        default="scan",
        help="scan or verify (opt-out and labs commands blocked)",
    )
    p.add_argument("--vault", type=Path, default=SKILL_ROOT / "localonly" / "vault")
    p.add_argument("--registry", type=Path, default=REGISTRY_DEFAULT)
    p.add_argument(
        "--execute",
        action="store_true",
        help="run vanish for real (requires OPACITE_VANISH_EXECUTE=1)",
    )
    p.add_argument("--json", action="store_true", dest="as_json")
    args = p.parse_args()

    broker_ids = [x.strip() for x in args.broker_ids.split(",") if x.strip()]
    if not broker_ids:
        raise SystemExit("error: empty --broker-ids")

    # Blocked actions need no vanish binary — record MANUAL_REQUIRED and exit.
    if args.action in BLOCKED_ACTIONS:
        init_state_db(args.case)
        reason = (
            f"vanish {args.action} blocked until opacite consent gate (Phase 3 scan-only)"
        )
        record_blocked_optout(
            args.case,
            broker_ids,
            args.lane,
            campaign_id=args.campaign_id,
            reason=reason,
        )
        raise SystemExit(
            f"error: {reason}\n"
            "Use --action scan or verify. Browser opt-out awaits opacite consent gate."
        )

    dry_run = not args.execute
    if os.environ.get("OPACITE_VANISH_EXECUTE") == "1":
        dry_run = False

    prefix = find_vanish()
    vanish_cli_missing = prefix is None
    if not prefix:
        # Scan/verify dry-run logs intent only — no subprocess; vanish need not be installed (CI).
        if args.action in ALLOWED_ACTIONS and dry_run:
            prefix = ["vanish"]
        else:
            raise SystemExit(INSTALL_HINT)

    registry = load_registry(args.registry)
    opacite_by_id = {b["id"]: b for b in registry.get("brokers", []) if b.get("id")}
    broker_slugs = [
        resolve_vanish_broker_slug(bid, opacite_by_id) for bid in broker_ids
    ]

    init_state_db(args.case)
    evidence_dir = case_dir(args.case) / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    campaign = args.campaign_id or "batch"

    profile = load_profile(args.vault)
    identity = scan_identity_args(profile)

    log_parts: list[str] = []
    proc: subprocess.CompletedProcess[str] | None = None

    if args.action == "scan":
        out_json = evidence_dir / f"vanish-scan-{campaign}.json"
        cmd = build_scan_cmd(prefix, identity, output_json=out_json)
        if dry_run:
            log_parts.append(
                f"# dry-run: would run\n$ {' '.join(cmd)}\n"
                "# vanish scan is local heuristic (Evidence C); no HTTP in scan itself\n"
            )
            submitted = list(broker_ids)
            failed: list[str] = []
        else:
            proc = run_vanish_subprocess(cmd)
            log_parts.append(f"$ {' '.join(cmd)}\n{proc.stdout}")
            if proc.stderr:
                log_parts.append(proc.stderr)
            if proc.returncode != 0:
                append_failed_batch(
                    args.case,
                    broker_ids,
                    args.lane,
                    reason=f"vanish scan exit {proc.returncode}",
                    campaign_id=args.campaign_id,
                )
                log_path = evidence_dir / f"vanish-scan-{campaign}.log"
                log_path.write_text("\n---\n".join(log_parts), encoding="utf-8")
                raise SystemExit(
                    f"error: vanish scan failed (exit {proc.returncode}); log: {log_path}"
                )
            submitted = list(broker_ids)
            failed = []

    else:  # verify
        cmd = build_verify_cmd(prefix, broker_slugs, dry_run=dry_run)
        if dry_run and vanish_cli_missing:
            log_parts.append(
                f"# dry-run: would run\n$ {' '.join(cmd)}\n"
                "# verify dry-run uses --no-fetch when vanish installed (Evidence A)\n"
            )
            submitted = list(broker_ids)
            failed = []
        else:
            proc = run_vanish_subprocess(cmd)
            log_parts.append(f"$ {' '.join(cmd)}\n{proc.stdout}")
            if proc.stderr:
                log_parts.append(proc.stderr)
            submitted = []
            failed = []
            if proc.returncode == 0:
                submitted = list(broker_ids)
            else:
                failed = list(broker_ids)

    mode = "dryrun" if dry_run else "run"
    log_path = evidence_dir / f"vanish-{args.action}-{mode}-{campaign}.log"
    log_path.write_text("\n---\n".join(log_parts), encoding="utf-8")

    meta_base: dict[str, Any] = {
        "runner": "vanish",
        "action": args.action,
        "campaign_id": args.campaign_id,
        "vanish_slugs": broker_slugs,
        "evidence_grade": "C" if args.action == "scan" else "A",
    }

    exposure_lane = args.lane == "scan" and args.action == "verify"

    if dry_run:
        for bid in submitted:
            dry_meta: dict[str, Any] = {**meta_base, "dry_run": True}
            if exposure_lane:
                dry_meta["exposure_status"] = "verify_dry_run"
            append_event(
                args.case,
                bid,
                "APPROVED",
                lane=args.lane,
                evidence_path=str(log_path),
                meta=dry_meta,
            )
        for bid in failed:
            append_failed_batch(
                args.case,
                [bid],
                args.lane,
                reason="vanish verify dry-run failed",
                campaign_id=args.campaign_id,
            )
    else:
        if exposure_lane:
            for bid in submitted:
                append_event(
                    args.case,
                    bid,
                    "VERIFIED_REMOVED",
                    lane=args.lane,
                    evidence_path=str(log_path),
                    meta={**meta_base, "exposure_status": "verified_removed"},
                )
            for bid in failed:
                append_event(
                    args.case,
                    bid,
                    "RE_LISTED",
                    lane=args.lane,
                    evidence_path=str(log_path),
                    meta={**meta_base, "exposure_status": "re_listed"},
                )
        else:
            if submitted:
                append_submitted_batch(
                    args.case,
                    submitted,
                    args.lane,
                    campaign_id=args.campaign_id,
                    runner="vanish",
                    evidence_path=str(log_path),
                )
            if failed:
                append_failed_batch(
                    args.case,
                    failed,
                    args.lane,
                    reason=f"vanish {args.action} failed",
                    campaign_id=args.campaign_id,
                )

    result = {
        "case": args.case,
        "lane": args.lane,
        "action": args.action,
        "dry_run": dry_run,
        "cli": prefix,
        "brokers_requested": len(broker_ids),
        "submitted": submitted,
        "failed": failed,
        "evidence_log": str(log_path),
        "opt_out_blocked": True,
        "llm_memory_check_blocked": True,
        "cloud_llm": False,
    }
    if args.action == "scan" and not dry_run:
        result["scan_json"] = str(evidence_dir / f"vanish-scan-{campaign}.json")

    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"vanish {args.action} ({mode}): "
            f"{len(submitted)} ok, {len(failed)} failed → {log_path}"
        )


if __name__ == "__main__":
    main()
