# BeenVerified — operator playbook

**Broker class:** people-search  
**Lane:** web  
**Process type:** opt-out-search  
**Automation tier:** B  
**Automation ceiling:** Medium  
**Rescan interval:** 60 days  


## Summary

Background-check style people-search with search-then-remove UI and confirmed CAPTCHA.

## Opt-out entry points

| Channel | Location | Notes |
|---------|----------|-------|
| Primary | https://www.beenverified.com/app/optout/search | Operator-verified entry point |
| CAPTCHA | Yes | Operator solves in browser; CapSolver not default |
| ID verification | No | Government ID upload is **manual-only** if ever requested |

## Required operator inputs

- First and last name
- State
- Select matching record(s)
- Email for verification

## Manual steps

1. Open opt-out search; enter name and state.
2. Select the correct record(s) — verify city/relatives before continuing.
3. Solve CAPTCHA in operator browser (not CapSolver default).
4. Submit and complete email verification.
5. BeenVerified family sites (PeopleLooker, Peoplesmart) may share data — consider sibling playbooks.

## Match verification

For search-for-removal flows, locate the subject's profile first. Use match scoring from `references/broker-taxonomy.md` (threshold_manual_review ≥50 before queueing; ≥70 only with operator override). Wrong-person removal is a legal and ethical failure — confirm city/state and age cues.


## Post-submit

1. Watch the vault inbox for confirmation or verification email; click links in a local browser only.
2. Save screenshot or PDF to `localonly/cases/<slug>/evidence/<broker_id>-<date>.png`.
3. Record `SUBMITTED` via `optout_runner.sh` or campaign SQLite; schedule rescan per broker class (60 days for people-search).


## Tier rationale

Tier **B**. CAPTCHA present per 2025–2026 guides (Pattern 8 corrected 'No CAPTCHA' table entry).

## Iron laws

- Never auto-upload government ID or selfies on the operator's behalf.
- No cloud telemetry during playbook execution; evidence stays in `localonly/cases/<slug>/`.
- Human `--confirm` (or explicit operator approval) before any outbound submission.


## Sources

- Pattern 8 synthesis (`localonly/archive/research/pattern8-opacite-2026-06-10/palamedes-phase3-synthesis.md`)
- `references/broker-taxonomy.md`
