# AGENTS.md: opacite agent host contract

Load-bearing contract for AI coding agents (Cursor, Claude Code, etc.) on **opacite** — local-first personal-data removal orchestration. No `CLAUDE.md` twin yet; add parity when a second agent host requires it.

---

## Posture

- **Local-first.** No cloud telemetry, no third-party analytics, no CapSolver-by-default. Outbound broker contact requires explicit operator `--confirm` and lane execute env vars.
- **Human-in-loop.** Scripts plan and record; they do not auto-submit opt-outs or live scans without operator intent.
- **FOSS composition.** Runners (eraser, symaira, vanish) are adapters; opacite owns vault, state DB, and campaign planning.

## Stakes tier

| Surface | Tier | Review |
|---------|------|--------|
| `scripts/*_adapter.py`, `optout_runner.sh`, vault/keychain | **vibe-dangerous** | Trainer code review + tests |
| `scripts/exposure_scan.py`, `rescan_scheduler.py`, `opacite_lib.py` | **vibe-careful** | Trainer code review + smoke |
| `SKILL.md`, `README.md`, `CHANGELOG.md`, `references/ROADMAP.md` | **vibe-careful** | Trainer review when user-facing claims change |
| `tests/`, `schemas/` | **vibe-careful** | CI smoke + unittest |

## Verify commands (product repo)

```bash
cd ~/Projects/opacite.skill
bash scripts/smoke_test.sh
python3 -m unittest discover -s tests -v
```

## Trainer PR code-review gate (iron law)

Every PR that merges to `main` must have a **fresh trainer code review** on the PR **HEAD** in canonical format — same mechanical gate as **toebeans** and **buds**.

1. **Marker:** `<!-- trainer-codereview-opacite-{branch-with-slashes-as-dashes} -->`
2. **Meta:** `<!-- head={7-char-sha} verdict=APPROVE|REQUEST_CHANGES|BLOCK round={N} -->` matching current PR HEAD.
3. **Body:** `### Bug inventory` (every P0–P4 row or explicit none) + `### Trainer notes` with **Program notes**, **Your form**, **Next session** (never `### Pedagogy`).

**CI:** job `Trainer PR review comment gate` via `scripts/ci-trainer-pr-review-gate.sh`. Runs **in parallel** with smoke — smoke must not `needs:` the gate.

**Docs-only exempt:** PRs that change **only** `docs/**` or `research/**` `.md`/`.txt` skip the comment gate. `AGENTS.md`, `SKILL.md`, `scripts/`, `.github/`, and mixed code+docs PRs are **never** exempt.

**Post / PATCH:** `bash scripts/trainer_pr_review_post.sh <pr_num> <verdict> <round> review.md` from the PR branch. Prefer **post then push** so `head=` matches the first CI run.

**Routing:** trainer → form-check `code-review` per `~/Projects/trainer.skill/references/trainer-codereview.md` before claiming PR ready. Local artifact optional: `localonly/trainer-reviews/<branch-slug>-round<N>.md`.

Spec: `~/Projects/trainer.skill/references/trainer-codereview-gate.md`.
