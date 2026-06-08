#!/usr/bin/env python3
"""Generate authorized-agent mandate (HTML + Markdown) for data broker opt-outs."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

SKILL_ROOT = Path(__file__).resolve().parent.parent


def load_profile(vault_dir: Path) -> dict:
    plain = vault_dir / "profile.yaml"
    enc = vault_dir / "profile.enc"
    if plain.is_file():
        if not yaml:
            raise SystemExit("error: pip install pyyaml to read profile.yaml")
        return yaml.safe_load(plain.read_text(encoding="utf-8")) or {}
    if enc.is_file():
        raise SystemExit(
            f"error: only encrypted profile at {enc} — decrypt to profile.yaml first:\n"
            "  age -d -o localonly/vault/profile.yaml localonly/vault/profile.enc"
        )
    raise SystemExit(f"error: no profile in {vault_dir} — run vault_init.sh")


def validate_profile(profile: dict) -> None:
    ln = profile.get("legal_name") or {}
    first = (ln.get("first") or profile.get("first_name") or "").strip()
    last = (ln.get("last") or profile.get("last_name") or "").strip()
    if not first or not last:
        raise SystemExit(
            "error: profile missing legal_name.first and legal_name.last — fill localonly/vault/profile.yaml"
        )
    emails = profile.get("emails") or [profile.get("email")]
    if not any(str(e).strip() for e in emails if e):
        raise SystemExit("error: profile missing at least one email in emails[]")


def full_name(profile: dict) -> str:
    ln = profile.get("legal_name") or profile
    first = ln.get("first") or profile.get("first_name", "")
    last = ln.get("last") or profile.get("last_name", "")
    return f"{first} {last}".strip()


def primary_address(profile: dict) -> str:
    addrs = profile.get("addresses") or []
    if not addrs:
        return "[ADDRESS]"
    a = addrs[0]
    if isinstance(a, str):
        return a
    parts = [a.get("street"), a.get("city"), a.get("state"), a.get("zip"), a.get("country")]
    return ", ".join(p for p in parts if p)


def primary_email(profile: dict) -> str:
    emails = profile.get("emails") or [profile.get("email")]
    for e in emails:
        if e:
            return str(e)
    return "[EMAIL]"


def render_markdown(profile: dict, case_slug: str) -> str:
    name = full_name(profile)
    email = primary_email(profile)
    addr = primary_address(profile)
    today = date.today().isoformat()
    state = profile.get("state_of_residence") or profile.get("state") or "[STATE]"
    return f"""# Authorized Agent — Personal Data Erasure / Opt-Out

**Date:** {today}  
**Principal (data subject):** {name}  
**Contact email:** {email}  
**Address:** {addr}  
**Case:** {case_slug}

---

## Appointment

I, **{name}**, appoint myself (or my designated local automation tooling operating solely on my device) as authorized agent to submit data erasure, deletion, and opt-out requests on my behalf to data brokers and people-search services.

This appointment is made under:

- **California:** California Consumer Privacy Act (CCPA/CPRA), including rights to delete and opt out of sale/sharing; and where applicable, the California Delete Act (DROP).
- **European Union / UK:** GDPR Article 17 (right to erasure) and Article 21 (objection to processing), where applicable.

## Scope

The agent may:

1. Submit opt-out and erasure requests using the identifiers listed in my encrypted local profile.
2. Receive and triage broker responses to the contact email above.
3. Re-submit requests on a recurring basis when data reappears.

The agent may **not** sell, share, or store my data with third-party cloud services.

## Identifiers authorized for matching

- Legal name and documented aliases (see local profile)
- Email addresses and phone numbers listed in local profile
- Current and prior mailing addresses listed in local profile

## Signature

_________________________________________  
{name}  
Date: {today}

---

*Template only — not legal advice. Review before signing. Store signed PDF in `localonly/cases/{case_slug}/mandate/`.*
"""


def render_html(md_body: str, title: str) -> str:
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_body = md_body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{safe_title}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 700px; margin: 2rem auto; line-height: 1.5; }}
  h1 {{ font-size: 1.25rem; }}
  @media print {{ body {{ margin: 1in; }} }}
</style>
</head>
<body>
<h1>{safe_title}</h1>
<pre style="white-space: pre-wrap; font-family: inherit;">{safe_body}</pre>
</body>
</html>
"""


def main() -> None:
    p = argparse.ArgumentParser(description="Generate authorized-agent mandate")
    p.add_argument("--case", required=True, help="case slug")
    p.add_argument("--vault", type=Path, default=SKILL_ROOT / "localonly" / "vault")
    args = p.parse_args()

    profile = load_profile(args.vault)
    validate_profile(profile)

    case_dir = SKILL_ROOT / "localonly" / "cases" / args.case / "mandate"
    case_dir.mkdir(parents=True, exist_ok=True)

    md = render_markdown(profile, args.case)
    md_path = case_dir / "authorized-agent.md"
    html_path = case_dir / "authorized-agent.html"
    md_path.write_text(md, encoding="utf-8")
    html_path.write_text(render_html(md, "Authorized Agent Mandate"), encoding="utf-8")

    meta = {
        "generated_at": date.today().isoformat(),
        "case": args.case,
        "markdown": str(md_path),
        "html": str(html_path),
        "note": "Print HTML to PDF; sign; store as signed PDF in same directory",
    }
    (case_dir / "manifest.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
