---
name: opacite
description: |
  Local-first orchestration for automated personal-data removal from data brokers and people-search sites without cloud telemetry. Composes FOSS runners (eraser, symaira-eraseme, vanish, auto-identity-remove) with encrypted on-device profile vault, exposure scan, opt-out campaign planner, inbox triage, and CA DROP integration. Human-in-loop before outbound requests. Triggers opacite, opacité, opacity, data broker removal, opt out of data brokers, remove my info from people search, PII removal, Incogni alternative, DeleteMe DIY, personal data erasure, DROP deletion request.
version: 0.5.3
type: project-skill
license: MIT
composes:
  - palamedes
  - trainer
  - form-check
  - superset
integrates_with:
  - engram
required_tools: [file_read, grep]
recommended_tools: [shell]
optional_tools: []
constraints:
  - local-first
  - no-cloud-telemetry
  - encrypted-profile-on-device
  - human-in-loop-before-submit
---

# opacite

**Local-first personal data removal orchestrator.** Reconstructs the Incogni loop — discover → authorize → request → verify → rescan — using composable FOSS tools and an on-device encrypted profile. **Not legal advice.** **Not employment screening.** **Not surveillance.**

> *Édouard Glissant, *Poétique de la relation* (1990): the **right to opacity** — persons need not be fully legible to systems that harvest and broker identity. This skill automates withdrawal of consent and visibility, not transparency into the operator. French *opacité* informs the slug; ASCII `opacite` is intentional for paths and invocation.*

## Invocation preamble

```
opacite v0.5.3 · jurisdiction={US|EU|UK|multi} · mode={plan|scan|campaign|triage|rescan|audit} · stakes=L2
```

## Iron laws

1. **PII never leaves the device unencrypted** — profile vault at `localonly/vault/` (gitignored); runners read via ephemeral env or stdin pipe.
2. **No third-party analytics** — no PostHog, no vendor dashboards, no "send us your data to opt you out."
3. **Human confirms before every outbound request** — automation prepares drafts; operator approves batch or per-broker (configurable `auto_submit: false` default).
4. **Authorized-agent compliance** — California/EU requests may require signed mandate; store signed PDF locally, never upload to cloud skill host.
5. **Compose, don't reinvent** — registry from Optery/symaira/state registries; execution via eraser (email), symaira/vanish/privotron (web), auto-identity-remove (Playwright bulk).
6. **Honest coverage ceiling** — ID verification, court records, and uncooperative brokers stay manual; measured automation ceiling is Phase 6 (see `localonly/archive/research/lane-gap-analysis.md`, `references/ROADMAP.md`).

## What Incogni does (target parity map)

| Incogni capability | opacite lane | Automation tier |
|------------------|------------------|-----------------|
| 420+ broker coverage | Registry sync + campaign planner | A — fully scriptable |
| Authorization / POA | Local mandate generator + signed PDF vault | B — human signs once |
| Public people-search scan | Exposure scan (name+geo queries) | A — scriptable |
| Private broker proactive opt-out | Email batch (eraser) + form runners | A/B — email A, forms B |
| Rescan every 60–90 days | Scheduler + state DB skip window | A |
| Dashboard / status | Local SQLite + HTML report | A |
| Custom removals (human experts) | Manual task queue + letter templates | C — operator |
| CAPTCHA / ID verification | CapSolver optional + manual queue | C — economics limit |
| Unlimited custom sites | vanish takedown letter drafts | B |

Tier key: **A** = unattended script · **B** = browser-assisted / one-click confirm · **C** = operator required.

## Modes

| Mode | When | Primary scripts |
|------|------|-----------------|
| `plan` | First run; jurisdiction unknown | Read `references/ARCHITECTURE.md`, run `registry_sync.sh --dry-run` |
| `scan` | Find where you appear | `exposure_scan.sh` |
| `campaign` | Execute opt-out wave | `optout_runner.sh --lane email\|web\|vanish\|scan\|drop` |
| `triage` | Process broker replies | symaira triage adapter or local IMAP + LLM (offline model only) |
| `rescan` | 60–90 day recurrence | `exposure_scan.sh` + delta opt-outs |
| `audit` | Coverage / gap report | `references/comparable-foss-repos.md`; archived lanes under `localonly/archive/research/` |

## Quick start (operator)

