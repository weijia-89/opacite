#!/usr/bin/env bash
# drop_lane.sh — operator-guided California DROP lane; records SUBMITTED in SQLite
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CASE=""
CONFIRM=0
EVIDENCE=""
CAMPAIGN_ID=""
DROP_URL="https://privacy.ca.gov/drop/"
REGISTERED_COUNT=545

usage() {
  cat <<EOF
Usage: drop_lane.sh --case <slug> [--confirm] [--evidence PATH] [--campaign-id ID]

Prints checklist (references/drop-workflow.md). With --confirm, writes SUBMITTED event
for aggregate broker_id california-drop-registry (lane=drop).

Without --confirm: plan-only reminder (no SQLite writes).

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --case) CASE="$2"; shift 2 ;;
    --confirm) CONFIRM=1; shift ;;
    --evidence) EVIDENCE="$2"; shift 2 ;;
    --campaign-id) CAMPAIGN_ID="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

[[ -n "$CASE" ]] || { echo "error: --case required" >&2; exit 1; }

CHECKLIST="$SKILL_ROOT/references/drop-workflow.md"
echo "=== California DROP (operator-guided) ==="
echo "Portal: $DROP_URL"
echo "Checklist: $CHECKLIST"
echo ""
echo "Steps:"
echo "  1. Verify CA residency in DROP"
echo "  2. Submit ONE deletion request (all registered brokers)"
echo "  3. Save confirmation to localonly/cases/$CASE/evidence/"
echo "  4. Re-run with --confirm --evidence <path>"
echo ""
echo "Registered brokers (Jan 2026 anchor): $REGISTERED_COUNT"
echo "Broker processing required from: 2026-08-01"
echo ""

if [[ $CONFIRM -eq 0 ]]; then
  echo "hint: add --confirm after you submit in the portal" >&2
  if command -v open >/dev/null 2>&1; then
    echo "opening: $DROP_URL" >&2
    open "$DROP_URL" || true
  fi
  exit 0
fi

python3 - "$CASE" "$EVIDENCE" "$CAMPAIGN_ID" "$REGISTERED_COUNT" "$SKILL_ROOT" <<'PY'
import json, sys
from pathlib import Path

case, evidence, campaign_id, count, root = sys.argv[1:6]
sys.path.insert(0, str(Path(root) / "scripts"))
from opacite_lib import append_event, init_state_db, status_summary

init_state_db(case)
meta = {
    "runner": "drop",
    "registered_broker_count": int(count),
    "portal": "https://privacy.ca.gov/drop/",
    "note": "aggregate DROP submission; not per-broker rows",
}
if campaign_id:
    meta["campaign_id"] = campaign_id

append_event(
    case,
    "california-drop-registry",
    "SUBMITTED",
    lane="drop",
    evidence_path=evidence or None,
    meta=meta,
)
print(json.dumps({
    "case": case,
    "broker_id": "california-drop-registry",
    "event": "SUBMITTED",
    "lane": "drop",
    "evidence": evidence or None,
    "status": status_summary(case),
}, indent=2))
PY
