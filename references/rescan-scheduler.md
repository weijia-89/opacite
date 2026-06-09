# Rescan scheduler (Phase 5.3)

**Cadence (Incogni Q2 proxy):**

| Bucket | Interval | Baseline signal |
|--------|----------|-----------------|
| people-search | **60 days** | `exports/exposure_report.json` `generated_at`, else latest lane=`scan` event |
| private-db | **90 days** | Latest lane=`email` event (eraser batch proxy for private brokers) |

**Iron law:** `rescan_scheduler.sh` is a **planner only** — it never calls vanish, eraser, or the network. Operator runs suggested commands with existing `--confirm` / `OPACITE_*_EXECUTE` gates.

## Quick use

```bash
bash scripts/rescan_scheduler.sh --case me --dry-run
bash scripts/rescan_scheduler.sh --case me --dry-run --json
```

Output: `localonly/cases/<slug>/exports/rescan_schedule.json`

When a bucket is **OVERDUE**, suggested commands include:

- `exposure_scan.sh --case <slug> --dry-run` (or `--delta-only` after Wave 4 agent 3)
- `optout_runner.sh --case <slug> --lane scan --confirm`
- `optout_runner.sh --case <slug> --plan --lane email --max 50` (private-db bucket)

## macOS launchd (primary)

Save as `~/Library/LaunchAgents/com.opacite.rescan.<slug>.plist` (replace `<slug>`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.opacite.rescan.SLUG</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>ABSOLUTE_PATH_TO/opacite.skill/scripts/rescan_scheduler.sh</string>
    <string>--case</string>
    <string>SLUG</string>
    <string>--dry-run</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>ABSOLUTE_PATH_TO/opacite.skill/localonly/cases/SLUG/evidence/rescan-scheduler.log</string>
  <key>StandardErrorPath</key>
  <string>ABSOLUTE_PATH_TO/opacite.skill/localonly/cases/SLUG/evidence/rescan-scheduler.err.log</string>
</dict>
</plist>
```

Load (operator):

```bash
launchctl load ~/Library/LaunchAgents/com.opacite.rescan.SLUG.plist
launchctl start com.opacite.rescan.SLUG
```

Review `rescan_schedule.json` and run overdue suggested commands manually.

## cron fallback (Linux / macOS without launchd)

Weekly Sunday 09:00 local (adjust path and slug):

```cron
0 9 * * 0 cd /path/to/opacite.skill && bash scripts/rescan_scheduler.sh --case me --dry-run >> localonly/cases/me/evidence/rescan-scheduler.log 2>&1
```

## Limitations (honest)

- Scheduler does not enqueue rescans automatically — Phase 5 exit still requires operator approval for outbound lanes.
- `private-db` proxy uses email-lane timestamps until a dedicated private-broker scan artifact exists.
- `--delta-only` and verify wiring are Wave 4 agents 2–3; scheduler suggestions will gain `--verify` / delta flags when those land.

## Related

- `references/ROADMAP.md` §5.3
- `scripts/exposure_scan.sh`
- `localonly/daily/2026-06-12.md` Wave 4 manifest
