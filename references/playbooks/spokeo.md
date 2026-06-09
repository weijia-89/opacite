# Spokeo — operator playbook

**Broker class:** people-search  
**Lane:** web  
**Process type:** search-for-removal  
**Automation tier:** B  
**Automation ceiling:** Medium  
**Rescan interval:** 60 days  


## Summary

Top-5 traffic site. Pattern 8 corrected Tier A→B: reCAPTCHA plus email verification required.

## Opt-out entry points

| Channel | Location | Notes |
|---------|----------|-------|
| Primary | https://www.spokeo.com/optout | Operator-verified entry point |
| Alt URL | https://help.spokeo.com/hc/en-us/articles/115002401187-How-do-I-opt-out- | Secondary entry |
| CAPTCHA | Yes | Operator solves in browser; CapSolver not default |
| ID verification | No | Government ID upload is **manual-only** if ever requested |

## Required operator inputs

- Spokeo profile URL
- Email for confirmation
- reCAPTCHA

## Manual steps

1. Search spokeo.com; open the subject profile; copy URL.
2. Paste URL at spokeo.com/optout.
3. Solve reCAPTCHA in operator browser.
4. Submit; complete confirmation email ('24–48 hours' processing stated on form).
5. Paid Spokeo accounts may retain data separately from free listing opt-out.

## Match verification

For search-for-removal flows, locate the subject's profile first. Use match scoring from `references/broker-taxonomy.md` (threshold_manual_review ≥50 before queueing; ≥70 only with operator override). Wrong-person removal is a legal and ethical failure — confirm city/state and age cues.


## Post-submit

1. Watch the vault inbox for confirmation or verification email; click links in a local browser only.
2. Save screenshot or PDF to `localonly/cases/<slug>/evidence/<broker_id>-<date>.png`.
3. Record `SUBMITTED` via `optout_runner.sh` or campaign SQLite; schedule rescan per broker class (60 days for people-search).


## Tier rationale

Tier **B**, not A. Fire-and-forget email automation will fail; plan for operator CAPTCHA + inbox confirm.

## Iron laws

- Never auto-upload government ID or selfies on the operator's behalf.
- No cloud telemetry during playbook execution; evidence stays in `localonly/cases/<slug>/`.
- Human `--confirm` (or explicit operator approval) before any outbound submission.


## Sources

- Pattern 8 synthesis (`localonly/archive/research/pattern8-opacite-2026-06-10/palamedes-phase3-synthesis.md`)
- `references/broker-taxonomy.md`
