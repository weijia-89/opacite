# opacite

The name comes from Édouard Glissant’s *droit à l’opacité*: the **right to opacity**. A person need not be fully legible to systems that sort, score, and sell identity.

This project aims to give you back your right to be opaque, to not be reducible and sortable, and to remain a complex, multi-faceted human worthy of an intentional read.

FOSS runners sit behind an encrypted vault on your machine. You approve each outbound batch. A campaign state machine tracks what was planned, sent, and still needs your hand.

**Canonical skill:** [`SKILL.md`](SKILL.md) · **Roadmap:** [`references/ROADMAP.md`](references/ROADMAP.md) · **Architecture:** [`ARCHITECTURE.md`](ARCHITECTURE.md) · **Security:** [`SECURITY.md`](SECURITY.md) · **History:** [`CHANGELOG.md`](CHANGELOG.md)

---

## Status (2026-06-08)

| Phase | Scope | State |
|-------|--------|-------|
| 0–1 | Registry merge, health scan, campaign planner, SQLite state | **Done** — 2,854 brokers; health filter on `--plan` |
| 1b | symaira YAML merge | **Done** |
| 2 | Vault, mandate, email lane, manual export, eraser ID mapping | **Done** — `eraser_adapter.py`, `keychain_smtp.sh`, `manual_tasks_export.py` |
| 3 | Web lane (symaira) | **Stub** — `symaira_adapter.py` (dry-run default) |
| 4 | California DROP | **Doc + recorder** — `drop-workflow.md`, `drop_lane.sh` |
| 5–6 | Rescan, metrics | Not started |

Nothing sends without `--confirm`. Dry-run eraser: `OPACITE_ERASER_DRY_RUN=1` on `--confirm --lane email`.

---

## Why Glissant showed up here

I did not name this project after a French poet because I wanted a literary brand. I named it after an irritant I could not shake.

People-search sites list your address, your relatives, your old phone numbers, often before you have told a new neighbor where you live. Data brokers buy and resell that packet. Incogni-class services ask you to upload the same packet to *them* so they can negotiate removal on your behalf. The posture is always extraction first, then a fee for partial repair.

Glissant’s essay [*For Opacity*](https://sites.evergreen.edu/politicalshakespeares/wp-content/uploads/sites/226/2015/12/Glissant-For-Opacity.pdf) gave language for what felt wrong about that posture. Not secrecy. Not “nothing to hide.” **Opacity**: the claim that you do not owe anyone a complete, searchable version of yourself so their database can run cleanly.

### Power, control, and the database (a plain version)

Poststructural thought (Foucault is the usual entry point) treats power as something that often works through **sorting**, not only through obvious force. **Biopolitics** is the clunky term for it: govern a population by measuring it, classifying it, optimizing flows of health, risk, labor, and data. A broker does not need to dislike you. It needs you to be **readable**.

| What the broker wants | What opacity refuses |
|-----------------------|---------------------|
| Fields that line up (name, address, kin) | The mismatch, the nickname, the life that does not fit one row |
| Sortability (risk score, marketing segment) | The right to be ambiguous without being treated as fraud |
| Total legibility for buyers | Relationship without extraction |

Colonial and administrative history is part of why Glissant’s frame lands hard in the Caribbean: “understand you” too often meant “reduce you to my grid.” Opacity is a political refusal of that reduction, not a demand to disappear.

opacite is the tooling side of that refusal for one mundane front: **broker databases**. Opt-out letters, erasure requests, [California DROP](https://privacy.ca.gov/drop/) where it applies. Local vault. No telemetry. You confirm before anything leaves the machine. The scripts are unglamorous. The aim is to give you back room to be opaque to systems built to render you flat.

---

## Theory (sources)

Glissant develops the idea in [*Poétique de la relation*](https://www.gallimard.fr/Catalogue/GALLIMARD/Blanche/Poetique-de-la-relation) (1990, Gallimard). Betsy Wing’s English [*Poetics of Relation*](https://press.umich.edu/Books/P/Poetics-of-Relation) (University of Michigan Press) is the standard translation.

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

**SMTP (macOS):** [`references/email-lane-setup.md`](references/email-lane-setup.md) + `scripts/keychain_smtp.sh`

**Verify:** `bash scripts/smoke_test.sh`

---

## Architecture

```
registry_sync.sh  →  unified-brokers.json
registry_health.sh → registry_health.json (reachable | blocked | dead)
optout_runner.sh --plan  →  campaign_plan.json + SQLite PLANNED events
optout_runner.sh --confirm --lane email  →  eraser_adapter.py  →  SUBMITTED / FAILED + evidence log
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

Operator-local research (gitignored): `localonly/archive/research/`

---

## License

MIT (skill and scripts). Respect upstream licenses when merging registries (Optery: CC-BY-NC-SA). See [`LICENSE`](LICENSE).
