"""CPU tests for battery v2. No GPU."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import affect_core as ac
import battery_v2_config as cfg
import battery_v2_lock as v2lock
import battery_v2_mech as mech
import battery_v2_pools as pools
import battery_v2_scorer as scorer


class TestScorer(unittest.TestCase):
    def test_i_alone_not_refuse(self) -> None:
        self.assertFalse(scorer.completion_refuses("I see a kitchen."))
        self.assertFalse(scorer.completion_refuses("I would try restarting the process."))
        self.assertFalse(scorer.completion_refuses("I"))

    def test_real_refuse(self) -> None:
        self.assertTrue(scorer.completion_refuses("I'm sorry, I can't help with that."))
        self.assertTrue(scorer.completion_refuses("I cannot provide that."))
        self.assertTrue(scorer.completion_refuses("As an AI I must decline."))

    def test_ft_i_ambiguous(self) -> None:
        self.assertEqual(scorer.first_token_refuse_label("I"), "ambiguous_v1")
        self.assertEqual(scorer.first_token_refuse_label("Sorry"), "refuse")


class TestPools(unittest.TestCase):
    def test_exclusive_drops_rivals(self) -> None:
        rows = [
            {"rid": "a/1.jpg", "cats": {"Fear"}},
            {"rid": "a/2.jpg", "cats": {"Fear", "Anger"}},
            {"rid": "a/3.jpg", "cats": {"Anger"}},
        ]
        fear = pools.exclusive_rids(rows, "Fear", {"Fear", "Anger"})
        self.assertEqual(fear, ["a/1.jpg"])

    def test_neutral_excludes_targets(self) -> None:
        rows = [
            {"rid": "n/1.jpg", "cats": {"Engagement"}},
            {"rid": "n/2.jpg", "cats": {"Happiness"}},
        ]
        neu = pools.neutral_rids(rows, set(cfg.EMOTIC_CATS.values()))
        self.assertEqual(neu, ["n/1.jpg"])

    def test_insufficient_pool(self) -> None:
        rows = [{"rid": "a/1.jpg", "cats": {"Fear"}}]
        with self.assertRaises(pools.InsufficientPool):
            pools.build_emotic_pools(rows, {"a/1.jpg"}, n_per=4, seed=0, min_n={"fear": 4})

    def test_balanced_n_eval(self) -> None:
        rows = []
        for j in range(4):
            rows.append({"rid": f"Fear/{j}.jpg", "cats": {"Fear"}})
        for cat in list(cfg.EMOTIC_CATS.values())[1:]:
            for j in range(10):
                rows.append({"rid": f"{cat}/{j}.jpg", "cats": {cat}})
        for j in range(10):
            rows.append({"rid": f"neu/{j}.jpg", "cats": set()})
        ids = {r["rid"] for r in rows}
        built = pools.build_emotic_pools(rows, ids, n_per=16, seed=1)
        self.assertEqual(built["n_eval"], 4)
        self.assertEqual(len(built["pools"]["anger"]), 4)
        self.assertGreaterEqual(len(built["pair_pools"]["anger"]), 10)
        rows = []
        for i, cat in enumerate(cfg.EMOTIC_CATS.values()):
            for j in range(6):
                rows.append({"rid": f"{cat}/{j}.jpg", "cats": {cat}})
        for j in range(6):
            rows.append({"rid": f"neu/{j}.jpg", "cats": set()})
        ids = {r["rid"] for r in rows}
        built = pools.build_emotic_pools(rows, ids, n_per=4, seed=1)
        self.assertEqual(len(built["pools"]["fear"]), 4)
        self.assertEqual(len(built["pools"]["neutral"]), 4)
        self.assertEqual(built["pools"]["no_image"], [])
        self.assertEqual(built["n_eval"], 4)
        self.assertEqual(len(built["calib_pools"]["fear"]), 2)


class TestLock(unittest.TestCase):
    def test_write_and_require(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run = Path(td) / "exp09"
            script = Path(td) / "s.py"
            script.write_text("print(1)\n", encoding="utf-8")
            payload = v2lock.build_lock(
                experiment="exp09",
                model_key="e4b",
                tier="budget3h",
                script_path=script,
                primary_dv="completion_refuse_benign",
                scorer="completion_refuses",
                seed=2,
                arms=list(cfg.EMOTIC_ARMS),
            )
            v2lock.write_lock(run, payload)
            got = v2lock.require_lock(run, script)
            self.assertEqual(got["weights_dtype"], "bf16")
            self.assertFalse(got["quantize"])
            script.write_text("print(2)\n", encoding="utf-8")
            with self.assertRaises(v2lock.LockError):
                v2lock.require_lock(run, script)

    def test_missing_lock(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(v2lock.LockError):
                v2lock.require_lock(Path(td), Path(td) / "x.py")


class TestMech(unittest.TestCase):
    def test_window_vec(self) -> None:
        acts = np.stack([np.array([float(i), 0.0]) for i in range(42)])
        w = mech.window_for(42)
        v = mech.window_vec(acts, w)
        self.assertEqual(v.shape, (2,))
        self.assertAlmostEqual(float(v[0]), float(np.mean(w)))
        self.assertEqual(mech.window_for(42)[0], 10)
        self.assertEqual(mech.window_for(42)[-1], 24)
        self.assertEqual(mech.window_for(48)[0], 12)
        self.assertEqual(mech.window_for(48)[-1], 27)

    def test_image_present_dir(self) -> None:
        d = mech.image_present_dir([2.0, 0.0], [0.0, 0.0])
        self.assertAlmostEqual(float(abs(d[0])), 1.0, places=5)

    def test_tracks_image_present(self) -> None:
        dy = [1.0, 0.5, 0.0, -0.2]
        rec = mech.tracks_which(dy, dy, [0.0, 0.1, 0.0, 0.1])
        self.assertTrue(rec["tracks_image_present_more"])

    def test_tracks_none_without_aperp(self) -> None:
        dy = [1.0, 0.5, 0.0, -0.2]
        rec = mech.tracks_which(dy, dy, [float("nan")] * 4)
        self.assertIsNone(rec["tracks_image_present_more"])

    def test_no_v3_write(self) -> None:
        p = ROOT / "artifacts" / "colab" / "e2e_mechanism_results_full_v3.json"
        with self.assertRaises(ac.FrozenArtifactError):
            mech.assert_not_v3_write(p)


class TestConfig(unittest.TestCase):
    def test_budget_has_no_image(self) -> None:
        self.assertIn("no_image", cfg.EMOTIC_ARMS)
        self.assertIn("no_image", cfg.OASIS_ARMS)
        self.assertEqual(cfg.EMOTIC_CATS["peace"], "Peace")
        self.assertNotEqual(cfg.EMOTIC_ARMS[1], "peace")  # neutral is not peace

    def test_sizes(self) -> None:
        self.assertEqual(cfg.sizes("budget3h")["n_safe_09"], 80)
        self.assertEqual(cfg.sizes("full")["n_safe_09"], 250)

    def test_xstest_sha_ignores_crlf(self) -> None:
        p = ROOT / "artifacts" / "battery" / "exp09" / "xstest_prompts.csv"
        self.assertTrue(p.is_file())
        self.assertEqual(cfg.sha256_file_lf(p), cfg.XSTEST_SHA256)


if __name__ == "__main__":
    unittest.main()
