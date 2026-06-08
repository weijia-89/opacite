#!/usr/bin/env bash
# exposure_scan.sh — read-only people-search discovery (no opt-outs)
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CASE=""
DRY_RUN=1
DELTA_ONLY=0
REGISTRY="$SKILL_ROOT/localonly/registry/unified-brokers.json"

usage() {
  cat <<'EOF'
Usage: exposure_scan.sh --case <slug> [--dry-run] [--delta-only]

Plans read-only exposure checks against people-search brokers in unified registry.
Default --dry-run prevents network I/O.

Writes: localonly/cases/<slug>/exports/exposure_plan.json

Requires profile in localonly/vault/profile.yaml (gitignored) for live scans.

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --case) CASE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --no-dry-run) DRY_RUN=0; shift ;;
    --delta-only) DELTA_ONLY=1; shift ;;
    --registry) REGISTRY="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

[[ -n "$CASE" ]] || { echo "error: --case required" >&2; usage; exit 1; }

CASE_DIR="$SKILL_ROOT/localonly/cases/$CASE"
OUT="$CASE_DIR/exports/exposure_plan.json"
mkdir -p "$CASE_DIR/exports"

python3 - "$REGISTRY" "$OUT" "$DRY_RUN" "$DELTA_ONLY" <<'PY'
import json, sys
from datetime import datetime, timezone

registry, out, dry_run, delta_only = sys.argv[1:5]
dry_run = dry_run != "0"
delta_only = delta_only != "0"

try:
    with open(registry, encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"error: registry not found: {registry}", file=sys.stderr)
    print("hint: run registry_sync.sh first", file=sys.stderr)
    sys.exit(1)

brokers = data.get("brokers", data if isinstance(data, list) else [])
scan_targets = [
    b for b in brokers
    if b.get("broker_class") == "people-search"
    or b.get("process") in ("search-for-removal", "opt-out-search")
]

plan = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "dry_run": dry_run,
    "delta_only": delta_only,
    "registry_count": len(brokers),
    "scan_target_count": len(scan_targets),
    "targets": [
        {
            "broker_id": b["id"],
            "name": b.get("name"),
            "url": b.get("url"),
            "opt_out_url": b.get("opt_out_url"),
            "process": b.get("process"),
            "action": "plan_scan" if dry_run else "execute_scan",
        }
        for b in scan_targets[:100]  # cap plan output; full run iterates all
    ],
    "note": "Live scan not implemented in v0.1 stub — integrate vanish scan or Playwright in M2",
}

with open(out, "w", encoding="utf-8") as f:
    json.dump(plan, f, indent=2)
    f.write("\n")

print(f"exposure plan: {len(scan_targets)} targets (showing {len(plan['targets'])}) → {out}")
if dry_run:
    print("dry-run: no HTTP requests made")
PY
