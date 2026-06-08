#!/usr/bin/env bash
# registry_health.sh — full HEAD-check of opt-out/website URLs (default: all brokers)
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REGISTRY="$SKILL_ROOT/localonly/registry/unified-brokers.json"
OUT="$SKILL_ROOT/localonly/registry/registry_health.json"
MAX=0
TIMEOUT=8
WORKERS=12
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: registry_health.sh [--registry PATH] [--out PATH] [--max N] [--workers N] [--timeout SEC] [--dry-run]

Default: check ALL brokers in unified registry (parallel HEAD, no PII).
Use --max N only for quick samples.

Statuses: reachable | blocked (401/403/405) | dead | skipped | offline | dry_run

Environment:
  OPACITE_OFFLINE=1  Skip network; write offline report

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --registry) REGISTRY="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --max) MAX="$2"; shift 2 ;;
    --workers) WORKERS="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

[[ -f "$REGISTRY" ]] || { echo "error: registry not found: $REGISTRY" >&2; exit 1; }

python3 - "$REGISTRY" "$OUT" "$MAX" "$TIMEOUT" "$WORKERS" "$DRY_RUN" "${OPACITE_OFFLINE:-0}" <<'PY'
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

registry, out, max_n, timeout, workers, dry_run, offline = sys.argv[1:8]
max_n = int(max_n)
timeout = int(timeout)
workers = int(workers)
dry_run = dry_run == "1"
offline = offline == "1"

with open(registry, encoding="utf-8") as f:
    data = json.load(f)
brokers = data.get("brokers", [])
if max_n:
    brokers = brokers[:max_n]

def pick_url(b):
    return b.get("opt_out_url") or b.get("url")

def head_ok(url: str) -> tuple[str, int | None]:
    if not url or not str(url).startswith("http"):
        return "skipped", None
    try:
        r = subprocess.run(
            ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}",
             "--max-time", str(timeout), "-I", "-L", url],
            capture_output=True, text=True, timeout=timeout + 5,
        )
        code = int(r.stdout.strip() or "0")
        if 200 <= code < 400:
            return "reachable", code
        if code in (401, 403, 405):
            return "blocked", code
        return "dead", code
    except (subprocess.TimeoutExpired, ValueError, OSError):
        return "dead", None

results = []
counts = {"reachable": 0, "blocked": 0, "dead": 0, "skipped": 0, "offline": 0, "dry_run": 0}

if offline or dry_run:
    for b in brokers:
        status = "offline" if offline else "dry_run"
        counts[status] += 1
        results.append({
            "broker_id": b.get("id"),
            "name": b.get("name"),
            "url_checked": pick_url(b),
            "status": status,
            "http_code": None,
        })
else:
    def check_one(b):
        url = pick_url(b)
        status, code = head_ok(url)
        return {
            "broker_id": b.get("id"),
            "name": b.get("name"),
            "url_checked": url,
            "status": status,
            "http_code": code,
        }

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(check_one, b): b for b in brokers}
        done = 0
        total = len(brokers)
        for fut in as_completed(futs):
            row = fut.result()
            results.append(row)
            counts[row["status"]] = counts.get(row["status"], 0) + 1
            done += 1
            if done % 100 == 0 or done == total:
                print(f"progress: {done}/{total}", file=sys.stderr)

checked = counts.get("reachable", 0) + counts.get("blocked", 0) + counts.get("dead", 0)
report = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "registry_path": registry,
    "brokers_in_registry": len(data.get("brokers", [])),
    "brokers_checked": checked,
    "full_scan": max_n == 0,
    "workers": workers,
    "offline": offline,
    "dry_run": dry_run,
    "counts": counts,
    "dead_pct": round(100 * counts.get("dead", 0) / checked, 1) if checked else None,
    "blocked_pct": round(100 * counts.get("blocked", 0) / checked, 1) if checked else None,
    "results": sorted(results, key=lambda x: x.get("broker_id") or ""),
}

with open(out, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
    f.write("\n")

dead = counts.get("dead", 0)
blocked = counts.get("blocked", 0)
print(
    f"health: full_scan={report['full_scan']} checked={checked} "
    f"reachable={counts.get('reachable',0)} blocked={blocked} dead={dead} → {out}"
)
if checked and dead / checked > 0.1:
    print(f"warn: >10% dead URLs ({dead}/{checked}) — review registry_health.json before --confirm", file=sys.stderr)
if checked and blocked / checked > 0.2:
    print(f"warn: >20% blocked URLs ({blocked}/{checked}) — may need manual/browser lane", file=sys.stderr)
PY
