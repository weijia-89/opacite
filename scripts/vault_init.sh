#!/usr/bin/env bash
# vault_init.sh — create profile template and encrypt at rest (age or openssl)
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VAULT_DIR="$SKILL_ROOT/localonly/vault"
TEMPLATE_SRC="$SKILL_ROOT/schemas/profile.template.yaml"
ENCRYPT=0
FORCE=0

usage() {
  cat <<'EOF'
Usage: vault_init.sh [--encrypt] [--force]

Copies schemas/profile.template.yaml → localonly/vault/profile.yaml (gitignored).
Fill PII locally, then:

  bash scripts/vault_init.sh --encrypt

Encryption:
  - prefers `age` (brew install age): age -p -o profile.enc profile.yaml
  - fallback: openssl aes-256-cbc -pbkdf2

After encrypt: remove or shred profile.yaml manually. profile.enc is gitignored.

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --encrypt) ENCRYPT=1; shift ;;
    --force) FORCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

mkdir -p "$VAULT_DIR"
PROFILE="$VAULT_DIR/profile.yaml"
ENC="$VAULT_DIR/profile.enc"

if [[ $ENCRYPT -eq 0 ]]; then
  [[ -f "$TEMPLATE_SRC" ]] || { echo "error: missing $TEMPLATE_SRC" >&2; exit 1; }
  if [[ -f "$PROFILE" && $FORCE -eq 0 ]]; then
    echo "profile exists: $PROFILE (use --force to overwrite from template)"
  else
    cp "$TEMPLATE_SRC" "$PROFILE"
    echo "created: $PROFILE from schemas/profile.template.yaml — fill before --encrypt"
  fi
  exit 0
fi

[[ -f "$PROFILE" ]] || { echo "error: $PROFILE missing — run without --encrypt first" >&2; exit 1; }

if command -v age >/dev/null 2>&1; then
  echo "encrypting with age (you will be prompted for passphrase)..."
  age -p -o "$ENC" "$PROFILE"
  echo "wrote: $ENC"
else
  echo "age not found; using openssl aes-256-cbc -pbkdf2"
  openssl enc -aes-256-cbc -pbkdf2 -salt -in "$PROFILE" -out "$ENC"
  echo "wrote: $ENC"
fi

echo ""
echo "NEXT: securely delete plaintext profile.yaml when satisfied:"
echo "  rm $PROFILE"
echo "  # or: shred -u $PROFILE  (linux)"
