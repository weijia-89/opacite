# Radaris — operator playbook

**Broker class:** people-search  
**Lane:** web  
**Process type:** direct-form  
**Automation tier:** B  
**Automation ceiling:** Medium  
**Rescan interval:** 60 days  


## Summary

Notorious re-listing and non-compliance risk despite automatable submission.

## Opt-out entry points

| Channel | Location | Notes |
|---------|----------|-------|
| Primary | https://radaris.com/control-privacy | Operator-verified entry point |
| Email | `customer-service@radaris.com` | CCPA/GDPR or fallback path |
| CAPTCHA | Yes | Operator solves in browser; CapSolver not default |
| ID verification | No | Government ID upload is **manual-only** if ever requested |

## Required operator inputs

- Profile URL
- Email
- OTP from email
- Age verification fields

## Manual steps

1. Locate Radaris profile; open control-privacy.
2. Complete multi-step form with CAPTCHA and email OTP.
3. Expect poor compliance — BBB C rating with many complaints (Pattern 8: stale F-rating).
4. Track exposure_status independently; do not trust broker ack alone.
5. Escalate with CCPA follow-up email if profile persists.

## Match verification

For search-for-removal flows, locate the subject's profile first. Use match scoring from `references/broker-taxonomy.md` (threshold_manual_review ≥50 before queueing; ≥70 only with operator override). Wrong-person removal is a legal and ethical failure — confirm city/state and age cues.


## Post-submit

1. Watch the vault inbox for confirmation or verification email; click links in a local browser only.
2. Save screenshot or PDF to `localonly/cases/<slug>/evidence/<broker_id>-<date>.png`.
3. Record `SUBMITTED` via `optout_runner.sh` or campaign SQLite; schedule rescan per broker class (60 days for people-search).


## Tier rationale

Tier **B** for submission; verified removal rate unknown — treat exposure scan as truth.

## Iron laws

- Never auto-upload government ID or selfies on the operator's behalf.
- No cloud telemetry during playbook execution; evidence stays in `localonly/cases/<slug>/`.
- Human `--confirm` (or explicit operator approval) before any outbound submission.


## Sources

- Pattern 8 synthesis (`localonly/archive/research/pattern8-opacite-2026-06-10/palamedes-phase3-synthesis.md`)
- `references/broker-taxonomy.md`
