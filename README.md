# opacite

**Local-first data-broker removal orchestrator** — compose FOSS opt-out runners behind encrypted profile storage, a unified registry, and human approval gates.

Named after Glissant’s *opacité*: the right to opacity, not transparency on demand. Data brokers treat you as legible inventory. This project helps you push back on your machine, with evidence you can audit.

**Not legal advice.**

## What is opacite?

A **skill + shell scripts** that:

1. Merges broker registries (Optery, eraser, symaira) into one local list
2. Stores your profile encrypted on disk
3. Plans opt-out batches with exposure scoring
4. Runs **email** removals via [eraser](https://github.com/digisamroc/eraser) after you `--confirm`
5. Tracks campaign state in SQLite and exports manual tasks brokers can’t automate

No cloud. No telemetry. No “upload your profile and we’ll opt you out.”

## Status

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Registry merge, vault, campaign plan | Done |
| 2 | Email lane, mandate gate, manual export, eraser ID mapping | Done |
| 3 | Web-form lane (symaira), manual queue | Planned |
| 4 | CA DROP lane | Partial (docs + recorder) |
| 5–6 | Rescan, coverage metrics | Planned |

See [ROADMAP](references/ROADMAP.md) and [CHANGELOG](CHANGELOG.md).

## Theory (why this exists)

Paid removal services sell **legibility as a service**: you hand them your life story so they can negotiate your disappearance from other databases. That inverts the power relation — you become more visible to fix visibility elsewhere.

| Force | What brokers assume | What opacity claims |
|-------|---------------------|---------------------|
| Biopolitics | Body and address as administrable data | You choose what circulates |
| Colonial legibility | Names and kinship mapped for control | Right to remain unread |
| Platform extraction | Profile as product input | Local orchestration, no third-party vault |

Sources (not endorsements): Glissant *Poetics of Relation*; Scott *Seeing Like a State*; Foucault on biopolitics; Hardt & Negri *Multitudes* on immaterial labor and capture.

## Quick start

**Requirements:** macOS (Keychain SMTP helpers), Python 3.10+, `bash`, optional [Go](https://go.dev/) to build eraser.

```bash
git clone https://github.com/weijia-89/opacite.git
cd opacite

# 1. Vault + profile template
bash scripts/vault_init.sh
# Edit localonly/vault/profile.yaml (gitignored), then:
bash scripts/vault_init.sh --encrypt

# 2. Registry
bash scripts/registry_sync.sh --case me

# 3. Plan (no sends)
bash scripts/optout_runner.sh --case me --plan

# 4. Dry-run email lane
OPACITE_ERASER_DRY_RUN=1 bash scripts/optout_runner.sh --case me --lane email --confirm --max 5

# 5. Live send (after SMTP setup — see references/email-lane-setup.md)
bash scripts/optout_runner.sh --case me --lane email --confirm --max 5
```

Smoke test: `bash scripts/smoke_test.sh`

## Repository layout

| Path | Role |
|------|------|
| `SKILL.md` | Agent skill contract (v0.4.0) |
| `ARCHITECTURE.md` | System design |
| `SECURITY.md` | Threat model and reporting |
| `scripts/` | Orchestration entrypoints |
| `schemas/` | SQL + JSON schemas |
| `references/` | Taxonomy, roadmap, setup guides |
| `tests/` | Unit tests |
| `localonly/` | **Gitignored** — vault, cases, registry cache |

## Privacy

- Operator data lives under `localonly/` and is **not** committed.
- ID verification and CAPTCHA-heavy brokers go to the manual queue only.
- See [SECURITY.md](SECURITY.md).

## Development

| Command | Purpose |
|---------|---------|
| `bash scripts/smoke_test.sh` | Local CI parity |
| `python3 -m unittest discover -s tests` | Unit tests |
| `.github/workflows/ci.yml` | GitHub Actions |

## Comparable FOSS

Prior landscape scan: [references/comparable-foss-repos.md](references/comparable-foss-repos.md).

| Repo | Role |
|------|------|
| [symaira-eraseme](https://github.com/danieljustus/symaira-eraseme) | Large registry, Playwright forms |
| [privacyworm](https://github.com/simonlpaige/privacyworm) | Local playbook, approval gate |
| [vanish](https://github.com/RAMBOXIE/vanish) | Scan / verify / report |
| [eraser](https://github.com/digisamroc/eraser) | Email opt-outs (750+ brokers) |
| [datapurge](https://github.com/puurpl/datapurge) | PWA mass-mail generator |
| [Big-Ass-Data-Broker-Opt-Out-List](https://github.com/yaelwrites/Big-Ass-Data-Broker-Opt-Out-List) | Human-maintained priority list |

## License

MIT — see [LICENSE](LICENSE). Respect upstream licenses when merging registries (Optery: CC-BY-NC-SA).
