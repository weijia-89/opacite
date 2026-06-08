#!/usr/bin/env python3
"""Export manual follow-up queue for a case (FAILED events + manual-only brokers)."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from opacite_lib import (  # noqa: E402
    REGISTRY_DEFAULT,
    case_dir,
    init_state_db,
    load_registry,
    utc_now,
)

MANUAL_PROCESSES = frozenset({
    "id-verification",
    "phone-opt-out",
    "control-profile",
})

REASON_BY_PROCESS = {
    "id-verification": "id_verification",
    "phone-opt-out": "manual_process",
    "control-profile": "manual_process",
}


def broker_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {b["id"]: b for b in registry.get("brokers", []) if b.get("id")}


def latest_events_with_meta(slug: str) -> list[dict[str, Any]]:
    init_state_db(slug)
    db = case_dir(slug) / "state.sqlite"
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute(
            """
            SELECT broker_id, event, lane, evidence_path, meta_json FROM (
              SELECT broker_id, event, lane, evidence_path, meta_json,
                     ROW_NUMBER() OVER (PARTITION BY broker_id ORDER BY id DESC) AS rn
              FROM broker_events WHERE case_slug = ?
            ) e WHERE e.rn = 1
            """,
            (slug,),
        ).fetchall()
        out = []
        for bid, event, lane, evidence_path, meta_json in rows:
            meta = json.loads(meta_json) if meta_json else {}
            out.append({
                "broker_id": bid,
                "event": event,
                "lane": lane,
                "evidence_path": evidence_path,
                "meta": meta,
            })
        return out
    finally:
        conn.close()


def task_from_broker(
    broker: dict[str, Any],
    *,
    reason: str,
    lane: str,
    notes: str = "",
) -> dict[str, Any]:
    return {
        "broker_id": broker["id"],
        "name": broker.get("name"),
        "reason": reason,
        "lane": lane,
        "process": broker.get("process"),
        "opt_out_url": broker.get("opt_out_url"),
        "notes": notes,
    }


def build_tasks(slug: str, registry_path: Path) -> dict[str, Any]:
    registry = load_registry(registry_path)
    by_id = broker_index(registry)
    tasks: list[dict[str, Any]] = []
    seen: set[str] = set()

    for row in latest_events_with_meta(slug):
        bid = row["broker_id"]
        if bid in seen:
            continue
        event = row["event"]
        lane = row.get("lane") or "email"
        broker = by_id.get(bid, {"id": bid, "name": row["meta"].get("name")})
        if event == "FAILED":
            reason = "failed_send"
            notes = str(row["meta"].get("reason") or "send failed")
            tasks.append(task_from_broker(broker, reason=reason, lane=lane, notes=notes))
            seen.add(bid)
        elif event == "MANUAL_REQUIRED":
            tasks.append(task_from_broker(broker, reason="manual_process", lane=lane))
            seen.add(bid)
        elif event == "AWAITING_REPLY":
            tasks.append(task_from_broker(
                broker, reason="confirm_link", lane=lane, notes="broker reply needs operator"
            ))
            seen.add(bid)

    for bid, broker in by_id.items():
        if bid in seen:
            continue
        proc = broker.get("process") or ""
        if proc in MANUAL_PROCESSES:
            tasks.append(task_from_broker(
                broker,
                reason=REASON_BY_PROCESS.get(proc, "manual_process"),
                lane=broker.get("runner") or "web",
                notes=f"registry process={proc}",
            ))
            seen.add(bid)

    return {
        "case": slug,
        "generated_at": utc_now(),
        "task_count": len(tasks),
        "tasks": tasks,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Manual tasks — {payload['case']}",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        f"**{payload['task_count']}** item(s). Never upload government ID into this repo.",
        "",
    ]
    if not payload["tasks"]:
        lines.append("_No manual tasks queued._")
        return "\n".join(lines) + "\n"

    lines.append("| Broker | Reason | Lane | Notes |")
    lines.append("|--------|--------|------|-------|")
    for t in payload["tasks"]:
        lines.append(
            f"| {t.get('name') or t['broker_id']} | {t['reason']} | {t['lane']} | {t.get('notes', '')} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description="Export manual task queue for a case")
    p.add_argument("--case", required=True)
    p.add_argument("--registry", type=Path, default=REGISTRY_DEFAULT)
    p.add_argument("--json-only", action="store_true")
    args = p.parse_args()

    payload = build_tasks(args.case, args.registry)
    out_dir = case_dir(args.case) / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "manual_tasks.json"
    md_path = out_dir / "manual_tasks.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")

    if args.json_only:
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps({"json": str(json_path), "markdown": str(md_path), **payload}, indent=2))


if __name__ == "__main__":
    main()
