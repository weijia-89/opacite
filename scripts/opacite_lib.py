#!/usr/bin/env python3
"""Shared helpers for opacite.skill scripts."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_SQL = SKILL_ROOT / "schemas" / "campaign.sql"
REGISTRY_DEFAULT = SKILL_ROOT / "localonly" / "registry" / "unified-brokers.json"
HEALTH_DEFAULT = SKILL_ROOT / "localonly" / "registry" / "registry_health.json"

# Latest event in this set → skip new PLANNED for same lane (idempotent --plan).
ACTIVE_PLAN_STATES = frozenset({
    "PLANNED",
    "APPROVED",
    "SUBMITTED",
    "AWAITING_REPLY",
    "VERIFIED_REMOVED",
})


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_registry(path: Path | str = REGISTRY_DEFAULT) -> dict[str, Any]:
    p = Path(path)
    with p.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {"brokers": data, "count": len(data)}
    return data


def load_health_report(path: Path | str = HEALTH_DEFAULT) -> dict[str, Any] | None:
    p = Path(path)
    if not p.is_file():
        return None
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def health_status_by_broker(report: dict[str, Any] | None) -> dict[str, str]:
    if not report:
        return {}
    out: dict[str, str] = {}
    for row in report.get("results", []):
        bid = row.get("broker_id")
        if bid:
            out[str(bid)] = str(row.get("status", "unknown"))
    return out


def case_dir(slug: str) -> Path:
    return SKILL_ROOT / "localonly" / "cases" / slug


def mandate_manifest_path(slug: str) -> Path:
    return case_dir(slug) / "mandate" / "manifest.json"


def mandate_ready(slug: str) -> bool:
    """True when mandate_generate.py has run for this case."""
    return mandate_manifest_path(slug).is_file()


def require_mandate(slug: str) -> None:
    if mandate_ready(slug):
        return
    raise SystemExit(
        f"error: no mandate for case {slug!r} — run:\n"
        f"  python3 scripts/mandate_generate.py --case {slug}\n"
        "  (print/sign PDF before --confirm email sends)"
    )


def expand_profile_aliases(profile: dict[str, Any]) -> dict[str, Any]:
    """Normalize legal name + aliases + contact lists for matching (ROADMAP 1.5)."""
    ln = profile.get("legal_name") or {}
    legal_first = (ln.get("first") or profile.get("first_name") or "").strip()
    legal_last = (ln.get("last") or profile.get("last_name") or "").strip()
    name_variants: list[dict[str, str]] = []
    if legal_first or legal_last:
        name_variants.append({
            "kind": "legal",
            "first": legal_first,
            "last": legal_last,
            "full": f"{legal_first} {legal_last}".strip(),
        })
    for i, alias in enumerate(profile.get("aliases") or []):
        if not isinstance(alias, dict):
            continue
        first = (alias.get("first") or "").strip()
        last = (alias.get("last") or "").strip()
        if not first and not last:
            continue
        name_variants.append({
            "kind": f"alias_{i}",
            "first": first,
            "last": last,
            "full": f"{first} {last}".strip(),
        })
    emails = [str(e).strip() for e in (profile.get("emails") or []) if e and str(e).strip()]
    phones = [str(p).strip() for p in (profile.get("phones") or []) if p and str(p).strip()]
    addresses = [a for a in (profile.get("addresses") or []) if a]
    return {
        "name_variants": name_variants,
        "emails": emails,
        "phones": phones,
        "addresses": addresses,
        "identifier_count": len(name_variants) * max(len(emails), 1),
    }


def state_db_path(slug: str) -> Path:
    return case_dir(slug) / "state.sqlite"


def _migrate_db(conn: sqlite3.Connection) -> None:
    """One-time hygiene for schema_version duplicates on legacy DBs."""
    conn.execute(
        """
        DELETE FROM schema_version
        WHERE rowid NOT IN (SELECT MIN(rowid) FROM schema_version)
        """
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_schema_version ON schema_version(version)"
    )


def init_state_db(slug: str) -> Path:
    db = state_db_path(slug)
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    try:
        if SCHEMA_SQL.is_file():
            conn.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
        _migrate_db(conn)
        conn.commit()
    finally:
        conn.close()
    return db


def append_event(
    slug: str,
    broker_id: str,
    event: str,
    *,
    lane: str | None = None,
    evidence_path: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    init_state_db(slug)
    conn = sqlite3.connect(state_db_path(slug))
    try:
        conn.execute(
            """
            INSERT INTO broker_events (case_slug, broker_id, event, lane, ts, evidence_path, meta_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slug,
                broker_id,
                event,
                lane,
                utc_now(),
                evidence_path,
                json.dumps(meta) if meta else None,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def latest_events(slug: str, lane: str | None = None) -> dict[str, str]:
    """broker_id → latest event name (per lane when lane is set).

    When lane is set, partition by (broker_id, lane) so a web SUBMITTED does not
    mask an email PLANNED on the same broker (OB-01 / append_planned_batch).
    """
    init_state_db(slug)
    conn = sqlite3.connect(state_db_path(slug))
    try:
        if lane is not None:
            # COALESCE(lane,'') matches rows where lane IS NULL only when lane arg is ''.
            rows = conn.execute(
                """
                SELECT broker_id, event FROM (
                  SELECT broker_id, event,
                         ROW_NUMBER() OVER (
                           PARTITION BY broker_id, COALESCE(lane, '')
                           ORDER BY id DESC
                         ) AS rn
                  FROM broker_events
                  WHERE case_slug = ? AND COALESCE(lane, '') = ?
                ) e WHERE e.rn = 1
                """,
                (slug, lane),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT broker_id, event FROM (
                  SELECT broker_id, event,
                         ROW_NUMBER() OVER (PARTITION BY broker_id ORDER BY id DESC) AS rn
                  FROM broker_events WHERE case_slug = ?
                ) e WHERE e.rn = 1
                """,
                (slug,),
            ).fetchall()
        return {bid: event for bid, event in rows}
    finally:
        conn.close()


def append_planned_batch(
    slug: str,
    brokers: list[dict[str, Any]],
    lane: str,
    campaign_id: str | None = None,
) -> int:
    """Append PLANNED events; skip brokers already active on this lane."""
    meta_base = {"campaign_id": campaign_id} if campaign_id else {}
    current = latest_events(slug, lane=lane)
    written = 0
    for b in brokers:
        bid = b["id"]
        if current.get(bid) in ACTIVE_PLAN_STATES:
            continue
        meta = {**meta_base, "name": b.get("name"), "process": b.get("process")}
        append_event(slug, bid, "PLANNED", lane=lane, meta=meta)
        written += 1
    return written


def append_submitted_batch(
    slug: str,
    broker_ids: list[str],
    lane: str,
    *,
    campaign_id: str | None = None,
    runner: str = "eraser",
    evidence_path: str | None = None,
) -> int:
    meta_base: dict[str, Any] = {"runner": runner}
    if campaign_id:
        meta_base["campaign_id"] = campaign_id
    for bid in broker_ids:
        append_event(
            slug,
            bid,
            "SUBMITTED",
            lane=lane,
            evidence_path=evidence_path,
            meta=meta_base,
        )
    return len(broker_ids)


def append_failed_batch(
    slug: str,
    broker_ids: list[str],
    lane: str,
    *,
    reason: str,
    campaign_id: str | None = None,
) -> int:
    meta: dict[str, Any] = {"reason": reason}
    if campaign_id:
        meta["campaign_id"] = campaign_id
    for bid in broker_ids:
        append_event(slug, bid, "FAILED", lane=lane, meta=meta)
    return len(broker_ids)


def status_summary(slug: str) -> dict[str, int]:
    init_state_db(slug)
    conn = sqlite3.connect(state_db_path(slug))
    try:
        rows = conn.execute(
            """
            SELECT e.event, COUNT(*) FROM (
              SELECT broker_id, event,
                     ROW_NUMBER() OVER (PARTITION BY broker_id ORDER BY id DESC) AS rn
              FROM broker_events WHERE case_slug = ?
            ) e WHERE e.rn = 1 GROUP BY e.event
            """,
            (slug,),
        ).fetchall()
        return {event: count for event, count in rows}
    finally:
        conn.close()
