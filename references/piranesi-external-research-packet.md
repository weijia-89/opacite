# Piranesi export: opacite external deep research

**Paste into ChatPRD web or Opus 4.6.** No repo access. Return artifact to `palamedes` Pattern 8 ingest.

---

## Recommended ChatPRD Writing Template

Use default product-strategy template with "no local access" iron law reminder.

## Role

You are a senior privacy-product architect and consumer-protection researcher evaluating a **local-first DIY data-broker removal orchestrator** (`opacite`). The product bets on ~80% parity with Incogni for technical operators, without cloud-hosted PII. That percentage is a planning hypothesis, not a verified claim.

## Stable context

- **Incogni:** Surfshark-owned; 420+ automated broker opt-outs; scan + request + 60–90d rescan; authorization form; Unlimited tier adds human custom removals.
- **FOSS compose target:** eraser (750+ email), symaira-eraseme (1277 registry + Playwright), auto-identity-remove (500+ forms + CapSolver), vanish (58 guided opt-outs), Optery open JSON directory.
- **Legal lever:** California DROP (Delete Act). Consumer portal live Jan 2026; brokers must process from Aug 1, 2026; 45-day poll cycle.
- **Constraints:** PII encrypted on device; no third-party analytics; human approves before outbound requests; not legal advice.
- **Naming frame:** Glissant *right to opacity* (refusal of forced legibility to broker systems). Implementation is opt-out tooling, not literary theory.

## This session bet

**Bet:** A thin local orchestrator composing FOSS runners can deliver ~80% of Incogni Standard value for technical US/EU operators at near-zero subscription cost, if broker registry maintenance and authorized-agent compliance are solved.

**Kill criterion:** If >35% of top-100 people-search brokers require non-automatable ID verification with no email fallback, downgrade bet to ~60% and document.

## Line of work

`threat-privacy` + `product-bet` + `meta-workflow-design`

## In scope

1. Authorized-agent / mandate templates for US (CCPA/CPRA), EU (GDPR Art. 17), UK: **structure and required fields only** (not legal advice).
2. Broker registry maintenance economics: Optery vs symaira vs commercial lists; dead URL rate; community sustainability.
3. CAPTCHA / ID verification economics: when CapSolver is rational vs manual queue.
4. Competitive moat analysis: what Incogni/DeleteMe/Optery paid tiers still win on.
5. DROP integration playbook: residency, verification, expected broker compliance rate post-Aug 2026.
6. Threat model: local vault, SMTP credentials, wrong-person request, broker retaliation (rate limits).

## Out of scope

- Implementation code, git, CI
- Guaranteeing removal outcomes
- Employment screening / OSINT dossiers
- Cloud SaaS architecture proposals

## Evidence I have

### Incogni model (paraphrase from product pages, 2026)

- Scans people-search sites; proactive opt-outs to private brokers; periodic rescans; dashboard tracks request status not always removal.
- Requires name, email, address; optional extra aliases; online authorization signature.

### FOSS snapshot (paraphrase from GitHub READMEs, 2026)

**eraser:** `eraser send` bulk GDPR/CCPA emails; 750+ brokers YAML; manual follow-up for confirm links.

**symaira-eraseme:** 1277 brokers; `plan create`, `run-web-form`, inbox triage skills for LLM agents; weekly state registry scanner.

**auto-identity-remove:** Playwright monthly runner; CapSolver ~$0.001/solve; 90-day skip for completed brokers.

**vanish:** Evidence grades A/B/C; browser-assisted real opt-out URLs; verify command.

### DROP (paraphrase CA privacy.ca.gov, 2026)

- Single request to 500+ registered brokers; brokers access platform every 45 days from Aug 2026.

## Deliver this turn only

`Depth requirement: conduct an exhaustive search with no preset token/time cap; continue until marginal findings are low-yield, then report saturation criteria and residual unknowns.`

Produce:

1. **Executive decision card** (1 page) — GO / NO-GO on 80% bet with confidence.
2. **Authorized-agent field matrix** — jurisdiction × required fields × retention period × common broker rejections.
3. **Registry maintenance playbook** — recommend single SSOT, sync frequency, link-check strategy, contributor model.
4. **Automation ceiling table** — top 50 US people-search sites by traffic: process type, CAPTCHA?, ID?, email fallback?, estimated automation tier A/B/C.
5. **DROP section** — step-by-step consumer flow (as of 2026), limitations, interaction with DIY email campaigns (dedup strategy).
6. **Threat-privacy brief** — top 5 abuse cases for local-first removal tooling + mitigations.
7. **Residual unknowns** — explicit list with suggested empirical tests.

Use `[TBD]` for unverified counts. Tag claims `[verified]` only with cited URL.

## Placeholders rule

Do not invent broker compliance rates, Incogni internal metrics, or legal outcomes. Use ranges with rationale or `[TBD]`.

## Review pass (VP/CPO lens)

- Would you ship this to a privacy-conscious family member who is not technical?
- Where does human-in-loop destroy the value prop?
- What is the minimum viable paid feature if this were commercialized (hypothetical — product still FOSS/local)?

---

**Return path:** Save response to `~/Projects/opacite.skill/localonly/archive/research/external-opus-return.md` → invoke Palamedes Pattern 8 ingest.
