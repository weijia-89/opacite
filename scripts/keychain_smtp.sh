#!/usr/bin/env bash
# keychain_smtp.sh — store/read eraser SMTP password from macOS Keychain (no plaintext in repo)
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE="${OPACITE_KEYCHAIN_SERVICE:-opacite-eraser-smtp}"
ACCOUNT="${OPACITE_KEYCHAIN_ACCOUNT:-eraser-smtp}"
ERASER_CONFIG="${ERASER_CONFIG:-$HOME/.eraser/config.yaml}"

usage() {
  cat <<EOF
Usage: keychain_smtp.sh --store | --install [--host HOST] [--port PORT] [--username USER] [--from ADDR]

macOS Keychain helpers for eraser SMTP (ROADMAP 2.5). Password never written under opacite.skill/.

  --store     Prompt for SMTP app password; save to Keychain service "$SERVICE"
  --install   Merge SMTP block into $ERASER_CONFIG from Keychain + flags
  --check     Verify Keychain entry exists (exit 1 if missing)

Environment:
  OPACITE_KEYCHAIN_SERVICE   Keychain service name (default: opacite-eraser-smtp)
  OPACITE_KEYCHAIN_ACCOUNT   Keychain account (default: eraser-smtp)
  ERASER_CONFIG              eraser config path (default: ~/.eraser/config.yaml)

See references/email-lane-setup.md for Gmail app-password setup.

EOF
}

STORE=0
INSTALL=0
CHECK=0
SMTP_HOST="${SMTP_HOST:-smtp.gmail.com}"
SMTP_PORT="${SMTP_PORT:-465}"
SMTP_USER=""
SMTP_FROM=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --store) STORE=1; shift ;;
    --install) INSTALL=1; shift ;;
    --check) CHECK=1; shift ;;
    --host) SMTP_HOST="$2"; shift 2 ;;
    --port) SMTP_PORT="$2"; shift 2 ;;
    --username) SMTP_USER="$2"; shift 2 ;;
    --from) SMTP_FROM="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "error: Keychain integration is macOS-only; set SMTP in $ERASER_CONFIG manually" >&2
  exit 1
fi

read_password() {
  security find-generic-password -s "$SERVICE" -a "$ACCOUNT" -w 2>/dev/null
}

if [[ $CHECK -eq 1 ]]; then
  if read_password >/dev/null; then
    echo "ok: Keychain entry $SERVICE / $ACCOUNT"
    exit 0
  fi
  echo "missing: Keychain entry $SERVICE / $ACCOUNT" >&2
  exit 1
fi

if [[ $STORE -eq 1 ]]; then
  echo "Enter SMTP app password (input hidden):"
  read -rs SMTP_PASS
  echo
  [[ -n "$SMTP_PASS" ]] || { echo "error: empty password" >&2; exit 1; }
  security delete-generic-password -s "$SERVICE" -a "$ACCOUNT" >/dev/null 2>&1 || true
  security add-generic-password -s "$SERVICE" -a "$ACCOUNT" -w "$SMTP_PASS" -U
  unset SMTP_PASS
  echo "stored: Keychain $SERVICE (account $ACCOUNT)"
  exit 0
fi

if [[ $INSTALL -eq 1 ]]; then
  PASS="$(read_password)" || {
    echo "error: no Keychain password — run: bash scripts/keychain_smtp.sh --store" >&2
    exit 1
  }
  [[ -n "$SMTP_USER" ]] || {
    echo "error: --username required (your Gmail address)" >&2
    exit 1
  }
  [[ -n "$SMTP_FROM" ]] || SMTP_FROM="$SMTP_USER"
  mkdir -p "$(dirname "$ERASER_CONFIG")"
  python3 - "$ERASER_CONFIG" "$SMTP_HOST" "$SMTP_PORT" "$SMTP_USER" "$SMTP_FROM" "$PASS" <<'PY'
import sys
from pathlib import Path

path, host, port, user, from_addr, password = sys.argv[1:7]
p = Path(path)
try:
    import yaml
except ImportError:
    raise SystemExit("error: pip install pyyaml")

data = {}
if p.is_file():
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

data.setdefault("email", {})
data["email"]["provider"] = "smtp"
data["email"]["from"] = from_addr
data["email"].setdefault("smtp", {})
data["email"]["smtp"].update({
    "host": host,
    "port": int(port),
    "username": user,
    "password": password,
    "use_tls": True,
})
data.setdefault("options", {})
data["options"].setdefault("template", "generic")

p.write_text(yaml.dump(data, sort_keys=False, default_flow_style=False), encoding="utf-8")
p.chmod(0o600)
print(f"wrote: {p} (mode 600, password from Keychain)")
PY
  unset PASS
  exit 0
fi

usage
exit 1
