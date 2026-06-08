# Security policy

opacite is **local-first**: your profile, campaign state, and evidence logs stay on your machine. This document covers what the project does and does not protect.

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.4.x   | Yes       |
| < 0.4   | No        |

## Threat model (in scope)

| Asset | Protection |
|-------|------------|
| Profile PII | `localonly/vault/` (gitignored); encrypt with `vault_init.sh --encrypt` |
| SMTP credentials | macOS Keychain via `keychain_smtp.sh`, or `~/.eraser/config.yaml` (outside this repo) |
| Outbound opt-outs | Human `--confirm` gate; mandate required before email lane |
| Campaign audit trail | SQLite under `localonly/cases/<slug>/` (gitignored) |

## Out of scope

- Legal review of mandates or erasure letters (templates only; not legal advice)
- Broker compliance or removal guarantees
- Protection if you commit `localonly/`, `profile.yaml`, or `~/.eraser/config.yaml` to a public repo
- Cloud-hosted orchestration or third-party analytics (we do not ship these)

## What we do not collect

- No telemetry, crash reporting, or usage analytics in project scripts
- No default network calls except what **you** trigger (`registry_sync.sh`, eraser send, health scans)

## Reporting a vulnerability

Email security issues privately if you have a maintainer contact. If this repository has GitHub Security Advisories enabled, use **Report a vulnerability** on the Security tab.

Include:

1. Affected script or path
2. Steps to reproduce
3. Impact (e.g. PII leak, unintended send, secret in repo)
4. Your environment (macOS version, Python version) if relevant

Do **not** open a public issue for undisclosed credential leaks or PII exposure in operator configs.

## Operator hygiene (your responsibility)

1. Never commit `localonly/`, vault files, or case exports.
2. Use Gmail **app passwords** (or provider equivalent), not account passwords, in eraser SMTP config.
3. Run `bash scripts/smoke_test.sh` after pulling updates.
4. Review `campaign_plan.json` and dry-run logs before live `--confirm` sends.
5. Never auto-upload government ID; manual queue only.

## Dependency notes

opacite **composes** upstream tools ([eraser](https://github.com/digisamroc/eraser), [symaira](https://github.com/danieljustus/symaira-eraseme), etc.). Their security posture is separate. Registry data may include third-party opt-out URLs; `registry_health.sh` HEAD-checks reachability but does not audit page content.

## Disclosure timeline

We aim to acknowledge reports within 7 days and ship fixes for confirmed issues in project code on a best-effort basis. Upstream runner bugs should be reported to those projects directly.
