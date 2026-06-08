# Broker taxonomy and process types

Source fusion: brianreumere/data-brokers YAML schema [FOSS-007], symaira registry [FOSS-003], Optery directory fields [FOSS-006], privotron playbooks [FOSS-005].

## Broker classes

| Class | Description | Scan strategy | Opt-out strategy |
|-------|-------------|---------------|------------------|
| **people-search** | Public profile pages (Spokeo, Whitepages) | Name + city/state search | Profile URL removal |
| **marketing** | Ad-tech / consumer data aggregators | Cannot scan; proactive opt-out | Email CCPA/GDPR |
| **background-check** | Employment / tenant screening | Cannot scan | Email + form |
| **credit-bureau** | LexisNexis, Equifax (restricted) | Limited | Regulated forms |
| **B2B enrichment** | ZoomInfo, Clearbit | Email only | B2B opt-out forms |
| **people-finder EU** | GDPR jurisdiction brokers | Name search where legal | Art. 17 email |
| **state-registered** | CA/Vermont/TX registry listed | DROP (CA) or registry email | Centralized or direct |

## Process types (`process` field)

| `process` | Operator steps | Automation ceiling |
|-----------|----------------|-------------------|
| `email-opt-out` | Approve email batch | **High** — eraser |
| `direct-form` | Review pre-filled form | **High** — Playwright |
| `search-for-removal` | Confirm correct profile URL | **Medium** — search + match score |
| `opt-out-search` | Confirm match on special search UI | **Medium** |
| `control-profile` | Claim profile then delete | **Low** — account creation |
| `phone-opt-out` | Call or SMS verify | **Low** |
| `id-verification` | Upload ID / selfie | **Manual** |
| `captcha-gated` | Solve CAPTCHA | **Medium** with CapSolver; ToS risk |
| `drop-centralized` | One CA DROP request | **High** for CA residents [T1-verified, read:body, DROP-001] |

## Match scoring (exposure scan)

```yaml
match_score:
  name_exact: 40
  city_state_match: 25
  age_within_2yr: 15
  relative_name_overlap: 10
  phone_last4: 10
threshold_auto_queue: 70   # suggest opt-out
threshold_manual_review: 50
threshold_skip: 49
```

Wrong-person opt-out is a **legal and ethical failure mode** — default below Incogni's automation aggressiveness; require `threshold_auto_queue` only with operator config override.

## Registry merge precedence

1. **Optery JSON** — broadest metadata, opt-out URLs.
2. **symaira YAML** — jurisdiction tags, law templates (GDPR/CCPA).
3. **CA CPPA registry** — authoritative for DROP-eligible brokers.
4. **Local overrides** — `localonly/registry/overrides.yaml` for operator-discovered sites.

Conflict rule: prefer **newer `status.asOf`** from symaira; if tie, keep both `opt_out_url` candidates and flag `ambiguous: true`.

## Rescan policy

| Broker class | Re-check interval | Rationale |
|--------------|-------------------|-----------|
| people-search | 60 days | Fast re-listing [T2-verified, read:abstract, INC-002] |
| marketing email | 90 days | Slower re-acquisition |
| DROP-covered | 45 days | Statutory broker poll cycle [T1-verified, read:body, DROP-002] |
| manual-completed | 120 days | Operator effort amortization |
