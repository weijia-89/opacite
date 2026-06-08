#!/usr/bin/env python3
"""Unit tests for opacite registry merge and campaign state."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from opacite_lib import (  # noqa: E402
    append_planned_batch,
    status_summary,
)
from opacite_registry import (  # noqa: E402
    find_optery_merge_target,
    infer_process_generic,
    is_drop_eligible,
    make_broker,
    merge_broker,
    merge_registry,
)


class TestInferProcess(unittest.TestCase):
    def test_mailto_is_email(self) -> None:
        self.assertEqual(
            infer_process_generic({"opt_out_url": "mailto:privacy@x.com"}),
            "email-opt-out",
        )

    def test_url_with_email_word_not_email_lane(self) -> None:
        self.assertEqual(
            infer_process_generic({"opt_out_url": "https://x.com/email-opt-out-form"}),
            "direct-form",
        )


class TestDropEligible(unittest.TestCase):
    def test_us_only_not_drop(self) -> None:
        self.assertFalse(is_drop_eligible(["US"], "direct-form"))

    def test_us_ca_is_drop(self) -> None:
        self.assertTrue(is_drop_eligible(["US", "US-CA"], "direct-form"))


class TestMergeBroker(unittest.TestCase):
    def test_eraser_merges_into_optery_by_name_slug(self) -> None:
        reg: dict = {}
        optery = make_broker(
            "21022",
            "33 Mile Radius",
            {"email": "privacy@33mileradius.com"},
            ["optery"],
            process="email-opt-out",
        )
        eraser = make_broker(
            "33-mile-radius",
            "33 MILE RADIUS LLC",
            {"email": "legal@evercommerce.com"},
            ["eraser"],
            process="email-opt-out",
        )
        merge_broker(reg, optery)
        target = find_optery_merge_target(reg, eraser)
        self.assertEqual(target, "21022")

    def test_eraser_upgrades_process(self) -> None:
        base = {
            "id": "spokeo",
            "name": "Spokeo",
            "process": "direct-form",
            "runner": "symaira",
            "sources": ["symaira"],
            "jurisdiction": ["US"],
            "drop_eligible": False,
        }
        incoming = {
            "id": "spokeo",
            "process": "email-opt-out",
            "runner": "eraser",
            "contact_email": "privacy@spokeo.com",
            "sources": ["eraser"],
            "jurisdiction": ["US"],
            "drop_eligible": False,
        }
        reg: dict = {}
        merge_broker(reg, base)
        merge_broker(reg, incoming)
        self.assertEqual(reg["spokeo"]["process"], "email-opt-out")
        self.assertEqual(reg["spokeo"]["runner"], "eraser")
        self.assertEqual(reg["spokeo"]["contact_email"], "privacy@spokeo.com")


class TestMergeRegistry(unittest.TestCase):
    def test_mini_fixtures_merge(self) -> None:
        fixtures = ROOT / "tests" / "fixtures"
        out = merge_registry(
            fixtures / "optery-mini.json",
            fixtures / "eraser-mini.yaml",
            None,
            "US",
            merge_eraser=True,
            merge_symaira=False,
        )
        self.assertGreaterEqual(out["count"], 2)
        by_id = {b["id"]: b for b in out["brokers"]}
        self.assertEqual(by_id["spokeo"]["process"], "email-opt-out")
        self.assertIn("eraser", by_id["spokeo"]["sources"])


class TestPlanIdempotency(unittest.TestCase):
    def test_replan_skips_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            slug = "testcase"
            case_root = Path(tmp) / "cases" / slug
            case_root.mkdir(parents=True)
            # Point opacite_lib at temp tree
            import opacite_lib as lib

            orig_root = lib.SKILL_ROOT
            lib.SKILL_ROOT = Path(tmp)
            lib.SCHEMA_SQL = orig_root / "schemas" / "campaign.sql"
            try:
                brokers = [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}]
                n1 = append_planned_batch(slug, brokers, "email", campaign_id="c1")
                n2 = append_planned_batch(slug, brokers, "email", campaign_id="c2")
                self.assertEqual(n1, 2)
                self.assertEqual(n2, 0)
                summary = status_summary(slug)
                self.assertEqual(summary.get("PLANNED"), 2)
            finally:
                lib.SKILL_ROOT = orig_root


if __name__ == "__main__":
    unittest.main()
