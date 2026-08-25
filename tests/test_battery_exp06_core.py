"""Local numpy tests for exp06 waiting-game core. No GPU."""

from __future__ import annotations

import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import battery_exp06_core as c  # noqa: E402


class TestGrid(unittest.TestCase):
    def test_full_count(self) -> None:
        items = c.build_items("full")
        self.assertEqual(len(items), 7 * 31)

    def test_smoke_count(self) -> None:
        items = c.build_items("smoke")
        self.assertEqual(len(items), 4 * 8)

    def test_no_describe(self) -> None:
        for it in c.build_items("smoke"):
            p = c.prompt_for(it)
            self.assertNotIn("Describe", p)
            self.assertIn("Reply with exactly one letter", p)
            self.assertIn("A.", p)
            self.assertIn("B.", p)

    def test_dump_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "g.json"
            c.dump_grid(path)
            items = c.load_grid(path, "smoke")
            self.assertEqual(len(items), 32)


class TestK(unittest.TestCase):
    def test_implied_k_identity(self) -> None:
        # SS = LL / (1+k d)  =>  500 = 1000 / (1+k*1) => k=1
        self.assertAlmostEqual(c.implied_k(500, 1000, 1.0), 1.0)

    def test_patient_all_later(self) -> None:
        items = c.build_items("smoke")
        rows = []
        for it in items:
            rows.append({**it, "chose_now": bool(it["ss"] >= 1000), "fc_mass": 0.95})
        rec = c.kirby_k(rows)
        self.assertTrue(math.isfinite(rec["k"]))
        self.assertLess(rec["k"], 0.05)

    def test_impatient_all_now_except_zero(self) -> None:
        items = c.build_items("smoke")
        rows = []
        for it in items:
            rows.append({**it, "chose_now": it["ss"] > 0, "fc_mass": 0.9})
        rec = c.kirby_k(rows)
        self.assertTrue(math.isfinite(rec["k"]))
        self.assertGreater(rec["k"], 1.0)

    def test_known_switch(self) -> None:
        # For each delay, take now iff k_indiff < 0.2 (i.e. true k = 0.2)
        items = [it for it in c.build_items("full") if it["ss"] not in (0, 1000)]
        rows = []
        for it in items:
            rows.append({**it, "chose_now": (it["k_indiff"] or 0) < 0.2, "fc_mass": 0.99})
        rec = c.kirby_k(rows)
        self.assertTrue(0.05 < rec["k"] < 0.8)
        self.assertGreater(rec["consistency"], 0.9)

    def test_parse_letter(self) -> None:
        self.assertEqual(c.parse_letter("A"), "A")
        self.assertEqual(c.parse_letter("Answer: B"), "B")
        self.assertIsNone(c.parse_letter(""))


class TestGate(unittest.TestCase):
    def test_gate_counts(self) -> None:
        by = {}
        for cond in c.CONDITIONS:
            by[cond] = {"k": 0.1, "fc_mass": 0.9, "parse_rate": 1.0}
        g = c.gate_block(
            by,
            {
                "model_id": c.PRIMARY_MODEL,
                "weights_dtype": "nf4",
                "compute_dtype": "bf16",
                "split_hash": c.EXPECTED_SPLIT,
                "touched_v3": False,
            },
        )
        self.assertEqual(g["passed"], g["total"])
        self.assertGreaterEqual(g["total"], 10)


if __name__ == "__main__":
    unittest.main()
