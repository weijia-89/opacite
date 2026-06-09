#!/usr/bin/env bash
# exposure_scan.sh — read-only people-search discovery (no opt-outs)
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: exposure_scan.sh --case <slug> [--dry-run] [--no-dry-run] [--delta-only] [--registry PATH]

Plans read-only exposure checks against people-search brokers in unified registry.
Default --dry-run prevents live vanish execute.

Writes:
  localonly/cases/<slug>/exports/exposure_plan.json
  localonly/cases/<slug>/exports/exposure_report.json

SQLite (lane=scan): PLANNED on plan; APPROVED on dry-run; live execute delegates to
vanish_adapter.py when OPACITE_EXPOSURE_EXECUTE=1 (non-vanish → MANUAL_REQUIRED).

Requires profile in localonly/vault/profile.yaml (gitignored) for vanish live scan.

EOF
}

ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    *) ARGS+=("$1"); shift ;;
  esac
done

exec python3 "$SKILL_ROOT/scripts/exposure_scan.py" "${ARGS[@]}"
