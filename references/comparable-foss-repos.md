# Comparable FOSS repos (data-broker / people-search opt-out)

**Method:** Palamedes lane research (2026-06-07) plus follow-up web discovery (2026-06-08). Full 18-repo inventory archived at `localonly/archive/research/lane-foss-repos-github-codeberg.md`. Tags: `[verified]` = checked this session or prior lane; `[inferred]` = README claim not independently counted.

**opacite stance:** compose and wrap. Do not greenfield another 1,200-broker registry. Prefer local-first, no telemetry, human-in-loop. See [`ROADMAP.md`](ROADMAP.md).

---

## Tier A — explore first (architecture-aligned)

| Repo | License | Last activity `[verified]` | Automation | Brokers `[tag]` | opacite fit |
|------|---------|---------------------------|------------|-----------------|-------------|
| [simonlpaige/privacyworm](https://github.com/simonlpaige/privacyworm) | MIT | 2026-04 | Playbook YAML + Playwright; approval gate; no telemetry | 10 people-search playbooks WIP `[README]` | **5** (reference playbook engine) |
| [danieljustus/symaira-eraseme](https://github.com/danieljustus/symaira-eraseme) | MIT | 2026-06 | CLI campaigns, SMTP, Playwright forms, deadline tracking | 1,279 YAML `[verified]` | **4** (registry + execution patterns) |
| [RAMBOXIE/vanish](https://github.com/RAMBOXIE/vanish) | MIT | 2026-04 | Browser-assisted opt-out, scan/verify, HMAC audit chain | 58 opt-out / 210 scan `[README]` | **4** (verify/report wrap) |
| [puurpl/datapurge](https://github.com/puurpl/datapurge) | MIT | 2026-03 | PWA; BCC mass mail via user client; deadline tracking | 727 YAML `[verified]` | **4** (template + registry ingest) |
| [warpapaya/wraith](https://github.com/warpapaya/wraith) | MIT | 2026-03 | Playwright CLI, SQLite, 90-day rescan | 13 automated `[README]` | **4** (rescan pattern) |
| [RhythrosaLabs/data-broker-optout](https://github.com/RhythrosaLabs/data-broker-optout) | MIT | 2026-03 | Selenium + Flask dashboard, 90-day reschedule | 20+ `[README]` | **4** (people-search handlers) |

---

## Tier B — useful adapters or data

| Repo | License | Notes | opacite use |
|------|---------|-------|-------------|
| [digisamroc/eraser](https://github.com/digisamroc/eraser) | MIT | Email batch + web UI; 764 YAML `[verified]` | **Email lane** (`eraser_adapter.py`) |
| [stephenlthorn/auto-identity-remove](https://github.com/stephenlthorn/auto-identity-remove) | MIT | Playwright monthly; CapSolver optional | Per-site adapter reference; external CAPTCHA |
| [kevinl95/Privotron](https://github.com/kevinl95/Privotron) | MIT | Playwright framework; community broker JSON | Config patterns for people-search |
| [optery/optery-data-brokers-directory](https://github.com/optery/optery-data-brokers-directory) | CC-BY-NC-SA | Directory only, not runner | Registry ingest (956+ in opacite merge) |
| [yaelwrites/Big-Ass-Data-Broker-Opt-Out-List](https://github.com/yaelwrites/Big-Ass-Data-Broker-Opt-Out-List) | CC | Human priority guide (BADBOOL) | Gap detection, playbook QA |
| [brianreumere/data-brokers](https://github.com/brianreumere/data-brokers) | BSD-2 | 60 YAML directory | Small merge test corpus |
| [Excalibra/GhostByte](https://github.com/Excalibra/GhostByte) | MIT | TUI tracker; opens URLs; manual only | UX reference for manual queue |
| [andbardii/open-broker-remover](https://github.com/andbardii/open-broker-remover) | MIT | Dockerized local requests; SQLite | EU-focused removal patterns |

---

## Tier C — adjacent or wrong problem

| Repo | Why listed | opacite fit |
|------|------------|-------------|
| [moderatedan/Databroker-Reporting-Tool](https://github.com/moderatedan/Databroker-Reporting-Tool) | Reports URLs to Google Safe Browsing (not opt-out) | **2** |
| [celenity/BadBlock](https://codeberg.org/celenity/BadBlock) | DNS blocklist for broker domains | **1** (block, not remove) |
| [rohare/sjm-uk-list-brokers](https://codeberg.org/rohare/sjm-uk-list-brokers) | UK broker markdown list | **2** (manual GDPR) |
| [zanedb/data-brokers](https://github.com/zanedb/data-brokers) | Abandoned stub | **1** |

---

## GitHub topic discovery

Browse ongoing repos: [github.com/topics/data-broker](https://github.com/topics/data-broker), [github.com/topics/opt-out](https://github.com/topics/opt-out), [github.com/topics/data-removal](https://github.com/topics/data-removal).

**Not found in public FOSS `[verified]`:** dedicated DROP API client; `openeraseme` as distinct repo (alias confusion with eraser/symaira).

---

## Suggested reading order

1. **Architecture:** privacyworm, then symaira, then vanish (local-first plus evidence).
2. **Registry bulk:** symaira, optery, eraser/datapurge YAML, BADBOOL.
3. **Automation depth:** data-broker-optout, Privotron, auto-identity-remove (site-specific).
4. **opacite integration:** [`CHANGELOG.md`](../CHANGELOG.md), [`ARCHITECTURE.md`](ARCHITECTURE.md).

Do not cite broker counts or success rates from this table without checking upstream or marking `[inferred]`.
