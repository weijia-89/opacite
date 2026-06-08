#!/usr/bin/env python3
"""Invoke digisamroc/eraser CLI for a filtered broker batch; record SQLite events."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from opacite_lib import (  # noqa: E402
    REGISTRY_DEFAULT,
    append_failed_batch,
    append_submitted_batch,
    case_dir,
    init_state_db,
    load_registry,
)
from opacite_registry import _name_slug_matches, slugify  # noqa: E402

ERASER_CACHE = SKILL_ROOT / "localonly" / "registry" / "cache" / "eraser-brokers.yaml"


def find_eraser() -> str | None:
    env_bin = os.environ.get("ERASER_BIN")
    if env_bin and Path(env_bin).is_file():
        return env_bin
    for candidate in (
        Path.home() / "bin" / "eraser",
        Path("/usr/local/bin/eraser"),
    ):
        if candidate.is_file():
            return str(candidate)
    return shutil.which("eraser")


def load_eraser_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as e:
        raise SystemExit("error: pip install pyyaml for eraser adapter") from e
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _index_eraser_brokers(brokers: list[dict[str, Any]]) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    by_id: dict[str, dict[str, Any]] = {}
    by_email: dict[str, dict[str, Any]] = {}
    by_slug: dict[str, dict[str, Any]] = {}
    for item in brokers:
        if not isinstance(item, dict):
            continue
        bid = str(item.get("id", "")).lower()
        if bid:
            by_id[bid] = item
            by_slug[bid] = item
        email = (item.get("email") or "").strip().lower()
        if email:
            by_email[email] = item
        name_slug = slugify(str(item.get("name") or ""))
        if name_slug:
            by_slug[name_slug] = item
    return by_id, by_email, by_slug


def synthesize_eraser_item(opacite_broker: dict[str, Any]) -> dict[str, Any]:
    email = (opacite_broker.get("contact_email") or "").strip()
    if not email:
        raise ValueError(f"no contact_email for broker {opacite_broker.get('id')}")
    eraser_id = opacite_broker.get("eraser_id") or slugify(
        opacite_broker.get("name") or str(opacite_broker["id"])
    )
    return {
        "id": eraser_id,
        "name": opacite_broker.get("name", eraser_id),
        "email": email,
        "website": opacite_broker.get("url") or "",
        "opt_out_url": opacite_broker.get("opt_out_url") or "",
        "region": "us",
        "category": opacite_broker.get("broker_class") or "marketing",
    }


def resolve_brokers_for_eraser(
    opacite_ids: list[str],
    eraser_yaml: Path,
    registry_path: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Map opacite registry ids (often Optery numerics) → eraser YAML broker entries."""
    data = load_eraser_yaml(eraser_yaml)
    by_id, by_email, by_slug = _index_eraser_brokers(data.get("brokers", []))

    registry = load_registry(registry_path)
    opacite_by_id = {b["id"]: b for b in registry.get("brokers", []) if b.get("id")}

    kept: list[dict[str, Any]] = []
    unresolved: list[str] = []
    for oid in opacite_ids:
        ob = opacite_by_id.get(oid)
        if not ob:
            unresolved.append(oid)
            continue
        item: dict[str, Any] | None = None
        eraser_id = ob.get("eraser_id")
        if eraser_id:
            item = by_id.get(str(eraser_id).lower())
        if item is None:
            item = by_id.get(oid.lower())
        if item is None:
            em = (ob.get("contact_email") or "").strip().lower()
            if em:
                item = by_email.get(em)
        if item is None:
            ob_slug = slugify(ob.get("name") or "")
            item = by_slug.get(ob_slug)
        if item is None:
            for candidate in by_slug.values():
                if _name_slug_matches(ob.get("name") or "", candidate.get("name") or ""):
                    item = candidate
                    break
        if item is None:
            eraser_id = ob.get("eraser_id")
            if eraser_id:
                item = by_id.get(str(eraser_id).lower())
        if item is None:
            try:
                item = synthesize_eraser_item(ob)
            except ValueError:
                unresolved.append(oid)
                continue
        kept.append(item)

    if not kept:
        raise SystemExit(
            f"error: could not resolve any of {len(opacite_ids)} broker id(s) "
            f"for eraser (unresolved: {unresolved})"
        )
    if unresolved:
        print(
            f"warn: {len(unresolved)} broker id(s) skipped (no email / not in registry): "
            + ", ".join(unresolved),
            file=sys.stderr,
        )
    return kept, unresolved


def write_brokers_yaml(items: list[dict[str, Any]], out: Path) -> int:
    out.write_text(
        __import__("yaml").dump({"brokers": items}, sort_keys=False),
        encoding="utf-8",
    )
    return len(items)


