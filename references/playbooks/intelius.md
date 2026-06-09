# Intelius — operator playbook

**Broker class:** people-search  
**Lane:** web  
**Process type:** control-profile  
**Automation tier:** B  
**Automation ceiling:** Low  
**Rescan interval:** 60 days  

**Flags:** [self-service-only]

## Summary

PeopleConnect flagship brand; agent automation blocked for practical third-party submission.

## Opt-out entry points

| Channel | Location | Notes |
|---------|----------|-------|
| Primary | https://suppression.peopleconnect.us/ | Operator-verified entry point |
| Email | `support@mailer.intelius.com` | CCPA/GDPR or fallback path |
| CAPTCHA | No | Operator solves in browser; CapSolver not default |
| ID verification | No | Government ID upload is **manual-only** if ever requested |

## Required operator inputs

- Data subject identity fields per portal
- Email verification

## Manual steps

1. Tag broker `[self-service-only]` in registry.
2. Provide data subject a walkthrough link to suppression.peopleconnect.us.
3. Subject completes suppression for Intelius-family listings.
4. Optional parallel: subject emails support@mailer.intelius.com with CCPA delete request (separate track).
5. Operator logs completion from subject-provided screenshot only.

## Match verification

For search-for-removal flows, locate the subject's profile first. Use match scoring from `references/broker-taxonomy.md` (threshold_manual_review ≥50 before queueing; ≥70 only with operator override). Wrong-person removal is a legal and ethical failure — confirm city/state and age cues.


## Post-submit

1. Watch the vault inbox for confirmation or verification email; click links in a local browser only.
2. Save screenshot or PDF to `localonly/cases/<slug>/evidence/<broker_id>-<date>.png`.
3. Record `SUBMITTED` via `optout_runner.sh` or campaign SQLite; schedule rescan per broker class (60 days for people-search).


## Tier rationale

Tier **B**; ceiling **Low** / self-service. Pattern 8: do not count toward automated submission KPI.

## Iron laws

- Never auto-upload government ID or selfies on the operator's behalf.
- No cloud telemetry during playbook execution; evidence stays in `localonly/cases/<slug>/`.
- Human `--confirm` (or explicit operator approval) before any outbound submission.


## Sources

- Pattern 8 synthesis (`localonly/archive/research/pattern8-opacite-2026-06-10/palamedes-phase3-synthesis.md`)
- `references/broker-taxonomy.md`
