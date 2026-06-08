#!/usr/bin/env python3
"""Phase 2: mandate gate, alias expansion, eraser parse, manual queue."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from eraser_adapter import (  # noqa: E402
    parse_eraser_success,
    resolve_brokers_for_eraser,
)
from manual_tasks_export import build_tasks  # noqa: E402
from opacite_lib import (  # noqa: E402
    append_event,
    append_failed_batch,
    expand_profile_aliases,
    init_state_db,
    mandate_manifest_path,
    mandate_ready,
    require_mandate,
)


class TestMandateGate(unittest.TestCase):
    def test_require_mandate_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slug = "mandate-test"
            case = Path(tmp) / "cases" / slug / "mandate"
            case.mkdir(parents=True)
            with mock.patch("opacite_lib.SKILL_ROOT", Path(tmp)):
                with mock.patch("opacite_lib.case_dir", lambda s: Path(tmp) / "cases" / s):
                    with mock.patch(
                        "opacite_lib.mandate_manifest_path",
                        lambda s: Path(tmp) / "cases" / s / "mandate" / "manifest.json",
                    ):
                        self.assertFalse(mandate_ready(slug))
                        with self.assertRaises(SystemExit):
                            require_mandate(slug)

    def test_require_mandate_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slug = "mandate-ok"
            manifest = Path(tmp) / "cases" / slug / "mandate" / "manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text("{}", encoding="utf-8")
            with mock.patch(
                "opacite_lib.mandate_manifest_path",
                lambda s: Path(tmp) / "cases" / s / "mandate" / "manifest.json",
            ):
                self.assertTrue(mandate_ready(slug))
                require_mandate(slug)


class TestAliasExpansion(unittest.TestCase):
    def test_three_emails_expanded(self) -> None:
        profile = {
            "legal_name": {"first": "Wei", "last": "Jia"},
            "aliases": [{"first": "W", "last": "Jia"}],
            "emails": ["a@example.com", "b@example.com", "c@example.com"],
            "phones": ["111", "222", "333"],
            "addresses": [{"city": "SF"}],
        }
        out = expand_profile_aliases(profile)
        self.assertEqual(len(out["emails"]), 3)
        self.assertEqual(len(out["phones"]), 3)
        self.assertEqual(len(out["name_variants"]), 2)
        self.assertGreaterEqual(out["identifier_count"], 6)


class TestEraserParse(unittest.TestCase):
    def test_sent_lines(self) -> None:
        stdout = "[1/2] Acme Data (privacy@acme.com) — sent\n"
        submitted, failed = parse_eraser_success(stdout, ["acme-data", "other-broker"])
        self.assertIn("acme-data", submitted)
        self.assertEqual(failed, [])


class TestEraserResolve(unittest.TestCase):
    def test_optery_numeric_id_resolves_by_name_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            eraser_yaml = root / "eraser.yaml"
            eraser_yaml.write_text(
                "brokers:\n"
                "  - id: 33-mile-radius\n"
                "    name: 33 MILE RADIUS LLC\n"
                "    email: legal@evercommerce.com\n",
                encoding="utf-8",
            )
            reg_path = root / "registry.json"
            reg_path.write_text(
                json.dumps({
                    "brokers": [{
                        "id": "21022",
                        "name": "33 Mile Radius",
                        "contact_email": "privacy@33mileradius.com",
                        "process": "email-opt-out",
                    }],
                }),
                encoding="utf-8",
            )
            items, _ = resolve_brokers_for_eraser(["21022"], eraser_yaml, reg_path)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["id"], "33-mile-radius")
            self.assertEqual(items[0]["email"], "legal@evercommerce.com")


class TestManualExport(unittest.TestCase):
    def test_failed_event_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slug = "manual-exp"
            root = Path(tmp)
            reg = {
                "brokers": [
                    {
                        "id": "broker-a",
                        "name": "Broker A",
                        "process": "email-opt-out",
                        "opt_out_url": "mailto:a@broker.com",
                    },
                    {
                        "id": "idv-broker",
                        "name": "IDV Co",
                        "process": "id-verification",
                    },
                ],
                "count": 2,
            }
            reg_path = root / "brokers.json"
            reg_path.write_text(json.dumps(reg), encoding="utf-8")

            case_fn = lambda s: root / "cases" / s  # noqa: E731
            with mock.patch("opacite_lib.SKILL_ROOT", root):
                with mock.patch("manual_tasks_export.SKILL_ROOT", root):
                    with mock.patch("opacite_lib.case_dir", case_fn):
                        with mock.patch("manual_tasks_export.case_dir", case_fn):
                            init_state_db(slug)
                            append_failed_batch(
                                slug, ["broker-a"], "email", reason="smtp timeout"
                            )
                            payload = build_tasks(slug, reg_path)
            reasons = {t["reason"] for t in payload["tasks"]}
            self.assertIn("failed_send", reasons)
            self.assertIn("id_verification", reasons)


if __name__ == "__main__":
    unittest.main()
