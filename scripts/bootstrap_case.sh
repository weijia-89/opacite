#!/usr/bin/env bash
# bootstrap_case.sh — create a local-only removal case directory (no PII in git)
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SLUG=""
MKDIR=0

usage() {
  cat <<'EOF'
Usage: bootstrap_case.sh --slug <name> [--mkdir]

Creates localonly/cases/<slug>/ with config skeleton and SQLite state path.
Never commits vault contents — see .gitignore.

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --slug) SLUG="$2"; shift 2 ;;
    --mkdir) MKDIR=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

[[ -n "$SLUG" ]] || { echo "error: --slug required" >&2; usage; exit 1; }
[[ "$SLUG" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "error: slug must be lowercase alphanumeric" >&2; exit 1; }

CASE_DIR="$SKILL_ROOT/localonly/cases/$SLUG"

if [[ $MKDIR -eq 1 ]]; then
  mkdir -p "$CASE_DIR"/{evidence,exports,manual_tasks,mandate}
  mkdir -p "$SKILL_ROOT/localonly/vault"
  mkdir -p "$SKILL_ROOT/localonly/registry/cache"

  if [[ ! -f "$CASE_DIR/config.example.yaml" ]]; then
    cat > "$CASE_DIR/config.example.yaml" <<'YAML'
# Copy to config.yaml and fill — config.yaml is gitignored
jurisdiction: US
state: CA
auto_submit: false
match_threshold_auto: 70
rescan_days: 90
lanes:
  - drop
  - email
  - web
profile_ref: ../../vault/profile.yaml  # encrypt: vault_init.sh --encrypt
mandate_dir: mandate/
YAML
  fi

  if [[ ! -f "$CASE_DIR/README.md" ]]; then
    cat > "$CASE_DIR/README.md" <<EOF
# Case: $SLUG

Local-only PII removal case. Do not commit.

1. Copy \`config.example.yaml\` → \`config.yaml\`
2. Create encrypted profile in \`localonly/vault/\`
3. Run \`vault_init.sh\` → fill profile → \`vault_init.sh --encrypt\`
4. Run \`mandate_generate.py --case $SLUG\` → print/sign PDF
5. Run \`registry_sync.sh\` then \`exposure_scan.sh --case $SLUG --dry-run\`
EOF
  fi

  python3 - "$SLUG" "$SKILL_ROOT" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[2]) / "scripts"))
from opacite_lib import init_state_db
db = init_state_db(sys.argv[1])
print(f"state DB: {db}")
PY

  echo "created: $CASE_DIR"
else
  echo "$CASE_DIR"
fi
