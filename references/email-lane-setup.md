# Email lane setup (eraser + Keychain)

**Goal:** Send broker opt-out emails via [eraser](https://github.com/digisamroc/eraser) without storing SMTP passwords in `opacite.skill/` or case directories.

## Prerequisites

- macOS (Keychain script) or manual `~/.eraser/config.yaml`
- `pip install pyyaml`
- eraser built and in `PATH` (`go build -o eraser ./cmd/eraser` from eraser repo)
- Gmail (or other SMTP) with **app password** if using Google 2FA

## One-time setup

### 1. eraser profile

```bash
eraser init
```

Fill legal name and contact fields from your vault profile. eraser config lives at `~/.eraser/config.yaml` (outside git).

### 2. Keychain SMTP (macOS)

```bash
# Create Google App Password: https://myaccount.google.com/apppasswords
bash scripts/keychain_smtp.sh --store
bash scripts/keychain_smtp.sh --install \
  --username you@gmail.com \
  --from you@gmail.com \
  --host smtp.gmail.com \
  --port 465
bash scripts/keychain_smtp.sh --check
```

`--install` writes SMTP settings into `~/.eraser/config.yaml` with mode `600`. The password is read from Keychain service `opacite-eraser-smtp` at install time only; it is not copied into the repo.

### 3. opacite mandate

```bash
bash scripts/vault_init.sh --encrypt   # after filling profile
python3 scripts/mandate_generate.py --case me
# Print authorized-agent.html → PDF → sign → localonly/cases/me/mandate/
```

## Dry-run then live

Mandate must exist before `--confirm` on the email lane (`mandate/manifest.json` from `mandate_generate.py`).

```bash
OPACITE_ERASER_DRY_RUN=1 bash scripts/optout_runner.sh --case me --lane email --confirm --max 5
bash scripts/optout_runner.sh --case me --lane email --confirm --max 20
python3 scripts/manual_tasks_export.py --case me
```

Evidence logs: `localonly/cases/<slug>/evidence/eraser-*.log`

## Security notes

- Never commit `~/.eraser/config.yaml` or `localonly/vault/profile.yaml`
- Rotate app passwords if config file was copied to an unsafe location
- eraser rate-limits sends; opacite `--max` caps batch size per run
