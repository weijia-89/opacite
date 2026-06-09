#!/usr/bin/env bash
# exposure_scan.sh — read-only people-search discovery (no opt-outs)
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: exposure_scan.sh --case <slug> [--dry-run] [--no-dry-run] [--delta-only] [--verify] [--max N] [--registry PATH]

Plans read-only exposure checks against people-search brokers in unified registry.
Default --dry-run prevents live vanish execute.

--verify  Sample vanish brokers → vanish_adapter --action verify (lane=scan).
          Dry-run is CI-safe without vanish installed. Live requires OPACITE_EXPOSURE_EXECUTE=1.

Writes:
  localonly/cases/<slug>/exports/exposure_plan.json (scan) or exposure_verify_plan.json (verify)
  localonly/cases/<slug>/exports/exposure_report.json

SQLite (lane=scan): PLANNED on plan; APPROVED on dry-run; live execute delegates to
vanish_adapter.py when OPACITE_EXPOSURE_EXECUTE=1 (non-vanish → MANUAL_REQUIRED).
Verify dry-run: APPROVED + exposure_status; live verify: VERIFIED_REMOVED | RE_LISTED.

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
