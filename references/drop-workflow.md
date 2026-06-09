# California DROP workflow (operator checklist)

**Not legal advice.** Verified anchors: [`palamedes-synthesis-reviewed.md`](../localonly/archive/research/palamedes-synthesis-reviewed.md) Q8–Q11.

| Fact | Source |
|------|--------|
| DROP consumer portal live **Jan 1, 2026** | DROP-001 secondary |
| Brokers must process requests from **Aug 1, 2026** | DROP-001 |
| **545** registered data brokers (Jan 1, 2026) | DROP-001 |
| One deletion request applies to **all registered** brokers | DROP-001 |

**Portal:** [privacy.ca.gov/drop/](https://privacy.ca.gov/drop/)  
**About:** [About DROP and the Delete Act](https://privacy.ca.gov/drop/about-drop-and-the-delete-act/)  
**AG announcement:** [Attorney General DROP press release](https://oag.ca.gov/news/press-releases/california-data-protection-just-got-easier-attorney-general-bonta-reminds)

---

## Who should use DROP

California residents (verified via California Identity Gateway or Login.gov). Authorized agents may submit on behalf of a resident with proper documentation.

opacite does **not** auto-submit DROP. You complete the state portal yourself; opacite records the lane event for audit.

---

## Pre-flight

- [ ] Signed authorized-agent mandate in `localonly/cases/<slug>/mandate/` (if acting as agent)
- [ ] Vault profile matches identity you will verify in DROP
- [ ] Note today's date for SQLite evidence
- [ ] **Dedup:** If you already emailed the same brokers this week via eraser, DROP still covers registered brokers holistically — avoid duplicate *manual* follow-ups for the same broker without reviewing inbox

---

## Steps (human)

1. Open [https://privacy.ca.gov/drop/](https://privacy.ca.gov/drop/)
2. Complete California residency verification (Identity Gateway or Login.gov)
3. Submit **one** deletion request (applies to all registered data brokers)
4. Save confirmation screenshot or PDF to `localonly/cases/<slug>/evidence/drop-submission-<date>.pdf`
5. Run opacite recorder:

```bash
bash scripts/drop_lane.sh --case me --confirm --evidence localonly/cases/me/evidence/drop-submission-2026-06-09.pdf
```

6. Before **Aug 1, 2026:** status may remain pending; brokers are not yet required to process. After Aug 1, re-check DROP account status.

---

## opacite SQLite semantics

- Single aggregate event: `broker_id=california-drop-registry`, `lane=drop`, `event=SUBMITTED`
- Meta includes `registered_broker_count: 545` (Jan 2026 anchor) and evidence path
- Per-broker SUBMITTED rows for all 545 IDs are **not** written automatically; use `drop_dedup.py` to derive skip list from aggregate DROP + registry `drop_eligible`

---

## Email overlap dedup (Phase 4.2)

After DROP submission, **do not** email brokers already covered by the registry-wide DROP request. If you emailed some brokers before DROP, those overlap ids are redundant with DROP for `drop_eligible` brokers.

**Script (read-only SQLite + registry; no network):**

```bash
python3 scripts/drop_dedup.py --case me --dry-run
python3 scripts/drop_dedup.py --case me --dry-run --json
```

| Output field | Meaning |
|--------------|---------|
| `skip_brokers` | Broker ids to exclude from the next `optout_runner.sh --lane email` batch |
| `overlap` | `drop_eligible` ∩ email `SUBMITTED` (duplicate coverage) |
| `drop_lane_submitted` | True when any `lane=drop` event is `SUBMITTED` (aggregate or per-broker) |

**Skip rules:**

1. Always skip brokers with latest `lane=email` event `SUBMITTED`.
2. When DROP is `SUBMITTED`, also skip all registry brokers with `drop_eligible: true` (or `process: drop-centralized`).

Exit codes: `0` on success (including empty skip list); `1` when the case directory or registry file is missing.

Wire into planning: filter candidate email brokers against `skip_brokers` before `--confirm`.

---

## Non-registered brokers

DROP does not replace Phase 2–3 email/web lanes for brokers outside the CalPrivacy registry. Continue `optout_runner.sh --lane email|web` for those.
