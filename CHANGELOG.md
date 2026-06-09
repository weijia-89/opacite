# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [SemVer](https://semver.org/).

## [0.4.0] - 2026-06-08

### Added

- Phase 2 email lane: `eraser_adapter.py` with dry-run and live send paths
- `require_mandate()` gate before email `--confirm` (`OPACITE_SKIP_MANDATE=1` for tests)
- `expand_profile_aliases()` for multi-email profiles in `opacite_lib.py`
- `manual_tasks_export.py` + `schemas/manual_task.schema.json`
- `keychain_smtp.sh` for macOS Keychain SMTP setup
- `references/email-lane-setup.md` operator guide
- Eraser broker ID resolution: Optery numeric ids vs eraser YAML slugs (`eraser_id`, email, name slug)
- `find_eraser()` discovers `ERASER_BIN`, `~/bin/eraser`, `/usr/local/bin/eraser`
- Registry merge: `find_optery_merge_target()` + `eraser_id` on Optery rows when eraser matches
- `tests/test_phase2.py` (14 tests with registry merge)
- Public docs: `ARCHITECTURE.md`, `SECURITY.md`, `LICENSE`
- CI workflow `.github/workflows/ci.yml`

### Changed

- Research archive consolidated under `localonly/archive/research/` (not shipped in public repo)
- `smoke_test.sh`: mandate gate uses temp empty vault when operator profile is filled
- README and architecture docs rewritten for public release

### Fixed

- `none of N broker id(s) found in eraser-brokers.yaml` when unified registry used Optery ids
- Mandate smoke test failure after operator filled `localonly/vault/profile.yaml`

## [0.3.0] - 2026-06-07

### Added

- Registry merge (`opacite_registry.py`), health checks, exposure scoring
- Campaign SQLite schema and `optout_runner.sh` plan path
- Vault init with age/openssl encryption
- Mandate manifest generation
- DROP lane recorder stub and CA DROP references

## [0.2.0] - 2026-06-06

### Added

- Initial skill scaffold, broker taxonomy, comparable FOSS research
- `SKILL.md` v0.4.0 contract surface

## [0.5.0] - 2026-06-10

### Added

- Phase 3 Wave 1: `symaira_adapter.py` per-broker `run-web-form` path (dry-run default)
- `vanish_adapter.py` — scan/verify only; opt-out and LLM memory check blocked with evidence
- `drop_dedup.py` — skip email-lane brokers already covered by CA DROP submission
- 25 operator playbooks under `references/playbooks/` + `references/playbook-index.md`
- `references/vanish-lane-setup.md`, `requirements-dev.txt`
- Tests: `test_symaira_adapter.py`, `test_vanish_adapter.py`, `test_drop_dedup.py` (31 total)
- Piranesi Phase 3 ChatPRD packet index (`references/piranesi-phase3-chatprd-packets.md`)

### Changed

- `latest_events()` partitions by `(broker_id, lane)` so web SUBMITTED does not block email PLANNED
- `optout_runner.sh` web lane always passes `--per-broker` to symaira
- `smoke_test.sh` prefers `.venv`, checks PyYAML, compiles all lane adapters
- Phase 3 Palamedes synthesis archived under `localonly/archive/research/pattern8-opacite-2026-06-10/`

### Fixed

- SY-01: removed unsafe symaira `--use-plan-execute` batch path
- SY-03: `require_mandate()` on symaira `--execute` unless `OPACITE_SKIP_MANDATE=1`
- VN-02: vanish blocked actions recorded before CLI discovery (no false “install vanish” on opt-out)

## [0.5.1] - 2026-06-10

### Added

- `optout_runner.sh --lane vanish` → `vanish_adapter.py` (scan dry-run default; live with `OPACITE_VANISH_EXECUTE=1`)
- Post-confirm `manual_tasks_export.py` hint on web and vanish lanes (matches email lane)

### Changed

- `vanish_adapter.py`: scan dry-run works without vanish CLI installed (CI / operator stub path)
- `references/ROADMAP.md`: Phase 3.1–3.3, 4.2 status; gantt reflects v0.5.x progress

### Fixed

- Vanish scan dry-run no longer requires `vanish` in PATH when only logging intent

## [Unreleased]

### Planned

- Phase 5–6: `exposure_scan.sh` live mode, rescan scheduler, coverage metrics

[0.5.1]: https://github.com/weijia-89/opacite/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/weijia-89/opacite/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/weijia-89/opacite/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/weijia-89/opacite/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/weijia-89/opacite/releases/tag/v0.2.0
