# opacite

The name comes from Édouard Glissant’s *droit à l’opacité*: the **right to opacity**. A person need not be fully legible to systems that sort, score, and sell identity.

This project aims to give you back your right to be opaque, to not be reducible and sortable, and to remain a complex, multi-faceted human worthy of an intentional read.

FOSS runners sit behind an encrypted vault on your machine. You approve each outbound batch. A campaign state machine tracks what was planned, sent, and still needs your hand.

**Canonical skill:** [`SKILL.md`](SKILL.md) · **Roadmap:** [`references/ROADMAP.md`](references/ROADMAP.md) · **Architecture:** [`ARCHITECTURE.md`](ARCHITECTURE.md) · **Security:** [`SECURITY.md`](SECURITY.md) · **History:** [`CHANGELOG.md`](CHANGELOG.md)

---

## Status (2026-06-12)

| Phase | Scope | State |
|-------|--------|-------|
| 0–2 | Registry, vault, email lane, mandate, manual export | **Done** |
| 3 | Web + vanish lanes, 25 playbooks | **Done** — dry-run default; live via env execute flags |
| 4 | California DROP | **Doc + recorder + dedup** — operator submits portal |
| 5 | Rescan loop (scheduler, verify, delta scan) | **Done** — planner + dry-run paths; live outbound still needs `--confirm` + execute env |
| 6 | Metrics, audit UI | Planned |

Nothing sends without `--confirm`. Key env vars: `OPACITE_ERASER_DRY_RUN=1` (email dry-run), `OPACITE_EXPOSURE_EXECUTE=1` (live scan/verify), `OPACITE_EXPOSURE_VERIFY=1` (scan confirm → verify). Quarterly checklist: [`SKILL.md`](SKILL.md) §Quarterly operator ritual.

---

## Why 'opacite'

People-search sites list your address, your relatives, your old phone numbers, your old life, categorized and filtered and reduced down to data that prefigures you before you consent. Data brokers buy and resell that and then third-party for-profit services upload the same packet to the same brokers to negotiate removal on your behalf. You're in the middle of it, getting squeezed and being extracted from.

