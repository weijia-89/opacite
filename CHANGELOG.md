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

## [Unreleased]

### Planned

- Phase 3: symaira web-form lane and manual queue UI
- Phase 5–6: rescan and coverage measurement

[0.4.0]: https://github.com/weijia-89/opacite/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/weijia-89/opacite/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/weijia-89/opacite/releases/tag/v0.2.0