```bash
# 1. Bootstrap case (never commit vault)
bash ~/Projects/opacite.skill/scripts/bootstrap_case.sh --slug me --mkdir

# 2. Sync broker registry (Optery JSON + CA registry → local merge)
bash ~/Projects/opacite.skill/scripts/registry_sync.sh --jurisdiction US

# 3. Exposure scan (read-only plan; no opt-outs sent)
bash scripts/exposure_scan.sh --case me --dry-run
# Or via runner: optout_runner.sh --case me --lane scan --confirm

# 4. Plan campaign (prints batch plan; no sends)
bash scripts/optout_runner.sh --case me --plan --lane email --max 50

# 5. After operator review — execute one lane (live flags: OPACITE_*_EXECUTE=1)
bash scripts/optout_runner.sh --case me --lane email --confirm
```

## Specialist routing (trainer)

| Situation | Route to |
|-----------|----------|
| Multi-lane research fanout | `superset` + daily manifest `localonly/daily/<date>.md` |
| Threat model / mandate / GDPR framing | `form-check` + `references/legal-constraints.md` |
| Deep external product research | `piranesi` → full-context packet in `references/piranesi-<slug>-chatprd-packets.md` (see piranesi v0.2 iron law) |
| Evidence-grade synthesis | `palamedes` → `localonly/archive/research/palamedes-synthesis-reviewed.md` |
| GitHub/Codeberg FOSS inventory (18 repos) | `references/comparable-foss-repos.md` (source: archived lane research) |
| OSINT exposure discovery (non-removal) | `engram` (read-only; do not merge removal PII into dossiers) |

## File map

| Path | Purpose |
|------|---------|
| `references/ROADMAP.md` | Phased implementation plan (research → steady state) |
| `references/ARCHITECTURE.md` | System design, component graph |
| `references/broker-taxonomy.md` | Process types, broker classes |
| `references/legal-constraints.md` | DROP, CCPA, GDPR — constraints not counsel |
| `references/REFERENCES.md` | Palamedes source table |
| `references/piranesi-external-research-packet.md` | ChatPRD/Opus export (legacy — must meet piranesi v0.2 full-context gate) |
| `references/piranesi-*-chatprd-packets.md` | Full-context ChatPRD packets (canonical export path) |
| `localonly/archive/research/` | Archived Palamedes + lane synthesis (internal only) |
| `localonly/daily/` | Superset dispatch manifests |
| `scripts/` | registry_sync, registry_health, vault_init, mandate_generate, exposure_scan, exposure_scan.py, optout_runner, manual_tasks_export, eraser_adapter, symaira_adapter, vanish_adapter, drop_dedup, keychain_smtp, bootstrap_case, opacite_lib, opacite_registry |
| `schemas/campaign.sql` | SQLite campaign event schema |
| `schemas/broker.schema.json` | Unified broker entry schema |

## Piranesi export (iron law)

When routing to **piranesi** for ChatPRD/Opus:

1. **Full context only** — never outline packets in chat; never paraphrase-only `Evidence I have`.
2. **Read then embed** — verbatim iron laws, code, roadmap rows, audit findings, or Human prep attach list.
3. **Canonical path** — write complete packets to `references/piranesi-<slug>-chatprd-packets.md`; link from chat.
4. **Pre-send** — `piranesi.skill/references/checklist.md` Full Context Gate + Secure code fence.
5. **Repo exports** — four-backtick ` `````text ` fence; no nested triple-backticks; verify markdown preview.

## Kill criteria (do not scope-creep)

- Stop if operator wants **guaranteed** removal (brokers re-list; no service guarantees 100%).
- Stop if operator wants **fully unattended** ID-upload flows (high fraud risk; keep human-in-loop).
- Stop if project adds **cloud-hosted PII processing** — violates iron law #1.

## Version history

- **0.5.3** (2026-06-11): Phase 5 Wave 3 — exposure scan live path, `--lane scan --confirm`, `exposure_report.json`, lane=`scan` SQLite events.
- **0.5.2** (2026-06-10): SY-02 web/vanish lane split; trainer PR review helper.
- **0.5.1** (2026-06-10): vanish lane wired in optout_runner.
- **0.5.0** (2026-06-10): Phase 3 Wave 1 — symaira per-broker web lane, vanish scan adapter, DROP dedup, 25 operator playbooks.
- **0.4.0** (2026-06-09): Phase 2 complete — mandate gate, manual task export, Keychain SMTP, eraser SUBMITTED events.
- **0.3.0** (2026-06-08): Phase 1b symaira merge (default); full registry_health; Phase 2 vault + mandate generator.
- **0.2.0** (2026-06-08): Phase 1 — SQLite campaign state, registry_health, eraser merge, cruft cleanup.
- **0.1.0** (2026-06-07): Initial skill scaffold (formerly `privacyworm.skill`), research lanes, script stubs, Palamedes synthesis.
