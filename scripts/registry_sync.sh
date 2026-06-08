#!/usr/bin/env bash
# registry_sync.sh — merge Optery + eraser + symaira into unified registry (default: all merges)
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CACHE_DIR="$SKILL_ROOT/localonly/registry/cache"
OUT_FILE="$SKILL_ROOT/localonly/registry/unified-brokers.json"
JURISDICTION="US"
DRY_RUN=0
MERGE_ERASER=1
MERGE_SYMAIRA=1
OPTERY_URL="https://raw.githubusercontent.com/optery/optery-data-brokers-directory/master/data/data-brokers.json"
ERASER_URL="https://raw.githubusercontent.com/digisamroc/eraser/main/data/brokers.yaml"
SYMAIRA_TAR_URL="https://github.com/danieljustus/symaira-eraseme/archive/refs/heads/main.tar.gz"

usage() {
  cat <<'EOF'
Usage: registry_sync.sh [--jurisdiction US|EU|UK|multi] [--no-eraser] [--no-symaira] [--dry-run] [--out PATH]

Default: merges Optery + eraser email YAML + symaira broker registry tarball.
Does not send PII. Cache under localonly/registry/cache/.

Environment:
  OPACITE_OFFLINE=1  Skip network fetch; use cache only

Requires: python3, PyYAML (pip install pyyaml) for eraser/symaira merges

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --jurisdiction) JURISDICTION="$2"; shift 2 ;;
    --no-eraser) MERGE_ERASER=0; shift ;;
    --no-symaira) MERGE_SYMAIRA=0; shift ;;
    --merge)
      # legacy: --merge eraser (still on); --merge symaira
      case "${2:-}" in
        eraser) MERGE_ERASER=1; shift 2 ;;
        symaira) MERGE_SYMAIRA=1; shift 2 ;;
        *) echo "error: unknown --merge target" >&2; exit 1 ;;
      esac
      ;;
    --dry-run) DRY_RUN=1; shift ;;
    --out) OUT_FILE="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

mkdir -p "$CACHE_DIR"
mkdir -p "$(dirname "$OUT_FILE")"

OPTERY_CACHE="$CACHE_DIR/optery-data-brokers.json"
ERASER_CACHE="$CACHE_DIR/eraser-brokers.yaml"
SYMAIRA_TAR="$CACHE_DIR/symaira-main.tar.gz"
SYMAIRA_BROKERS="$CACHE_DIR/symaira/brokers"

fetch_optery() {
  if [[ "${OPACITE_OFFLINE:-0}" == "1" ]]; then
    [[ -f "$OPTERY_CACHE" ]] || {
      echo "error: OPACITE_OFFLINE=1 and no optery cache at $OPTERY_CACHE" >&2
      exit 1
    }
    echo "offline: using optery cache" >&2
    return 0
  fi
  curl -fsSL "$OPTERY_URL" -o "$OPTERY_CACHE.tmp" && mv "$OPTERY_CACHE.tmp" "$OPTERY_CACHE"
  echo "fetched: $OPTERY_CACHE"
}

fetch_eraser() {
  [[ $MERGE_ERASER -eq 1 ]] || return 0
  if [[ "${OPACITE_OFFLINE:-0}" == "1" ]]; then
    echo "offline: skip eraser fetch" >&2
    return 0
  fi
  curl -fsSL "$ERASER_URL" -o "$ERASER_CACHE.tmp" && mv "$ERASER_CACHE.tmp" "$ERASER_CACHE"
  echo "fetched: $ERASER_CACHE"
}

fetch_symaira() {
  [[ $MERGE_SYMAIRA -eq 1 ]] || return 0
  if [[ "${OPACITE_OFFLINE:-0}" == "1" ]]; then
    echo "offline: skip symaira fetch" >&2
    return 0
  fi
  if [[ -d "$SYMAIRA_BROKERS" ]] && [[ -n "$(find "$SYMAIRA_BROKERS" -name '*.yaml' 2>/dev/null | head -1)" ]]; then
  # refresh if tarball newer than 7 days — always fetch on explicit sync for now
    :
  fi
  curl -fsSL "$SYMAIRA_TAR_URL" -o "$SYMAIRA_TAR.tmp" && mv "$SYMAIRA_TAR.tmp" "$SYMAIRA_TAR"
  rm -rf "$CACHE_DIR/symaira-extract" "$CACHE_DIR/symaira"
  mkdir -p "$CACHE_DIR/symaira-extract"
  # Extract only registry/brokers (skip .cursor paths in archive)
  tar -xzf "$SYMAIRA_TAR" -C "$CACHE_DIR/symaira-extract" \
    --exclude='*/.cursor/*' \
    symaira-eraseme-main/registry/brokers 2>/dev/null \
    || tar -xzf "$SYMAIRA_TAR" -C "$CACHE_DIR/symaira-extract" symaira-eraseme-main/registry/brokers
  mkdir -p "$CACHE_DIR/symaira"
  mv "$CACHE_DIR/symaira-extract/symaira-eraseme-main/registry/brokers" "$CACHE_DIR/symaira/brokers"
  rm -rf "$CACHE_DIR/symaira-extract"
  echo "extracted symaira brokers → $SYMAIRA_BROKERS"
}

normalize() {
  local args=(python3 "$SKILL_ROOT/scripts/opacite_registry.py"
    --optery "$OPTERY_CACHE"
    --out "$OUT_FILE"
    --jurisdiction "$JURISDICTION")
  [[ $MERGE_ERASER -eq 1 && -f "$ERASER_CACHE" ]] && args+=(--eraser "$ERASER_CACHE")
  [[ $MERGE_SYMAIRA -eq 1 && -d "$SYMAIRA_BROKERS" ]] && args+=(--symaira-dir "$SYMAIRA_BROKERS")
  [[ $MERGE_ERASER -eq 0 ]] && args+=(--no-eraser)
  [[ $MERGE_SYMAIRA -eq 0 ]] && args+=(--no-symaira)
  "${args[@]}"
}

if [[ $DRY_RUN -eq 1 ]]; then
  echo "[dry-run] would fetch and write $OUT_FILE"
  [[ -f "$OPTERY_CACHE" ]] || { echo "no optery cache"; exit 1; }
  normalize
  exit 0
fi

fetch_optery
fetch_eraser
fetch_symaira
[[ -f "$OPTERY_CACHE" ]] || { echo "error: optery registry missing after fetch" >&2; exit 1; }
normalize
