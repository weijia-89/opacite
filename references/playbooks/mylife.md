# MyLife — operator playbook

**Broker class:** people-search  
**Lane:** web  
**Process type:** email-opt-out  
**Automation tier:** B  
**Automation ceiling:** Medium  
**Rescan interval:** 60 days  


## Summary

Pattern 8 corrected Tier C→B; DL upload requirement not confirmed in current sources.

## Opt-out entry points

| Channel | Location | Notes |
|---------|----------|-------|
| Primary | https://www.mylife.com/privacyrequest | Operator-verified entry point |
| Email | `membersupport@mylife.com` | CCPA/GDPR or fallback path |
| Alt URL | https://www.mylife.com/help | Secondary entry |
| CAPTCHA | No | Operator solves in browser; CapSolver not default |
| ID verification | No | Government ID upload is **manual-only** if ever requested |

## Required operator inputs

- Legal name
- Email
- Profile URL if web form used
- Phone optional for 'complete' removal per some guides

## Manual steps

1. Prefer documented email path: membersupport@mylife.com with deletion request and identifying info.
2. Alternatively use privacyrequest web form.
3. Do **not** upload driver's license — if site prompts for ID, stop and queue manual_tasks (Tier C escalation).
4. Phone call may be recommended by third-party guides for completeness — operator choice.
5. Canary-test: verify profile visibility at 30 days (email-only completeness uncertain).

## Match verification

For search-for-removal flows, locate the subject's profile first. Use match scoring from `references/broker-taxonomy.md` (threshold_manual_review ≥50 before queueing; ≥70 only with operator override). Wrong-person removal is a legal and ethical failure — confirm city/state and age cues.


## Post-submit

1. Watch the vault inbox for confirmation or verification email; click links in a local browser only.
2. Save screenshot or PDF to `localonly/cases/<slug>/evidence/<broker_id>-<date>.png`.
3. Record `SUBMITTED` via `optout_runner.sh` or campaign SQLite; schedule rescan per broker class (60 days for people-search).


## Tier rationale

Tier **B** with caveat: email path existence ≠ verified removal completeness [speculative].

## Iron laws

- Never auto-upload government ID or selfies on the operator's behalf.
- No cloud telemetry during playbook execution; evidence stays in `localonly/cases/<slug>/`.
- Human `--confirm` (or explicit operator approval) before any outbound submission.


## Sources

- Pattern 8 synthesis (`localonly/archive/research/pattern8-opacite-2026-06-10/palamedes-phase3-synthesis.md`)
- `references/broker-taxonomy.md`