def parse_eraser_success(
    stdout: str,
    broker_ids: list[str],
    *,
    opacite_by_id: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[str], list[str]]:
    """Best-effort map eraser CLI output → opacite broker ids."""
    submitted: list[str] = []
    failed: list[str] = []
    opacite_by_id = opacite_by_id or {}

    def match_line_to_opacite_id(name: str, email_hint: str = "") -> str | None:
        name_l = name.lower()
        email_l = email_hint.lower()
        for bid in broker_ids:
            if bid.lower() in name_l or name_l in bid.lower():
                return bid
        for bid in broker_ids:
            ob = opacite_by_id.get(bid) or {}
            if slugify(ob.get("name") or "") in name_l or name_l in slugify(
                ob.get("name") or ""
            ):
                return bid
            if email_l and (ob.get("contact_email") or "").lower() == email_l:
                return bid
        return None

    for line in stdout.splitlines():
        m = re.search(r"\]\s+(.+?)\s+\(([^)]+)\)", line)
        if not m:
            continue
        name = m.group(1).strip()
        email_hint = m.group(2).strip()
        matched = match_line_to_opacite_id(name, email_hint)
        if matched is None:
            continue
        if "error" in line.lower() or "failed" in line.lower():
            if matched not in failed:
                failed.append(matched)
        elif "sent" in line.lower() or "would send" in line.lower() or "✓" in line:
            if matched not in submitted:
                submitted.append(matched)

    if not submitted and not failed:
        return list(broker_ids), []
    mentioned = set(submitted) | set(failed)
    for bid in broker_ids:
        if bid not in mentioned:
            submitted.append(bid)
    return submitted, failed


def run_eraser_send(brokers_yaml: Path, *, dry_run: bool) -> subprocess.CompletedProcess[str]:
    eraser = find_eraser()
    if not eraser:
        raise SystemExit("error: eraser not found")
    cmd = [eraser, "send", "--brokers", str(brokers_yaml)]
    if dry_run:
        cmd.append("--dry-run")
    return subprocess.run(cmd, capture_output=True, text=True)


def main() -> None:
    p = argparse.ArgumentParser(description="opacite → eraser email lane adapter")
    p.add_argument("--case", required=True)
    p.add_argument("--broker-ids", required=True, help="comma-separated opacite broker ids")
    p.add_argument("--campaign-id", default=None)
    p.add_argument("--lane", default="email")
    p.add_argument("--eraser-yaml", type=Path, default=ERASER_CACHE)
    p.add_argument("--registry", type=Path, default=REGISTRY_DEFAULT)
    p.add_argument("--dry-run", action="store_true", help="eraser send --dry-run (no SMTP)")
    p.add_argument("--json", action="store_true", dest="as_json")
    args = p.parse_args()

    if not find_eraser():
        raise SystemExit(
            "error: eraser not in PATH — install from https://github.com/digisamroc/eraser "
            "and run `eraser init` first (or set ERASER_BIN=/path/to/eraser)"
        )
    if not args.eraser_yaml.is_file():
        raise SystemExit(f"error: eraser broker yaml missing: {args.eraser_yaml}")

    broker_ids = [x.strip() for x in args.broker_ids.split(",") if x.strip()]
    if not broker_ids:
        raise SystemExit("error: empty --broker-ids")

    registry = load_registry(args.registry)
    opacite_by_id = {b["id"]: b for b in registry.get("brokers", []) if b.get("id")}

    init_state_db(args.case)
    evidence_dir = case_dir(args.case) / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="opacite-eraser-") as tmp:
        brokers_yaml = Path(tmp) / "batch.yaml"
        items, _skipped = resolve_brokers_for_eraser(
            broker_ids, args.eraser_yaml, args.registry
        )
        n = write_brokers_yaml(items, brokers_yaml)
        proc = run_eraser_send(brokers_yaml, dry_run=args.dry_run)
        log_path = evidence_dir / f"eraser-{'dryrun' if args.dry_run else 'send'}-{args.campaign_id or 'batch'}.log"
        log_path.write_text(
            proc.stdout + ("\n--- stderr ---\n" + proc.stderr if proc.stderr else ""),
            encoding="utf-8",
        )

        if proc.returncode != 0:
            append_failed_batch(
                args.case,
                broker_ids,
                args.lane,
                reason=f"eraser exit {proc.returncode}",
                campaign_id=args.campaign_id,
            )
            raise SystemExit(
                f"error: eraser send failed (exit {proc.returncode}); log: {log_path}\n{proc.stderr}"
            )

        submitted, failed = parse_eraser_success(
            proc.stdout, broker_ids, opacite_by_id=opacite_by_id
        )
        if not args.dry_run:
            append_submitted_batch(
                args.case,
                submitted,
                args.lane,
                campaign_id=args.campaign_id,
                evidence_path=str(log_path),
            )
        else:
            from opacite_lib import append_event

            for bid in submitted:
                append_event(
                    args.case,
                    bid,
                    "APPROVED",
                    lane=args.lane,
                    evidence_path=str(log_path),
                    meta={"campaign_id": args.campaign_id, "dry_run": True},
                )
        if failed:
            append_failed_batch(
                args.case,
                failed,
                args.lane,
                reason="eraser send line error",
                campaign_id=args.campaign_id,
            )

    result = {
        "case": args.case,
        "lane": args.lane,
        "campaign_id": args.campaign_id,
        "dry_run": args.dry_run,
        "brokers_requested": len(broker_ids),
        "brokers_in_yaml": n,
        "submitted": submitted,
        "failed": failed,
        "evidence_log": str(log_path),
    }
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"eraser {'dry-run' if args.dry_run else 'send'}: "
            f"{len(submitted)} ok, {len(failed)} failed → {log_path}"
        )


if __name__ == "__main__":
    main()
