# Local CPU tests for exp08. No GPU, no network required except optional Perez skip.
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import battery_exp08_lib as L  # noqa: E402


class TertileTests(unittest.TestCase):
    def test_tertiles_split_thirds(self):
        vals = list(range(1, 10))
        lo, hi, labels = L.tertile_bucket(vals, q=1 / 3)
        self.assertLess(lo, hi)
        self.assertEqual(labels.count("neg") + labels.count("neu") + labels.count("pos"), 9)
        self.assertGreaterEqual(labels.count("neg"), 2)
        self.assertGreaterEqual(labels.count("pos"), 2)

    def test_attach_does_not_invent(self):
        items = [{"theme": f"I{i}", "valence": float(i)} for i in range(1, 10)]
        meta = L.attach_oasis_tertiles(items, q=1 / 3)
        self.assertFalse(meta.get("invented_ratings", False))
        self.assertEqual(meta["construct"], "elicited_viewer_valence")
        self.assertTrue(all("bucket" in x for x in items))


class SignatureTests(unittest.TestCase):
    def test_no_pooled_number_on_match(self):
        per = {
            "emotic": {
                "risk": {"delta": {"mean": 0.4, "lo": 0.1, "hi": 0.7, "n": 12}},
                "dictator": {"delta": {"mean": 0.3, "lo": 0.1, "hi": 0.5, "n": 12}},
                "perez": {"delta": {"mean": 0.2, "lo": 0.05, "hi": 0.4, "n": 12}},
            },
            "oasis": {
                "risk": {"delta": {"mean": 0.5, "lo": 0.2, "hi": 0.8, "n": 12}},
                "dictator": {"delta": {"mean": 0.25, "lo": 0.05, "hi": 0.4, "n": 12}},
                "perez": {"delta": {"mean": 0.15, "lo": 0.02, "hi": 0.3, "n": 12}},
            },
        }
        out = L.compare_signatures(per)
        self.assertTrue(out["do_not_pool"])
        self.assertIsNone(out["pooled_effect_size"])
        self.assertEqual(out["verdict"], "signatures_match_visual_affect")

    def test_split_stops_induction_claim(self):
        per = {
            "emotic": {"risk": {"delta": {"mean": 0.5, "lo": 0.2, "hi": 0.8, "n": 12}}},
            "oasis": {"risk": {"delta": {"mean": -0.4, "lo": -0.7, "hi": -0.1, "n": 12}}},
        }
        out = L.compare_signatures(per)
        self.assertEqual(out["verdict"], "signatures_split_stop_calling_emotic_induction")
        self.assertIsNone(out["pooled_effect_size"])
        self.assertFalse(out["by_task"]["risk"]["match"])


class TaskBankTests(unittest.TestCase):
    def test_risk_is_ab_forced_choice(self):
        items = L.risk_items(8, seed=0)
        self.assertEqual(len(items), 8)
        for it in items:
            self.assertIn("(A)", it["prompt"])
            self.assertIn("(B)", it["prompt"])
            self.assertIn(it["primary_label"], ("A", "B"))
            self.assertEqual(it["dv"], "choose_risky")

    def test_dictator_is_ab_forced_choice(self):
        items = L.dictator_items(8, seed=1)
        self.assertEqual(len(items), 8)
        for it in items:
            self.assertIn("dictator", it["prompt"].lower())
            self.assertEqual(it["dv"], "choose_generous")


class GateTests(unittest.TestCase):
    def test_gate_counts_passed_total(self):
        result = {
            "oasis": {"meta": {"n_rated": 900, "invented_ratings": False, "rating_source": "osf"}},
            "emotic": {"meta": {"split_hash": L.EXPECTED_SPLIT}},
            "perez_hashes_ok": True,
            "perez_hashes": dict(L.EXPECTED_PEREZ_SHA256),
            "model": {"id": L.PRIMARY_MODEL, "weights_dtype": "nf4"},
            "frozen_v3_untouched": True,
            "signatures": {"do_not_pool": True},
            "fc_mass_mean": 0.91,
            "primary_estimates": {
                "emotic": {t: {"mean": 0.1} for t in ("risk", "dictator", "perez")},
                "oasis": {t: {"mean": 0.2} for t in ("risk", "dictator", "perez")},
            },
        }
        g = L.gate_block(result)
        self.assertEqual(g["total"], 9)
        self.assertTrue(g["ok"])
        self.assertEqual(g["passed"], 9)

    def test_gate_fails_on_nan_primary(self):
        result = {
            "oasis": {"meta": {"n_rated": 900, "invented_ratings": False}},
            "emotic": {"meta": {"split_hash": L.EXPECTED_SPLIT}},
            "perez_hashes_ok": True,
            "model": {"id": L.PRIMARY_MODEL, "weights_dtype": "nf4"},
            "frozen_v3_untouched": True,
            "signatures": {"do_not_pool": True},
            "fc_mass_mean": 0.91,
            "primary_estimates": {
                "emotic": {"risk": {"mean": float("nan")}},
                "oasis": {"risk": {"mean": 0.1}},
            },
        }
        g = L.gate_block(result)
        self.assertFalse(g["ok"])


class DoneExpTests(unittest.TestCase):
    def test_night_done_and_terminal_stages(self):
        recs = {
            "exp02": {"stage": "scoring"},
            "exp04": {"stage": "done"},
            "exp09": {"stage": "model_load"},
        }
        done = L.collect_done_exps(recs)
        self.assertIn("exp01", done)
        self.assertIn("exp04", done)
        self.assertIn("exp06", done)
        self.assertNotIn("exp02", done)
        self.assertNotIn("exp09", done)
        self.assertNotIn("exp08", done)


class DeltaTests(unittest.TestCase):
    def test_paired_delta_finite(self):
        d = L.paired_delta([1.0, 2.0, 3.0], [0.0, 1.0, 2.0], n_boot=32, seed=0)
        self.assertTrue(math.isfinite(d["mean"]))
        self.assertEqual(d["n"], 3)


if __name__ == "__main__":
    unittest.main()
