# Vanish lane setup (scan + verify only)

**Goal:** Wrap [RAMBOXIE/vanish](https://github.com/RAMBOXIE/vanish) for exposure triage and post-opt-out verification. Phase 3 is **scan-only** — `opt-out` and `llm-memory-check` are blocked until the opacite consent gate ships (Palamedes synthesis, day-45).

## Prerequisites

- Node.js ≥ 20
- opacite profile in `localonly/vault/profile.yaml` (`legal_name`, `emails[0]` minimum)
- `pip install pyyaml` (or `requirements-dev.txt`)

## Install vanish

Pick one path:

```bash
# Zero-install probe (pulls package on first run — network required once)
npx --yes vanish scan --help

# Global install (recommended for repeat use)
npm install -g vanish

# From source
git clone https://github.com/RAMBOXIE/vanish
cd vanish && npm link
```

Override discovery:

```bash
export VANISH_BIN=/path/to/vanish
```

## Operator flow

### 1. Scan (default, local heuristic — Evidence C)

`vanish scan` scores all 210 brokers locally (no HTTP). Use for **prioritization**, not confirmed presence.

```bash
python3 scripts/vanish_adapter.py \
  --case me \
  --broker-ids spokeo,whitepages,beenverified \
  --json
```

- **Default:** dry-run — writes evidence log + `APPROVED` events in SQLite (no vanish subprocess for scan).
- **Live scan:** requires both `--execute` and `OPACITE_VANISH_EXECUTE=1`:

```bash
OPACITE_VANISH_EXECUTE=1 python3 scripts/vanish_adapter.py \
  --case me \
  --broker-ids spokeo,whitepages \
  --execute \
  --json
```

Evidence: `localonly/cases/<slug>/evidence/vanish-scan-*.log` and `vanish-scan-*.json` (execute mode).

### 2. Verify (post opt-out — Evidence A for broker HTTP liveness)

After a broker opt-out was recorded elsewhere (symaira / manual), verify removal:

```bash
python3 scripts/vanish_adapter.py \
  --case me \
  --broker-ids spokeo \
  --action verify \
  --json
```

Dry-run adds `--no-fetch` to vanish (no HTTP). Execute mode runs real liveness checks.

### 3. Opt-out — blocked in Phase 3

```bash
python3 scripts/vanish_adapter.py --case me --broker-ids spokeo --action opt-out
# → exit 1, MANUAL_REQUIRED events, consent-gate message
```

Browser-assisted `vanish opt-out` lands after Wave 2 (`optout-lane-wire`) + consent gate. Do not use `llm-memory-check` (sends PII to cloud LLM probes).

## Tier B seed sites (documentation URLs only)

From lane-gap analysis / Palamedes top-50 Tier B people-search (no PII in repo):

| Broker | Opt-out / privacy URL |
|--------|------------------------|
| Spokeo | https://www.spokeo.com/optout |
| Whitepages | https://www.whitepages.com/suppression-requests |
| BeenVerified | https://www.beenverified.com/app/optout/search |
| MyLife | https://www.mylife.com/ccpa/index.pubview |
| LexisNexis (consumer) | https://optout.lexisnexis.com |
| Radaris | https://radaris.com/control/privacy |
| Intelius | PeopleConnect suppression (self-service only — no third-party agent) |
| TruthFinder | PeopleConnect suppression (self-service only) |
| Instant Checkmate | PeopleConnect suppression (self-service only) |
| Classmates | PeopleConnect suppression (self-service only) |

Tag PeopleConnect brands `[self-service-only]` in registry; route to `manual_tasks_export`, not automated vanish opt-out.

## Evidence grades (honest KPI language)

| vanish command | Grade | opacite use |
|----------------|-------|-------------|
| `scan` | C (heuristic triage) | Discovery / prioritization only |
| `verify` | A (local HTTP liveness) | `exposure_status` independent of `request_status` |
| `opt-out` | B (browser-assisted) | **Blocked** until consent gate |
| `llm-memory-check` | D (cloud probe) | **Hard-blocked** in adapter |

## Security notes

- No cloud telemetry from opacite; vanish scan itself is offline.
- Verify execute mode may HTTP-check broker profile URLs — operator approves via `OPACITE_VANISH_EXECUTE=1`.
- Never commit vault profile or vanish queue state with PII.

## Related

- `scripts/vanish_adapter.py` — adapter entrypoint
- `references/comparable-foss-repos.md` — vanish fit tier
- `localonly/archive/research/pattern8-opacite-2026-06-10/palamedes-phase3-synthesis.md` — Phase 3 policy SSOT
