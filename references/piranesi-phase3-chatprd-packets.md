# Piranesi — Phase 3 ChatPRD packets (full context)

> **Iron law (piranesi v0.2.1):** Each packet below is a **single four-backtick** `text` fence. Copy everything **inside** the fence (not the backticks). No nested triple-backtick code fences — code excerpts use 4-space indent.

**Use:** Copy **one** packet block into ChatPRD or Opus.

**Return path:** `localonly/archive/research/external-opus-return-<topic>.md` → Palamedes Pattern 8 ingest.

---

## Packet 1 — FOSS compose decision (symaira · privacyworm · vanish)

````text
Recommended ChatPRD Writing Template: none
Reason: External research; opacite has no ChatPRD product template.

Role
You are a senior privacy-engineering architect advising opacite, a local-first DIY data-broker removal orchestrator. You have NO repo access, NO ability to run code, git, or verify builds. Work ONLY from evidence pasted below.

Stable context — opacite iron laws (verbatim)
1. PII never leaves the device unencrypted — profile vault at localonly/vault/ (gitignored); runners read via ephemeral env or stdin pipe.
2. No third-party analytics — no PostHog, no vendor dashboards, no "send us your data to opt you out."
3. Human confirms before every outbound request — automation prepares drafts; operator approves batch or per-broker (auto_submit: false default).
4. Authorized-agent compliance — signed mandate stored locally; never upload to cloud skill host.
5. Compose, don't reinvent — registry from Optery/symaira/state registries; execution via eraser (email), symaira/vanish/privotron (web).
6. Honest coverage ceiling — ID verification, court records, uncooperative brokers stay manual; measured ceiling is Phase 6.

Stable context — project status (2026-06-10)
- Phase 2 DONE: eraser email lane, mandate gate, manual_tasks_export, Keychain SMTP helper, public repo weijia-89/opacite.
- Phase 3 IN PROGRESS: symaira web stub, vanish adapter missing, privacyworm playbooks not ported.
- Operator decision: live email batch SKIPPED this wave.
- Campaign state machine: PLANNED → APPROVED → SUBMITTED → AWAITING_REPLY → VERIFIED_REMOVED | RE_LISTED | MANUAL_REQUIRED | FAILED.

Stable context — Phase 3 roadmap (verbatim)
| # | Work item | Acceptance |
| 3.1 | symaira adapter wrapper (plan execute with consent gate) | Web-form brokers run with operator grant |
| 3.2 | vanish integration for guided opt-out URLs (top 58) | Opens browser + evidence path in SQLite |
| 3.3 | Port/reference playbooks as opacite playbooks | ≥20 people-search sites with documented process |
| 3.4 | manual_tasks queue (MD + JSON): IDV, CAPTCHA, broken URL | Never stores ID images in repo |
| 3.5 | Inbox triage v1: IMAP classify confirm_link / removed_ack / need_more_info | Operator reviews; optional offline LLM only |
Kill gate: Do not enable CapSolver by default. Manual-first.
Exit: One end-to-end campaign across email + 10 web brokers with manual queue populated for failures.

Stable context — automation tiers (verbatim from broker-taxonomy)
| process | Automation ceiling |
| email-opt-out | High — eraser |
| direct-form | High — Playwright |
| search-for-removal | Medium — search + match score |
| control-profile | Low — account creation |
| phone-opt-out | Low |
| id-verification | Manual |
| captcha-gated | Medium with CapSolver; ToS risk |
| drop-centralized | High for CA residents |

This session bet
Bet: opacite should compose symaira (bulk registry + web/email execution), privacyworm (playbook schema + approval UX patterns), and vanish (browser-assisted opt-out + verify/report) WITHOUT merging their profile stores or SQLite event databases.

Line of work
product-bet + threat-privacy + meta-workflow-design

In scope
- Decision matrix: broker tier × lane × recommended runner × fallback × manual queue trigger
- Profile/vault bridging (single opacite vault → runner-specific export)
- Dual-SQLite risk (symaira event store vs opacite broker_events) and mitigations
- Consent mapping: symaira grant/consent token; privacyworm scan→review→optout --approved-only; vanish operator-in-browser
- Integration anti-patterns and refusal list (cloud LLM triage default, CapSolver default, vanish llm-memory-check)

Out of scope
- Implementation code, git, CI
- Guaranteed removal outcomes
- Employment screening / OSINT dossiers
- Cloud SaaS orchestration

Evidence I have — SOC audit findings (2026-06-10, local review)

### symaira-eraseme
- MIT; PyPI symeraseme 0.2.0; Python ≥3.11; pushed 2026-06-06; 1,277 broker YAML.
- CLI (upstream): init-profile; brokers list/show; plan create --campaign X --max N; plan execute --campaign X --batch-size N --dry-run|--yes --consent-file; run-web-form BROKER_ID --dry-run; grant; poll-inbox; classify-reply (optional triage extra → Anthropic).
- Profile: ~/.config/symeraseme/profile.json. Own SQLite event store.
- Optional: pip install symeraseme[triage] → anthropic for inbox classify.

