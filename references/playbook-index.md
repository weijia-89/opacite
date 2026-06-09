# Playbook index — people-search operators

Operator documentation for ROADMAP 3.3. These are **process guides**, not executable adapters.

Tier meanings (Pattern 8 synthesis, 2026-06-10):

| Tier | Meaning | Typical lane |
|------|---------|--------------|
| **A** | Email or simple form; eraser/symaira with operator confirm | email / web |
| **B** | Browser-assisted; CAPTCHA and/or email verification | web |
| **C** | IDV, phone-only walls, or manual queue | manual_tasks |

**Automation ceiling** is practical submittability, not verified removal. PeopleConnect brands marked `[self-service-only]` require the data subject to complete suppression.peopleconnect.us — do not count toward automated submission KPI.

Sources: `localonly/archive/research/pattern8-opacite-2026-06-10/palamedes-phase3-synthesis.md`, `references/broker-taxonomy.md`, `references/comparable-foss-repos.md`.

**Count:** 25 playbooks

| Broker | Playbook | Lane | Tier | Ceiling | Process | Flags |
|--------|----------|------|------|---------|---------|-------|
| whitepages | [playbooks/whitepages.md](playbooks/whitepages.md) | web | B | Medium | search-for-removal | — |
| beenverified | [playbooks/beenverified.md](playbooks/beenverified.md) | web | B | Medium | opt-out-search | — |
| truepeoplesearch | [playbooks/truepeoplesearch.md](playbooks/truepeoplesearch.md) | web | B | Medium | search-for-removal | — |
| fastpeoplesearch | [playbooks/fastpeoplesearch.md](playbooks/fastpeoplesearch.md) | web | B | Medium | direct-form | — |
| spokeo | [playbooks/spokeo.md](playbooks/spokeo.md) | web | B | Medium | search-for-removal | — |
| truthfinder | [playbooks/truthfinder.md](playbooks/truthfinder.md) | web | B | Low | control-profile | [self-service-only] |
| intelius | [playbooks/intelius.md](playbooks/intelius.md) | web | B | Low | control-profile | [self-service-only] |
| instantcheckmate | [playbooks/instantcheckmate.md](playbooks/instantcheckmate.md) | web | B | Low | control-profile | [self-service-only] |
| peoplefinders | [playbooks/peoplefinders.md](playbooks/peoplefinders.md) | web | A | High | direct-form | — |
| mylife | [playbooks/mylife.md](playbooks/mylife.md) | web | B | Medium | email-opt-out | — |
| radaris | [playbooks/radaris.md](playbooks/radaris.md) | web | B | Medium | direct-form | — |
| thatsthem | [playbooks/thatsthem.md](playbooks/thatsthem.md) | web | A | High | direct-form | — |
| nuwber | [playbooks/nuwber.md](playbooks/nuwber.md) | web | A | High | search-for-removal | — |
| usphonebook | [playbooks/usphonebook.md](playbooks/usphonebook.md) | web | A | High | direct-form | — |
| peekyou | [playbooks/peekyou.md](playbooks/peekyou.md) | web | B | Medium | direct-form | — |
| peoplelooker | [playbooks/peoplelooker.md](playbooks/peoplelooker.md) | web | B | Medium | direct-form | — |
| anywho | [playbooks/anywho.md](playbooks/anywho.md) | web | B | Low | control-profile | [self-service-only] |
| zabasearch | [playbooks/zabasearch.md](playbooks/zabasearch.md) | web | B | Low | control-profile | [self-service-only] |
| smartbackgroundchecks | [playbooks/smartbackgroundchecks.md](playbooks/smartbackgroundchecks.md) | web | A | High | direct-form | — |
| checkpeople | [playbooks/checkpeople.md](playbooks/checkpeople.md) | web | B | Medium | direct-form | — |
| searchpeoplefree | [playbooks/searchpeoplefree.md](playbooks/searchpeoplefree.md) | web | B | Medium | direct-form | — |
| cyberbackgroundchecks | [playbooks/cyberbackgroundchecks.md](playbooks/cyberbackgroundchecks.md) | web | A | High | direct-form | — |
| familytreenow | [playbooks/familytreenow.md](playbooks/familytreenow.md) | web | A | High | direct-form | — |
| lexisnexis | [playbooks/lexisnexis.md](playbooks/lexisnexis.md) | web | B | Medium | direct-form | restricted-records track = Tier C |
| pimeyes | [playbooks/pimeyes.md](playbooks/pimeyes.md) | web | C | Manual | id-verification | manual queue only |

## Tier distribution

- Tier **A**: 7
- Tier **B**: 17
- Tier **C**: 1

## Pattern 8 corrections applied

- Whitepages: C → **B** (email `privacyrequest@whitepages.com` + web form)
- Spokeo: A → **B** (reCAPTCHA + email verification)
- BeenVerified: CAPTCHA **yes** (stays B)
- MyLife: C → **B** (email/web; no confirmed DL requirement)
- LexisNexis: general data-sale opt-out **B**; restricted-records suppression **C**
- PeopleConnect family: **B** tier but `[self-service-only]` ceiling **Low**

## Iron laws (all playbooks)

- Never auto-upload government ID
- No cloud/telemetry in execution path
- Human confirm before outbound submission
