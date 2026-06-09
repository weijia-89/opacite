# PimEyes — operator playbook

**Broker class:** people-search  
**Lane:** web  
**Process type:** id-verification  
**Automation tier:** C  
**Automation ceiling:** Manual  
**Rescan interval:** 60 days  


## Summary

Face-search broker requiring IDV; opacite documents only, does not automate.

## Opt-out entry points

| Channel | Location | Notes |
|---------|----------|-------|
| Primary | https://pimeyes.com/en/opt-out-request-form | Operator-verified entry point |
| CAPTCHA | No | Operator solves in browser; CapSolver not default |
| ID verification | Yes (government photo ID + selfie — manual only) | Government ID upload is **manual-only** if ever requested |

## Required operator inputs

- Face image
- Redacted government ID
- Selfie
- Phone

## Manual steps

1. **Tier C — manual queue only.**
2. Data subject completes opt-out in their own browser.
3. If government ID is requested, subject uploads directly — operator never stores ID in repo or automates upload.
4. Export task via manual_tasks_export.
5. Biometric opt-out has distinct legal sensitivity — document counsel if needed.



## Post-submit

1. Watch the vault inbox for confirmation or verification email; click links in a local browser only.
2. Save screenshot or PDF to `localonly/cases/<slug>/evidence/<broker_id>-<date>.png`.
3. Record `SUBMITTED` via `optout_runner.sh` or campaign SQLite; schedule rescan per broker class (60 days for people-search).


## Tier rationale

Tier **C**. Iron law: never document or implement auto-upload of government ID.

## Iron laws

- Never auto-upload government ID or selfies on the operator's behalf.
- No cloud telemetry during playbook execution; evidence stays in `localonly/cases/<slug>/`.
- Human `--confirm` (or explicit operator approval) before any outbound submission.


## Sources

- Pattern 8 synthesis (`localonly/archive/research/pattern8-opacite-2026-06-10/palamedes-phase3-synthesis.md`)
- `references/broker-taxonomy.md`