### opacite scripts/symaira_adapter.py — load-bearing bug (verbatim)
    def run_symaira(...):
        plan = f"opacite-{campaign}"
        cmds.append([cli, "plan", "create", "--campaign", plan, "--max", str(len(broker_ids))])
        for bid in broker_ids:
            cmds.append([cli, "brokers", "show", bid])
        exec_cmd = [cli, "plan", "execute", "--campaign", plan,
                    "--batch-size", str(batch_size), "--delay", str(delay)]

Audit finding SY-01: plan create scans registry by --max count, NOT opacite's broker_ids list; brokers show loop does not constrain the plan.
Audit finding SY-02: plan execute has no --delay flag in upstream CLI [needs_human_review: verify against symeraseme 0.2.0 --help].
Per-broker path uses: symeraseme run-web-form BROKER_ID --dry-run (valid upstream command).

### privacyworm
- MIT; v1.0.0 Beta; pushed 2026-04-28; Python ≥3.11.
- Flow: privacyworm init → scan --headed → review (y/N per listing) → optout --approved-only → status → rescan.
- Profile: ~/.privacyworm/profile.yaml.enc (Fernet + Argon2id). No telemetry claim in README.
- Limitations (README verbatim): covers 10 of ~200 major US brokers; all 10 playbooks fixture_only/dry_run_only as of 2026-04-27; CAPTCHA pause; IDV handoff; CA residents should use DROP first.
- Playbooks: YAML data not code; PLAYBOOK_SPEC defines search url_template, listing_selectors, match_fields, opt-out blocks.

### vanish
- MIT; v0.3.0; Node ≥20; pushed 2026-04-28; npx github:RAMBOXIE/vanish.
- scan: 210 brokers, Evidence grade C (triage not confirmation).
- opt-out: 58 brokers browser-assisted, Evidence B (operator submits).
- verify + report: HMAC-signed local audit chain, Evidence A for HTTP liveness.
- Labs tier: llm-memory-check → OpenAI/Anthropic (Evidence D) — must NOT be opacite default.

### opacite integration status
- symaira: registry merge ✅; symaira_adapter stub ✅; consent bridge ❌; profile bridge ❌; tests ❌
- privacyworm: no adapter; playbook port ❌
- vanish: runner tag in schema ✅; vanish_adapter ❌; exposure_scan stub

Deliver this turn only
Depth requirement: exhaustive search until marginal findings are low-yield; report saturation criteria and residual unknowns.

Produce ONE artifact: FOSS Compose Decision Record with:
1. Executive recommendation (≤200 words)
2. Decision matrix: broker class × process type × runner × fallback × manual trigger
3. ≥8 integration anti-patterns
4. Consent & evidence model for opacite SQLite per runner
5. 90-day kill criteria per runner
6. Open questions [TBD] / [needs_human_review]

Placeholders rule
Do not invent CVEs, broker compliance rates, or site-specific mechanics without cited URL per row.

Review pass — add exactly 5 VP Product bullets after artifact.
````

---

## Packet 2 — Automation ceiling table (Phase 6)

````text
Recommended ChatPRD Writing Template: none

Role
Consumer-privacy researcher + automation engineer. NO repo access. NO code execution.

Stable context — opacite iron laws (verbatim)
1. PII never leaves the device unencrypted — profile vault at localonly/vault/ (gitignored); runners read via ephemeral env or stdin pipe.
2. No third-party analytics — no PostHog, no vendor dashboards, no "send us your data to opt you out."
3. Human confirms before every outbound request — automation prepares drafts; operator approves batch or per-broker (auto_submit: false default).
4. Authorized-agent compliance — signed mandate stored locally; never upload to cloud skill host.
5. Compose, don't reinvent — registry from Optery/symaira/state registries; execution via eraser (email), symaira/vanish/privotron (web).
6. Honest coverage ceiling — ID verification, court records, uncooperative brokers stay manual; measured ceiling is Phase 6.

Stable context — honest metrics policy (ROADMAP)
Do NOT use "brokers removed" as sole KPI — brokers count requests complete without confirming deletion. Track request_status and exposure_status separately. Primary outcome: exposure delta quarter-over-quarter.

Stable context — verified market anchors [paraphrase, 2026]
- Incogni: 420+ brokers marketed; 60d public / 90d private rescan cadence.
- Eraser: 764 email brokers in YAML (README says 750+).
- symaira: 1,279 YAML broker files.
- vanish: 210 scan / 58 browser-assisted opt-out (README).
- privacyworm: 10 playbooks, zero live-verified as of 2026-04-27.
- CA DROP: portal live Jan 2026; broker processing required from Aug 2026; ~545 registered brokers Jan 2026 [secondary: DataGrail; primary privacy.ca.gov may 403 — verify in body-read].

This session bet
If >35% of top-50 US people-search sites require Tier C (non-automatable IDV, no email fallback), downgrade opacite scope to email + DROP + guided forms only.