![Main risks of an under-regulated data brokers industry](https://policyreview.info/sites/default/files/assets/images/node-1670/1.png)

*Figure: Main risks of an under-regulated data brokers industry.* From [The untamed and discreet role of data brokers in surveillance capitalism: a transnational and interdisciplinary overview](https://policyreview.info/articles/analysis/untamed-and-discreet-role-data-brokers-surveillance-capitalism-transnational-and), *Internet Policy Review*.

Glissant’s essay [*For Opacity*](https://sites.evergreen.edu/politicalshakespeares/wp-content/uploads/sites/226/2015/12/Glissant-For-Opacity.pdf) gives language to the right of self-definition. **Opacity** is the claim that you do not owe anyone a complete, searchable version of yourself for someone else to make lazy, heuristic decisions based on non-representative data.

### Power, control, and the database (a plain version)

Poststructural thought treats power as something that often works through sorting, not only through obvious force. A state, comprised of institutions, controls its population by measuring it, classifying it, and directing the flows for health, risk, labor, and data. It's impersonal and massive and dehumanizing at its core and prone to abuse.

| What the broker wants | What opacity refuses |
|-----------------------|---------------------|
| Fields that line up (name, address, kin) | The mismatch, the nickname, the life that does not fit one row |
| Sortability (risk score, marketing segment) | The right to be ambiguous without being treated as fraud |
| Total legibility for buyers | Relationship without extraction |

Colonial and administrative history helped define Glissant’s frame. Colonial oppressors impose bureaucracy as a means of control. Colonial subjects are categorized, sorted, and assigned direction with policing as enforcement and imprisonment as punishment. This is the same frame at home as it is abroad.

---

## Theory (sources)

Glissant develops the idea in [*Poétique de la relation*](https://www.gallimard.fr/Catalogue/GALLIMARD/Blanche/Poetique-de-la-relation) (1990, Gallimard). Betsy Wing’s English [*Poetics of Relation*](https://press.umich.edu/Books/P/Poetics-of-Relation) (University of Michigan Press) is a good translation of it if you want a more transparent read.

> “Agree not merely to the right to difference but… to the right to opacity that is not enclosure within an impenetrable autarchy but subsistence within an irreducible singularity.”  
> — Glissant, [*For Opacity*](https://sites.evergreen.edu/politicalshakespeares/wp-content/uploads/sites/226/2015/12/Glissant-For-Opacity.pdf)

**Further reading:**
- [Library of Glissant Studies](https://glissantstudies.com/)
- [Toolshed — Glissant’s right to opacity](https://tool-shed.org/resource/edouard-glissants-right-to-opacity/)
- [Multitudes — *Opacité et transversalité*](https://www.multitudes.net/opacite-et-transversalite-lamitie-singuliere-de-felix-guattari-et-edouard-glissant/) (French)
- [CalPrivacy — DROP portal](https://privacy.ca.gov/drop/); [AG press release](https://oag.ca.gov/news/press-releases/california-data-protection-just-got-easier-attorney-general-bonta-reminds)

Verified broker-market claims (counts, cadence): [`references/ROADMAP.md`](references/ROADMAP.md) § North star. Not legal advice.

---

## Disambiguation

[`simonlpaige/privacyworm`](https://github.com/simonlpaige/privacyworm) is a separate FOSS playbook engine (same problem domain). **This tree is `opacite`**, an orchestration layer that composes privacyworm, eraser, symaira, and others.

---

## Quick start

```bash
git clone https://github.com/weijia-89/opacite.git && cd opacite
pip install pyyaml
bash scripts/bootstrap_case.sh --slug me --mkdir
bash scripts/vault_init.sh && $EDITOR localonly/vault/profile.yaml
bash scripts/vault_init.sh --encrypt
python3 scripts/mandate_generate.py --case me   # requires filled legal_name + emails
bash scripts/registry_sync.sh --jurisdiction US # optery + eraser + symaira
bash scripts/registry_health.sh                 # full parallel HEAD scan (~minutes)
bash scripts/optout_runner.sh --case me --plan --lane email --max 20
bash scripts/optout_runner.sh --case me --status
```

**Email lane (after [eraser](https://github.com/digisamroc/eraser) `init` + SMTP):**

```bash
OPACITE_ERASER_DRY_RUN=1 bash scripts/optout_runner.sh --case me --lane email --confirm --max 5
bash scripts/optout_runner.sh --case me --lane email --confirm --max 20
python3 scripts/manual_tasks_export.py --case me
```

**DROP (CA resident):** submit at [privacy.ca.gov/drop](https://privacy.ca.gov/drop/), then  
`bash scripts/drop_lane.sh --case me --confirm --evidence <screenshot.pdf>`

**Web lane (symaira, dry-run default):**  
`bash scripts/optout_runner.sh --case me --lane web --confirm --max 3`  
Live: `OPACITE_SYMAIRA_EXECUTE=1` (requires `symeraseme` in PATH).

**Vanish lane (scan/verify only; opt-out blocked):**  
`bash scripts/optout_runner.sh --case me --lane vanish --confirm --max 3`  
Setup: [`references/vanish-lane-setup.md`](references/vanish-lane-setup.md)

**Rescan cadence (planner only; no network):**  
`bash scripts/rescan_scheduler.sh --case me --dry-run` → `exports/rescan_schedule.json`

**Exposure scan lane (people-search discovery; no opt-outs):**  
`bash scripts/optout_runner.sh --case me --lane scan --confirm --max 10`  
Or: `bash scripts/exposure_scan.sh --case me --dry-run`  
Repeat rescans: `bash scripts/exposure_scan.sh --case me --dry-run --delta-only`  
Verify sample: `bash scripts/exposure_scan.sh --case me --verify --dry-run --max 5`  
Live vanish scan: `OPACITE_EXPOSURE_EXECUTE=1 bash scripts/exposure_scan.sh --case me --no-dry-run`  
Writes `exports/exposure_plan.json` and `exports/exposure_report.json`.

**DROP dedup (after CA submission):**  
`python3 scripts/drop_dedup.py --case me --dry-run`

**SMTP (macOS):** [`references/email-lane-setup.md`](references/email-lane-setup.md) + `scripts/keychain_smtp.sh`

**Verify:** `bash scripts/smoke_test.sh`

---

## Architecture

```
registry_sync.sh  →  unified-brokers.json
registry_health.sh → registry_health.json (reachable | blocked | dead)
optout_runner.sh --plan  →  campaign_plan.json + SQLite PLANNED events
optout_runner.sh --confirm --lane email|web|vanish|scan|drop  →  lane adapters / exposure_scan
exposure_scan.sh  →  exposure_plan.json + exposure_report.json (lane=scan events)
manual_tasks_export.py  →  exports/manual_tasks.{json,md}
```

Registry ingest: [Optery](https://github.com/optery/optery-data-brokers-directory) + [eraser](https://github.com/digisamroc/eraser) + [symaira](https://github.com/danieljustus/symaira-eraseme). PII under `localonly/vault/` and `localonly/cases/` (gitignored).

Full design (state machine, eraser ID resolution, lane map): [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## Privacy

- No cloud telemetry. No “upload your profile to opt you out.”
- Gitignored: vault, cases, `*.enc`, generated registry JSON, SQLite state DBs.
- ID verification and CAPTCHA-heavy brokers stay in a manual queue. Never auto-upload government ID.
- See [`SECURITY.md`](SECURITY.md).

---

## Development

| Command | Purpose |
|---------|---------|
| `bash scripts/smoke_test.sh` | Local CI parity |
| `python3 -m unittest discover -s tests` | Unit tests |
| `.github/workflows/ci.yml` | GitHub Actions |

See [`CHANGELOG.md`](CHANGELOG.md) for recent fixes.

---

## Comparable FOSS projects

Palamedes lane research is the evidence base: [`references/comparable-foss-repos.md`](references/comparable-foss-repos.md)

| Repo | What it does |
|------|----------------|
| [danieljustus/symaira-eraseme](https://github.com/danieljustus/symaira-eraseme) | 1,200+ broker registry, CLI campaigns, Playwright web forms |
| [simonlpaige/privacyworm](https://github.com/simonlpaige/privacyworm) | Local playbook engine, approval gate, no telemetry |
| [RAMBOXIE/vanish](https://github.com/RAMBOXIE/vanish) | Local scan/verify/report, browser-assisted opt-out |
| [digisamroc/eraser](https://github.com/digisamroc/eraser) | 750+ broker email sends |
| [puurpl/datapurge](https://github.com/puurpl/datapurge) | PWA mass-mail generator, 700+ broker YAML |
| [stephenlthorn/auto-identity-remove](https://github.com/stephenlthorn/auto-identity-remove) | Playwright monthly runner (CapSolver optional) |
| [yaelwrites/Big-Ass-Data-Broker-Opt-Out-List](https://github.com/yaelwrites/Big-Ass-Data-Broker-Opt-Out-List) | Human-maintained priority opt-out guide |

---

## Documentation index

| Path | Role |
|------|------|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | System design |
| [`SECURITY.md`](SECURITY.md) | Threat model and reporting |
| [`references/ROADMAP.md`](references/ROADMAP.md) | Phase plan and verified anchors |
| [`references/comparable-foss-repos.md`](references/comparable-foss-repos.md) | Curated FOSS exploration index |
| [`references/piranesi-external-research-packet.md`](references/piranesi-external-research-packet.md) | Opus/ChatPRD automation-ceiling packet |
| [`references/playbook-index.md`](references/playbook-index.md) | People-search operator playbooks (25 sites) |
| [`references/vanish-lane-setup.md`](references/vanish-lane-setup.md) | Vanish CLI install and scan lane |

Operator-local research (gitignored): `localonly/archive/research/`

---

## License

MIT (skill and scripts). Respect upstream licenses when merging registries (Optery: CC-BY-NC-SA). See [`LICENSE`](LICENSE).
