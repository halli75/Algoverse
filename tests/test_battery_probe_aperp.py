"""Numpy-only tests for the exp10 a_perp probe helper."""

from __future__ import annotations

import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import affect_core as ac  # noqa: E402
import battery_probe_aperp as probe  # noqa: E402


class TestProjection(unittest.TestCase):
    def test_window_matches_core(self) -> None:
        self.assertEqual(probe.core_window(42), list(range(10, 25)))
        acts = np.zeros((42, 4))
        dirs = np.zeros((42, 4))
        dirs[:, 0] = 1.0
        acts[10] = np.array([2.0, 0, 0, 0])
        acts[24] = np.array([4.0, 0, 0, 0])
        acts[0] = np.array([100.0, 0, 0, 0])
        p = probe.project_aperp(acts, dirs)
        self.assertAlmostEqual(p, (2.0 + 4.0) / 15.0)

    def test_hidden_states_drop_embedding(self) -> None:
        emb = np.ones((1, 3, 4))
        layers = [np.zeros((1, 3, 4)) for _ in range(42)]
        layers[10][0, -1, 0] = 7.0
        acts = probe.hidden_states_to_acts([emb, *layers], n_layers=42)
        self.assertEqual(acts.shape, (42, 4))
        self.assertAlmostEqual(float(acts[10, 0]), 7.0)


class TestMediationMath(unittest.TestCase):
    def test_perfect_positive_mediation(self) -> None:
        dm = np.linspace(1.0, 3.0, 64)
        dy = 2.0 * dm
        rec = probe.paired_product_of_coefficients(dm, dy)
        self.assertGreater(rec["a_mean_dM"], 0)
        self.assertAlmostEqual(rec["b_dY_on_dM"], 2.0, places=6)
        self.assertAlmostEqual(rec["ab"], rec["a_mean_dM"] * 2.0, places=6)
        self.assertAlmostEqual(rec["pearson"], 1.0, places=6)
        self.assertIsNotNone(rec["spearman"])

    def test_zero_mediator_variance(self) -> None:
        dm = np.ones(64)
        dy = np.linspace(0, 1, 64)
        rec = probe.paired_product_of_coefficients(dm, dy)
        self.assertTrue(rec["b_dY_on_dM"] is None or (isinstance(rec["b_dY_on_dM"], float) and math.isnan(rec["b_dY_on_dM"])))
        v = probe.domain_verdict(rec, {}, 64)
        self.assertEqual(v, "NO_MEDIATOR_MOVEMENT")

    def test_insufficient_power(self) -> None:
        dm = np.arange(10, dtype=float)
        dy = dm
        rec = probe.paired_product_of_coefficients(dm, dy)
        self.assertEqual(probe.domain_verdict(rec, {}, 10), "INSUFFICIENT_POWER")

    def test_bootstrap_ci_finite(self) -> None:
        rng = np.random.default_rng(0)
        dm = rng.normal(1.0, 0.2, size=64)
        dy = 0.5 * dm + rng.normal(0, 0.05, size=64)
        ci = probe.bootstrap_ci(dm, dy, n_boot=200, seed=0)
        self.assertIsNotNone(ci["ab"]["lo"])
        self.assertTrue(probe.ci_excludes_zero(ci["ab"]["lo"], ci["ab"]["hi"]))

    def test_undefined_correlation_stays_none(self) -> None:
        self.assertIsNone(probe.pearson([1, 1, 1], [0, 1, 2]))
        self.assertIsNone(probe.spearman([1], [1]))


class TestFrozenGuard(unittest.TestCase):
    def test_refuse_v3_json_write(self) -> None:
        with self.assertRaises(ac.FrozenArtifactError):
            probe.refuse_v3_write(ac.FROZEN_V3_PATH)

    def test_pack_diagnostic_label(self) -> None:
        a = ac.unit(np.ones((4, 3)))
        r = ac.unit(np.array([[1.0, 0, 0], [1.0, 0, 0], [1.0, 0, 0], [1.0, 0, 0]]))
        body = probe.pack_diagnostic_dirs(
            {"a_perp": a, "r_dir": r},
            path="dirs_diagnostic.pt",
        )
        self.assertEqual(body["status"], probe.DIAGNOSTIC_LABEL)
        self.assertTrue(body["diagnostic"])


if __name__ == "__main__":
    unittest.main()
