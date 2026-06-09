#!/usr/bin/env bash
# optout_runner.sh — campaign planner, SQLite state, lane dispatcher
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CASE=""
LANE=""
PLAN=0
CONFIRM=0
MAX=50
REGISTRY="$SKILL_ROOT/localonly/registry/unified-brokers.json"
HEALTH="$SKILL_ROOT/localonly/registry/registry_health.json"
SKIP_HEALTH_FILTER=0

usage() {
  cat <<'EOF'
Usage: optout_runner.sh [--case <slug>] [--lane email|web|drop|scan] [--plan] [--confirm] [--max N] [--status]

Default: --plan (no network side effects)

Lanes:
  email  → eraser adapter (SMTP; requires local eraser install + config)
  web    → symaira / auto-identity-remove adapter
  drop   → California DROP portal (operator-guided)
  scan   → exposure_scan.sh delegation

--confirm required for any outbound action. Without --confirm, plan only.
--status prints SQLite event summary for --case.
--skip-health-filter includes brokers with dead URLs (not recommended).

EOF
}

STATUS_ONLY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --case) CASE="$2"; shift 2 ;;
    --lane) LANE="$2"; shift 2 ;;
    --plan) PLAN=1; shift ;;
    --confirm) CONFIRM=1; shift ;;
    --status) STATUS_ONLY=1; shift ;;
    --max) MAX="$2"; shift 2 ;;
    --registry) REGISTRY="$2"; shift 2 ;;
    --health) HEALTH="$2"; shift 2 ;;
    --skip-health-filter) SKIP_HEALTH_FILTER=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ $STATUS_ONLY -eq 1 ]]; then
  [[ -n "$CASE" ]] || { echo "error: --case required with --status" >&2; exit 1; }
  python3 - "$CASE" "$SKILL_ROOT" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[2]) / "scripts"))
from opacite_lib import status_summary, state_db_path

slug = sys.argv[1]
if not state_db_path(slug).is_file():
    print(f"no state DB for case {slug}")
    sys.exit(0)
summary = status_summary(slug)
print(f"case={slug} status:")
for k, v in sorted(summary.items()):
    print(f"  {k}: {v}")
PY
  exit 0
fi

[[ $PLAN -eq 1 || -n "$LANE" ]] || PLAN=1

python3 - "$REGISTRY" "$HEALTH" "$LANE" "$PLAN" "$CONFIRM" "$MAX" "$CASE" "$SKILL_ROOT" "$SKIP_HEALTH_FILTER" <<'PY'
import json, os, subprocess, sys, uuid
from datetime import datetime, timezone
from pathlib import Path

registry, health_path, lane, plan, confirm, max_n, case, skill_root, skip_health = sys.argv[1:10]
plan = plan == "1"
confirm = confirm == "1"
max_n = int(max_n)
skip_health = skip_health == "1"
sys.path.insert(0, str(Path(skill_root) / "scripts"))
from opacite_lib import (
    append_planned_batch,
    health_status_by_broker,
    init_state_db,
    load_health_report,
    status_summary,
)

try:
    with open(registry, encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print("error: run registry_sync.sh first", file=sys.stderr)
    sys.exit(1)

brokers = data.get("brokers", [])
health_map = health_status_by_broker(load_health_report(health_path))
excluded_dead = []
excluded_blocked = []

def filter_lane(b):
    if lane == "email":
        return b.get("process") == "email-opt-out" or b.get("runner") == "eraser"
    if lane == "web":
        return b.get("process") in ("direct-form", "search-for-removal", "opt-out-search", "captcha-gated")
    if lane == "drop":
        return b.get("drop_eligible") or b.get("process") == "drop-centralized"
    if lane == "scan":
        return b.get("broker_class") == "people-search"
    return True

def health_ok(b):
    if skip_health or not health_map:
        return True
    st = health_map.get(b.get("id", ""))
    if st == "dead":
        excluded_dead.append(b.get("id"))
        return False
    if st == "blocked" and lane == "email":
        excluded_blocked.append(b.get("id"))
        return False
    return True

candidates = [b for b in brokers if filter_lane(b) and health_ok(b)]
selected = candidates[:max_n] if lane else candidates[:max_n]
campaign_id = str(uuid.uuid4())[:8]

campaign = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "campaign_id": campaign_id,
    "mode": "plan" if (plan and not confirm) else ("execute" if confirm else "plan"),
    "lane": lane or "all",
    "case": case or None,
    "confirm": confirm,
    "max": max_n,
    "batch_count": len(selected),
    "health_filter": not skip_health and bool(health_map),
    "excluded_dead_count": len(excluded_dead),
    "excluded_blocked_count": len(excluded_blocked),
    "brokers": [
        {
            "id": b["id"],
            "name": b.get("name"),
            "process": b.get("process"),
            "runner": b.get("runner"),
            "automation_tier": b.get("automation_tier"),
        }
        for b in selected
    ],
}

