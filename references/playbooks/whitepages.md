# Whitepages — operator playbook

**Broker class:** people-search  
**Lane:** web  
**Process type:** search-for-removal  
**Automation tier:** B  
**Automation ceiling:** Medium  
**Rescan interval:** 60 days  


## Summary

High-traffic people-search site. Pattern 8 corrected Tier C→B: email and web-form fallbacks exist beyond phone verification.

## Opt-out entry points

| Channel | Location | Notes |
|---------|----------|-------|
| Primary | https://www.whitepages.com/suppression-requests | Operator-verified entry point |
| Email | `privacyrequest@whitepages.com` | CCPA/GDPR or fallback path |
| Alt URL | https://www.whitepages.com/privacy/consumer-rights | Secondary entry |
| CAPTCHA | No | Operator solves in browser; CapSolver not default |
| ID verification | No (phone on fast path only) | Government ID upload is **manual-only** if ever requested |

## Required operator inputs

- Profile URL from whitepages.com search
- Legal name
- Email for confirmation
- Optional: mailing address for postal path

## Manual steps

1. Search whitepages.com for the subject; copy the full profile URL.
2. Open suppression-requests (multi-step web form) OR email privacyrequest@whitepages.com with profile URL and deletion request.
3. If using the automated URL tool, phone verification may be offered — email/form paths avoid phone per consumer-rights page.
4. Complete any email confirmation link.
5. Re-scan in 60 days; Premium tier may retain data separately.

## Match verification

For search-for-removal flows, locate the subject's profile first. Use match scoring from `references/broker-taxonomy.md` (threshold_manual_review ≥50 before queueing; ≥70 only with operator override). Wrong-person removal is a legal and ethical failure — confirm city/state and age cues.


## Post-submit

1. Watch the vault inbox for confirmation or verification email; click links in a local browser only.
2. Save screenshot or PDF to `localonly/cases/<slug>/evidence/<broker_id>-<date>.png`.
3. Record `SUBMITTED` via `optout_runner.sh` or campaign SQLite; schedule rescan per broker class (60 days for people-search).


## Tier rationale

Tier **B** (web form + operator browser). Pattern 8 adversarial review: phone is primary on one path but not sole path; email completion rate unverified [needs_human_review].

## Iron laws

- Never auto-upload government ID or selfies on the operator's behalf.
- No cloud telemetry during playbook execution; evidence stays in `localonly/cases/<slug>/`.
- Human `--confirm` (or explicit operator approval) before any outbound submission.


## Sources

- Pattern 8 synthesis (`localonly/archive/research/pattern8-opacite-2026-06-10/palamedes-phase3-synthesis.md`)
- `references/broker-taxonomy.md`
