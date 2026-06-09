# LexisNexis (consumer data sale) — operator playbook

**Broker class:** people-search  
**Lane:** web  
**Process type:** direct-form  
**Automation tier:** B  
**Automation ceiling:** Medium  
**Rescan interval:** 60 days  


## Summary

Two-track broker. Pattern 8: general opt-out is Tier B; restricted suppression is Tier C.

## Opt-out entry points

| Channel | Location | Notes |
|---------|----------|-------|
| Primary | https://optout.lexisnexis.com/ | Operator-verified entry point |
| Alt URL | https://consumer.risk.lexisnexis.com/ | Secondary entry |
| CAPTCHA | No | Operator solves in browser; CapSolver not default |
| ID verification | No (opt-out of sale); Yes for restricted-records suppression track | Government ID upload is **manual-only** if ever requested |

## Required operator inputs

- Name
- Address
- Email
- Date of birth as form requires

## Manual steps

1. Use optout.lexisnexis.com for **general consumer data-sale opt-out** (no police report).
2. Do **not** conflate with Information Suppression for restricted public records (separate Tier C track requiring documentation).
3. Never auto-upload police reports or government ID.
4. Submit; retain confirmation.
5. Restricted-records suppression: queue manual_tasks — counsel may be needed.



## Post-submit

1. Watch the vault inbox for confirmation or verification email; click links in a local browser only.
2. Save screenshot or PDF to `localonly/cases/<slug>/evidence/<broker_id>-<date>.png`.
3. Record `SUBMITTED` via `optout_runner.sh` or campaign SQLite; schedule rescan per broker class (60 days for people-search).


## Tier rationale

Tier **B** for data-sale opt-out; Tier **C** for restricted-records suppression program only.

## Iron laws

- Never auto-upload government ID or selfies on the operator's behalf.
- No cloud telemetry during playbook execution; evidence stays in `localonly/cases/<slug>/`.
- Human `--confirm` (or explicit operator approval) before any outbound submission.


## Sources

- Pattern 8 synthesis (`localonly/archive/research/pattern8-opacite-2026-06-10/palamedes-phase3-synthesis.md`)
- `references/broker-taxonomy.md`
