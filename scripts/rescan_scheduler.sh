#!/usr/bin/env bash
# rescan_scheduler.sh — 60d people-search / 90d private DB cadence (dry-run planner)
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: rescan_scheduler.sh --case <slug> [--dry-run] [--json]

Prints rescan due dates from local artifacts only (no network):
  - people-search (60d): last exposure_report.json or lane=scan activity
  - private-db (90d): last lane=email activity (eraser proxy)

Writes: localonly/cases/<slug>/exports/rescan_schedule.json

Does not execute scans — operator runs suggested commands with --confirm gates.
See references/rescan-scheduler.md for launchd/cron templates.

EOF
}

ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    *) ARGS+=("$1"); shift ;;
  esac
done

exec python3 "$SKILL_ROOT/scripts/rescan_scheduler.py" "${ARGS[@]}"
