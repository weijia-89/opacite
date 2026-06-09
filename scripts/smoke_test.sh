#!/usr/bin/env bash
# smoke_test.sh — fast local verification (no network, no eraser send)
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SKILL_ROOT"

if [[ -x "$SKILL_ROOT/.venv/bin/python" ]]; then
  PYTHON="$SKILL_ROOT/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

if ! "$PYTHON" -c "import yaml" 2>/dev/null; then
  echo "error: PyYAML required — run: python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt" >&2
  exit 1
fi

echo "== syntax =="
for sh in scripts/*.sh; do
  bash -n "$sh"
  echo "  ok $sh"
done

echo "== python compile =="
"$PYTHON" -m py_compile scripts/opacite_lib.py scripts/opacite_registry.py \
  scripts/mandate_generate.py scripts/eraser_adapter.py \
  scripts/manual_tasks_export.py scripts/drop_dedup.py scripts/symaira_adapter.py \
  scripts/vanish_adapter.py scripts/exposure_scan.py

echo "== unit tests =="
"$PYTHON" -m unittest discover -s tests -p 'test_*.py' -v

echo "== registry merge (fixtures) =="
FIX="$SKILL_ROOT/tests/fixtures"
OUT="$(mktemp -t opacite-brokers.XXXXXX.json)"
"$PYTHON" scripts/opacite_registry.py \
  --optery "$FIX/optery-mini.json" \
  --eraser "$FIX/eraser-mini.yaml" \
  --no-symaira \
  --out "$OUT"
COUNT="$("$PYTHON" -c "import json; print(json.load(open('$OUT'))['count'])")"
[[ "$COUNT" -ge 2 ]] || { echo "fail: expected >=2 brokers"; exit 1; }
rm -f "$OUT"

echo "== plan idempotency (temp case) =="
CASE_ROOT="$(mktemp -d -t opacite-case.XXXXXX)"
export OPACITE_TEST_CASE_ROOT="$CASE_ROOT"
# Use existing registry if present; else mini merge output
REG="$SKILL_ROOT/localonly/registry/unified-brokers.json"
if [[ ! -f "$REG" ]]; then
  REG="$(mktemp -t opacite-reg.XXXXXX.json)"
  "$PYTHON" scripts/opacite_registry.py \
    --optery "$FIX/optery-mini.json" \
    --eraser "$FIX/eraser-mini.yaml" \
    --no-symaira \
    --out "$REG"
fi
mkdir -p "$SKILL_ROOT/localonly/cases/smoke-$$"
bash scripts/bootstrap_case.sh --slug "smoke-$$" --mkdir 2>/dev/null || mkdir -p "$SKILL_ROOT/localonly/cases/smoke-$$/exports"
"$PYTHON" - "$REG" "smoke-$$" "$SKILL_ROOT" <<'PY'
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[3]) / "scripts"))
from opacite_lib import append_planned_batch, init_state_db, status_summary

reg, slug, root = sys.argv[1:4]
with open(reg) as f:
    brokers = json.load(f).get("brokers", [])[:3]
init_state_db(slug)
n1 = append_planned_batch(slug, brokers, "email", campaign_id="s1")
n2 = append_planned_batch(slug, brokers, "email", campaign_id="s2")
assert n1 == len(brokers), (n1, len(brokers))
assert n2 == 0, n2
print(f"  plan idempotent: {n1} written, {n2} skipped on replay")
PY
rm -rf "$SKILL_ROOT/localonly/cases/smoke-$$"

echo "== mandate validation gate =="
EMPTY_VAULT="$(mktemp -d -t opacite-vault.XXXXXX)"
cp "$SKILL_ROOT/schemas/profile.template.yaml" "$EMPTY_VAULT/profile.yaml"
MANDATE_ERR="$("$PYTHON" scripts/mandate_generate.py --case smoke-mandate --vault "$EMPTY_VAULT" 2>&1)" || true
rm -rf "$EMPTY_VAULT"
if [[ "$MANDATE_ERR" == *legal_name* ]]; then
  echo "  ok empty profile rejected"
else
  echo "fail: mandate should reject empty profile: $MANDATE_ERR"
  exit 1
fi

echo "smoke_test: PASS"