Line of work
threat-privacy + product-bet

In scope
- Top 50 US people-search sites by traffic proxy
- Per site: opt-out mechanism, CAPTCHA, IDV, email fallback, tier A/B/C
- Aggregate % A/B/C with methodology
- DROP dedup narrative vs DIY email campaigns
- Honest KPI recommendations

Out of scope
- Implementation, legal advice, cloud SaaS, employment screening

Evidence I have — tier definitions (verbatim)
Tier A = email/automatable (eraser)
Tier B = web form + operator browser (symaira, vanish opt-out)
Tier C = IDV/CAPTCHA/manual only (manual_tasks_export queue)

Evidence I have — FOSS automation limits
- Eraser README: many brokers need confirm links/forms/ID after email.
- symaira beta: web-form CAPTCHA requires manual setup.
- privacyworm: all 10 playbooks fixture_only/dry_run_only.
- vanish: scan is triage (C); b1-live mostly dry-run [needs_human_review: REAL_LOOP_STATUS.md on GitHub].

Human prep (optional attachments before send)
- Attach BADBOOL priority list excerpt if ChatPRD supports file upload: github.com/yaelwrites/Big-Ass-Data-Broker-Opt-Out-List
- Attach opacite comparable-foss-repos.md table if available offline

Deliver this turn only
Depth requirement: exhaustive search until low-yield; report saturation + unknowns.

Produce ONE artifact: Automation Ceiling Table (US Top 50) with methodology, 50-row table (Site | Traffic proxy | Opt-out type | CAPTCHA | IDV | Email fallback | Tier | Source URL), aggregate %, GO/NO-GO on Incogni-class coverage hypothesis, honest KPIs, residual unknowns.

Placeholders rule
One cited source URL per site row or mark [needs_human_review].

Review pass — 5 VP Product bullets.
````

---

## Packet 3 — Cloud/LLM integration refusal policy

````text
Recommended ChatPRD Writing Template: none

Role
Privacy threat-modeling lead for local-first PII removal. NO repo access.

Stable context — opacite iron laws (verbatim)
1. PII never leaves device unencrypted — profile vault at localonly/vault/ (gitignored).
2. No third-party analytics — no PostHog, no vendor dashboards.
3. Human confirms before every outbound request — auto_submit: false default.
4. Authorized-agent mandate stored locally only.
5. Compose FOSS runners; do not greenfield registry.
6. Honest coverage ceiling; manual queue for IDV.

Stable context — Phase 3.5 roadmap item
Inbox triage v1: IMAP classify confirm_link / removed_ack / need_more_info. Operator reviews. Optional offline LLM only.

This session bet
opacite can deliver symaira-class lifecycle (deadlines, manual tasks, inbox handling) WITHOUT cloud LLM in the default path.

Line of work
integration-no + threat-privacy + test-strategy

Evidence I have — symaira cloud touchpoints (upstream README + pyproject, 2026)
Optional extras:
  pip install symeraseme[triage]   # LLM triage via Anthropic Claude
  pip install symeraseme[openai]
Commands when triage enabled: poll-inbox, classify-reply, generate-rebuttal
.env.example documents ANTHROPIC_API_KEY

Evidence I have — vanish cloud touchpoints
Labs command llm-memory-check: probes OpenAI/Anthropic for memorization. Evidence grade D. Not a removal capability.

Evidence I have — privacyworm (no LLM in core deps)
Inbox: privacyworm inbox check — validates confirm-link domain against playbook allowlist before operator click. No LLM classification.

Evidence I have — opacite intent
symaira_adapter.py result JSON includes "cloud_llm_triage": False — documents intent, not runtime enforcement.

Hard refusal examples for opacite (seed list — extend in deliverable)
- Default Anthropic/OpenAI inbox classify on broker replies containing PII
- vanish llm-memory-check in smoke_test or default docs
- CapSolver or third-party CAPTCHA SaaS enabled by default
- Uploading profile vault to ChatPRD/Opus for "optimization"
- PostHog/analytics on opt-out funnels

Deliver this turn only
Produce ONE artifact: Cloud/LLM Integration Policy with:
1. Hard refusal list (≥10)
2. Opt-in allowlist (if any) with preconditions
3. Inbox triage v1 local-only design (states, transitions, operator review points)
4. Contributor PR checklist (≥12 gates)
5. Test strategy for proving no cloud calls in default path [needs_human_review: opacite CI not pasted — recommend network sandbox test]

Placeholders rule
Do not invent Anthropic retention policies without cited docs.

Review pass — 5 VP Product bullets.
````

---

## Checklist (pre-send)

- [ ] Pasted **one** packet only (copy **inside** the four-backtick fence)
- [ ] Markdown preview: entire prompt renders inside one code block (no leaked headings/tables)
- [ ] Did not ask ChatPRD to read ~/Projects/ or run git
- [ ] Return saved to localonly/archive/research/ for ingest
