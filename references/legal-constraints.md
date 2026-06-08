# Legal constraints (not legal advice)

**Tag:** informational only · **Stakes:** L2 · Operator should consult counsel for mandate wording and jurisdiction.

opacite automates *submission* of rights requests; it does not guarantee broker compliance.

## United States — California

### Delete Act (SB 362) / DROP

- DROP (Delete Request and Opt-out Platform) available to consumers **January 1, 2026** [T1-verified, read:body, DROP-001].
- Registered data brokers must access DROP **at least every 45 days** beginning **August 1, 2026** [T1-verified, read:body, DROP-002].
- Single verifiable consumer request can reach **500+ registered brokers** [T1-verified, read:body, DROP-001].
- **opacite action:** `optout_runner.sh --lane drop` opens/guides DROP submission; store confirmation ID in campaign state.

### CCPA / CPRA

- Right to delete personal information collected from consumer, with exemptions (public records, certain transactions).
- **Authorized agent** requests require signed permission; Incogni model uses online authorization [T2-verified, read:body, INC-001].
- **opacite action:** generate mandate from `templates/authorized-agent-mandate.md` (milestone 2); operator signs; PDF in vault.

### Other states

- Vermont, Oregon, Texas maintain data broker registries [inferred:symaira-scanner, FOSS-003].
- No federal DROP equivalent yet — email/form lane still required for non-CA brokers.

## European Union / UK — GDPR / UK GDPR

- **Article 17** erasure right; brokers must respond within one month (extendable).
- **opacite action:** eraser `template: gdpr` or symaira `--law GDPR` campaigns.
- Cross-border: target brokers with EU establishment or EU data subjects; jurisdiction tagging in registry.

## Authorized-agent economics

Commercial services (Incogni, DeleteMe) collect mandate + identifiers once, amortize across bulk requests [T2-verified, read:body, INC-003]. DIY orchestration is legally similar if:

1. Mandate is accurate and signed.
2. Requests are verifiable (broker can confirm identity).
3. Operator does not impersonate another person.

**Risk:** automated wrong-person requests may violate broker ToS or state consumer protection norms — human match review mitigates.

## What opacite must NOT claim

- "Guaranteed removal" — brokers re-list [T2-verified, read:body, INC-003].
- "Legal advice" — templates are starting points only.
- "Background check clearing" — different regulatory regime.

## Data minimization in requests

Send only fields broker requires:

| Field | When to include |
|-------|-----------------|
| Full name | Always |
| City + state | People-search |
| Email | Reply channel |
| DOB | Only if broker requires (mark `sensitive: true`) |
| Government ID | **Never automate upload** — manual queue only |
| SSN | **Never** |

## Retention

- Campaign state: keep until operator deletes case.
- Signed mandate: keep while active + 1 year [speculative:conservative-retention].
- Broker reply emails: local IMAP archive; no cloud NLP unless operator opts in with local model.

## Falsifiers (legal strategy wrong if…)

- DROP does not cover a broker → email lane still needed [verified: DROP covers registered brokers only].
- Broker rejects unauthorized agent → operator must submit under own name [contested:broker-policy-variance].
- GDPR broker claims legitimate interest → erasure may be denied; escalation template required [inferred:GDPR-practice].