out_path = None
if case:
    out_dir = os.path.join(skill_root, "localonly", "cases", case, "exports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "campaign_plan.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(campaign, f, indent=2)
        f.write("\n")
    init_state_db(case)
    n = append_planned_batch(case, selected, lane or "all", campaign_id=campaign_id)
    campaign["state_events_written"] = n
    campaign["state_events_skipped"] = len(selected) - n
    campaign["status_after_plan"] = status_summary(case)

print(json.dumps(campaign, indent=2))
if out_path:
    print(f"\nwritten: {out_path}", file=sys.stderr)
    print(f"state: {os.path.join(skill_root, 'localonly', 'cases', case, 'state.sqlite')}", file=sys.stderr)
if excluded_dead:
    print(f"filtered {len(excluded_dead)} dead URL broker(s) via registry_health.json", file=sys.stderr)
if excluded_blocked:
    print(f"filtered {len(excluded_blocked)} blocked URL broker(s) for email lane", file=sys.stderr)

if confirm:
    if not case:
        print("error: --case required with --confirm", file=sys.stderr)
        sys.exit(1)
    if not lane:
        print("error: --lane required with --confirm", file=sys.stderr)
        sys.exit(1)
    if lane == "drop":
        drop_sh = os.path.join(skill_root, "scripts", "drop_lane.sh")
        cmd = [drop_sh, "--case", case, "--campaign-id", campaign_id]
        if confirm:
            cmd.append("--confirm")
        print(f"\nexecuting: {' '.join(cmd)}", file=sys.stderr)
        subprocess.run(cmd, check=True)
        if confirm:
            campaign["execute_status"] = status_summary(case)
            print(json.dumps({"campaign_id": campaign_id, "status": campaign["execute_status"]}, indent=2))
        sys.exit(0)
    if lane == "web":
        if not selected:
            print("error: no brokers selected for web lane", file=sys.stderr)
            sys.exit(1)
        ids = ",".join(b["id"] for b in selected)
        adapter = os.path.join(skill_root, "scripts", "symaira_adapter.py")
        cmd = [sys.executable, adapter, "--case", case, "--broker-ids", ids,
               "--campaign-id", campaign_id, "--lane", "web", "--per-broker"]
        if not confirm or os.environ.get("OPACITE_SYMAIRA_EXECUTE") != "1":
            cmd.append("--dry-run")
        else:
            cmd.append("--execute")
        print(f"\nexecuting: {' '.join(cmd)}", file=sys.stderr)
        subprocess.run(cmd, check=True)
        campaign["execute_status"] = status_summary(case)
        print(json.dumps({"campaign_id": campaign_id, "status": campaign["execute_status"]}, indent=2))
        sys.exit(0)
    if lane == "email":
        if not selected:
            print("error: no brokers selected for email lane", file=sys.stderr)
            sys.exit(1)
        if os.environ.get("OPACITE_SKIP_MANDATE") != "1":
            from opacite_lib import require_mandate
            require_mandate(case)
        ids = ",".join(b["id"] for b in selected)
        adapter = os.path.join(skill_root, "scripts", "eraser_adapter.py")
        cmd = [sys.executable, adapter, "--case", case, "--broker-ids", ids, "--campaign-id", campaign_id, "--lane", "email"]
        if os.environ.get("OPACITE_ERASER_DRY_RUN") == "1":
            cmd.append("--dry-run")
        print(f"\nexecuting: {' '.join(cmd)}", file=sys.stderr)
        subprocess.run(cmd, check=True)
        campaign["execute_status"] = status_summary(case)
        export_py = os.path.join(skill_root, "scripts", "manual_tasks_export.py")
        if os.path.isfile(export_py):
            subprocess.run(
                [sys.executable, export_py, "--case", case, "--json-only"],
                check=False,
                capture_output=True,
            )
            print(
                f"\nhint: manual queue → localonly/cases/{case}/exports/manual_tasks.md",
                file=sys.stderr,
            )
        print(json.dumps({"campaign_id": campaign_id, "status": campaign["execute_status"]}, indent=2))
        sys.exit(0)
    print("error: specify --lane email|web|drop", file=sys.stderr)
    sys.exit(1)

if not confirm:
    print("\nhint: pass --plan (default) or add --confirm to execute (human gate)", file=sys.stderr)
PY
