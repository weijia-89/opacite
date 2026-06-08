#!/usr/bin/env python3
"""Registry fetch, merge (Optery + eraser + symaira), normalize to opacite schema."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent

PROCESS_RANK: dict[str, int] = {
    "email-opt-out": 4,
    "drop-centralized": 4,
    "direct-form": 3,
    "search-for-removal": 2,
    "opt-out-search": 2,
    "captcha-gated": 1,
    "id-verification": 0,
}

RUNNER_RANK: dict[str, int] = {
    "eraser": 4,
    "drop": 4,
    "vanish": 3,
    "symaira": 2,
}


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:64] or "unknown"


def infer_tier(process: str) -> str:
    return {
        "email-opt-out": "A",
        "drop-centralized": "A",
        "direct-form": "B",
        "search-for-removal": "B",
        "opt-out-search": "B",
        "id-verification": "C",
        "captcha-gated": "C",
    }.get(process, "B")


def broker_class_from_type(broker_type: str) -> str:
    t = (broker_type or "people-search").lower()
    if "market" in t:
        return "marketing"
    if "background" in t:
        return "background-check"
    if "credit" in t:
        return "credit-bureau"
    return "people-search"


def is_drop_eligible(jurisdiction_list: list[str], process: str) -> bool:
    if process == "drop-centralized":
        return True
    return "US-CA" in jurisdiction_list


def make_broker(
    bid: str,
    name: str,
    item: dict[str, Any],
    sources: list[str],
    *,
    process: str | None = None,
    jurisdiction: str = "US",
) -> dict[str, Any]:
    process = process or infer_process_generic(item)
    broker_type = (
        item.get("type")
        or item.get("broker_class")
        or item.get("category")
        or "people-search"
    )
    jurs = item.get("jurisdiction") or item.get("jurisdictions")
    if isinstance(jurs, list):
        jurisdiction_list = jurs
    elif isinstance(jurs, str):
        jurisdiction_list = [jurs]
    elif jurisdiction == "US":
        jurisdiction_list = ["US"]
    else:
        jurisdiction_list = ["global"]

    runner = "eraser" if process == "email-opt-out" else "symaira"
    if process in ("search-for-removal", "opt-out-search"):
        runner = "vanish"
    if process == "drop-centralized":
        runner = "drop"

    return {
        "id": bid,
        "name": name,
        "url": item.get("website") or item.get("url"),
        "opt_out_url": item.get("optOutUrl") or item.get("opt_out_url"),
        "contact_email": item.get("contactEmail")
        or item.get("email")
        or item.get("contact_email"),
        "process": process,
        "broker_class": broker_class_from_type(str(broker_type)),
        "jurisdiction": jurisdiction_list,
        "drop_eligible": is_drop_eligible(jurisdiction_list, process),
        "automation_tier": infer_tier(process),
        "sources": list(sources),
        "runner": runner,
        "status": {"working": True, "as_of": date.today().isoformat()},
    }


def infer_process_generic(entry: dict[str, Any]) -> str:
    email = entry.get("contactEmail") or entry.get("email") or entry.get("contact_email")
    opt = entry.get("optOutUrl") or entry.get("opt_out_url") or ""
    if email and not opt:
        return "email-opt-out"
    if opt:
        u = str(opt).lower().strip()
        if u.startswith("mailto:"):
            return "email-opt-out"
        return "direct-form"
    if email:
        return "email-opt-out"
    return "search-for-removal"


def infer_process_symaira(doc: dict[str, Any]) -> tuple[str, str | None]:
    opt_outs = doc.get("opt_out") or []
    opt_url = None
    for o in opt_outs:
        if not isinstance(o, dict):
            continue
        t = (o.get("type") or "").lower()
        url = o.get("url")
        if t == "email" and o.get("email"):
            return "email-opt-out", f"mailto:{o['email']}"
        if t in ("web_form", "form", "url") and url:
            opt_url = url
            return "direct-form", url
    website = doc.get("website")
    if website:
        return "search-for-removal", website
    return "search-for-removal", None


def _ranked_upgrade(existing: dict[str, Any], incoming: dict[str, Any], key: str, ranks: dict[str, int]) -> None:
    cur = existing.get(key)
    new = incoming.get(key)
    if not new:
        return
    if not cur:
        existing[key] = new
        return
    if ranks.get(str(new), -1) > ranks.get(str(cur), -1):
        existing[key] = new
        if key == "process":
            existing["automation_tier"] = infer_tier(new)


def _name_slug_matches(a: str, b: str) -> bool:
    sa, sb = slugify(a), slugify(b)
    if not sa or not sb:
        return False
    if sa == sb:
        return True
    return sa.startswith(sb + "-") or sb.startswith(sa + "-")


def find_optery_merge_target(
    brokers_by_id: dict[str, dict[str, Any]],
    incoming: dict[str, Any],
) -> str | None:
    """Match eraser row to existing Optery broker by email or slugified name."""
    email = (incoming.get("contact_email") or "").lower()
    in_name = incoming.get("name") or ""
    for existing in brokers_by_id.values():
        if "optery" not in existing.get("sources", []):
            continue
        if email and (existing.get("contact_email") or "").lower() == email:
            return str(existing["id"])
        if _name_slug_matches(in_name, existing.get("name") or ""):
            return str(existing["id"])
    return None


def merge_broker(
    brokers_by_id: dict[str, dict[str, Any]],
    incoming: dict[str, Any],
) -> None:
    bid = incoming["id"]
    if bid not in brokers_by_id:
        brokers_by_id[bid] = incoming
        return
    existing = brokers_by_id[bid]
    for src in incoming.get("sources", []):
        if src not in existing["sources"]:
            existing["sources"].append(src)
    for key in ("opt_out_url", "contact_email", "url", "eraser_id"):
        if not existing.get(key) and incoming.get(key):
            existing[key] = incoming[key]
    _ranked_upgrade(existing, incoming, "process", PROCESS_RANK)
    _ranked_upgrade(existing, incoming, "runner", RUNNER_RANK)
    # Recompute drop_eligible after process/jurisdiction merge
    existing["drop_eligible"] = is_drop_eligible(
        existing.get("jurisdiction") or [],
        existing.get("process") or "",
    )


def load_optery(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    items = raw if isinstance(raw, list) else raw.get("brokers", raw.get("data", []))
    out: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        name = (
            item.get("name")
            or item.get("title")
            or item.get("brokerName")
            or item.get("company")
        )
        if not name:
            continue
        bid = item.get("id") or slugify(name)
        bid = re.sub(r"[^a-z0-9-]", "-", str(bid).lower()).strip("-")[:64]
        if bid in seen_ids:
            bid = bid + "-" + hashlib.sha1(name.encode()).hexdigest()[:6]
        seen_ids.add(bid)
        out.append(make_broker(bid, name, item, ["optery"]))
    return out


def load_eraser(path: Path, jurisdiction: str) -> tuple[list[dict[str, Any]], int]:
    if not path.is_file():
        return [], 0
    try:
        import yaml
    except ImportError:
        print("warn: PyYAML not installed; skip eraser merge", file=sys.stderr)
        return [], 0
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    added = 0
    out: list[dict[str, Any]] = []
    for item in data.get("brokers", []):
        if not isinstance(item, dict):
            continue
        email = item.get("email")
        if not email:
            continue
        bid = re.sub(r"[^a-z0-9-]", "-", str(item.get("id") or slugify(item.get("name", ""))).lower())
        bid = bid.strip("-")[:64]
        entry = {
            "email": email,
            "website": item.get("website"),
            "opt_out_url": item.get("opt_out_url"),
            "category": item.get("category"),
        }
        b = make_broker(
            bid, item.get("name", bid), entry, ["eraser"],
            process="email-opt-out", jurisdiction=jurisdiction,
        )
        out.append(b)
        added += 1
    return out, added


def load_symaira(brokers_dir: Path, jurisdiction_filter: str) -> tuple[list[dict[str, Any]], int]:
    if not brokers_dir.is_dir():
        return [], 0
    try:
        import yaml
    except ImportError:
        print("warn: PyYAML not installed; skip symaira merge", file=sys.stderr)
        return [], 0
    out: list[dict[str, Any]] = []
    count = 0
    for yaml_path in sorted(brokers_dir.rglob("*.yaml")):
        if yaml_path.name.startswith("_"):
            continue
        try:
            doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(doc, dict) or not doc.get("name"):
            continue
        bid = re.sub(r"[^a-z0-9-]", "-", str(doc.get("id") or slugify(doc["name"])).lower()).strip("-")[:64]
        jurs = doc.get("jurisdictions") or []
        if jurisdiction_filter == "US" and jurs and "US" not in jurs and "global" not in jurs:
            continue
        if jurisdiction_filter == "EU" and jurs and not any(j in jurs for j in ("EU", "UK", "global")):
            continue
        process, opt_url = infer_process_symaira(doc)
        entry = {
            "website": doc.get("website"),
            "opt_out_url": opt_url,
            "category": doc.get("category"),
            "jurisdictions": jurs,
        }
        b = make_broker(bid, doc["name"], entry, ["symaira"], process=process)
        out.append(b)
        count += 1
    return out, count


def merge_registry(
    optery_path: Path,
    eraser_path: Path | None,
    symaira_dir: Path | None,
    jurisdiction: str,
    *,
    merge_eraser: bool = True,
    merge_symaira: bool = True,
) -> dict[str, Any]:
    brokers_by_id: dict[str, dict[str, Any]] = {}
    stats = {"optery": 0, "eraser_new": 0, "symaira_new": 0}

    for b in load_optery(optery_path):
        merge_broker(brokers_by_id, b)
        stats["optery"] += 1

    if merge_eraser and eraser_path:
        eraser_brokers, _ = load_eraser(eraser_path, jurisdiction)
        before = len(brokers_by_id)
        for b in eraser_brokers:
            target_id = find_optery_merge_target(brokers_by_id, b)
            if target_id:
                payload = {**b, "id": target_id, "eraser_id": b["id"]}
                merge_broker(brokers_by_id, payload)
            else:
                merge_broker(brokers_by_id, b)
        stats["eraser_new"] = len(brokers_by_id) - before

    if merge_symaira and symaira_dir:
        symaira_brokers, parsed = load_symaira(symaira_dir, jurisdiction)
        before = len(brokers_by_id)
        for b in symaira_brokers:
            merge_broker(brokers_by_id, b)
        stats["symaira_new"] = len(brokers_by_id) - before
        stats["symaira_parsed"] = parsed

    brokers = list(brokers_by_id.values())
    sources = ["optery"]
    if merge_eraser:
        sources.append("eraser")
    if merge_symaira:
        sources.append("symaira")

    return {
        "generated_at": date.today().isoformat(),
        "jurisdiction_filter": jurisdiction,
        "sources": sources,
        "count": len(brokers),
        "merge_stats": stats,
        "brokers": brokers,
    }


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Merge opacite broker registries")
    p.add_argument("--optery", type=Path, required=True)
    p.add_argument("--eraser", type=Path, default=None)
    p.add_argument("--symaira-dir", type=Path, default=None)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--jurisdiction", default="US")
    p.add_argument("--no-eraser", action="store_true")
    p.add_argument("--no-symaira", action="store_true")
    args = p.parse_args()

    if not args.optery.is_file():
        print(f"error: optery registry missing: {args.optery}", file=sys.stderr)
        sys.exit(1)

    meta = merge_registry(
        args.optery,
        args.eraser,
        args.symaira_dir,
        args.jurisdiction,
        merge_eraser=not args.no_eraser,
        merge_symaira=not args.no_symaira,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    s = meta["merge_stats"]
    print(
        f"wrote {meta['count']} brokers → {args.out} "
        f"(optery={s.get('optery',0)} +eraser={s.get('eraser_new',0)} +symaira={s.get('symaira_new',0)})"
    )


if __name__ == "__main__":
    main()
