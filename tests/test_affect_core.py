"""Unit tests for the locked shared affect/refusal core (no GPU)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import affect_core as ac  # noqa: E402


class TestFractionalGate(unittest.TestCase):
    def test_locked_windows(self) -> None:
        self.assertEqual(ac.fractional_gate_layers(34), (8, 20))
        self.assertEqual(ac.fractional_gate_layers(42), (10, 25))
        self.assertEqual(ac.fractional_gate_layers(48), (12, 28))

    def test_window_list_exclusive_hi(self) -> None:
        w = ac.gate_window(34)
        self.assertEqual(w[0], 8)
        self.assertEqual(w[-1], 19)
        self.assertEqual(len(w), 12)

    def test_core_config_rejects_drift(self) -> None:
        with self.assertRaises(ac.CoreConfigError):
            ac.CoreMethodConfig(alpha=0.15)
        with self.assertRaises(ac.CoreConfigError):
            ac.CoreMethodConfig(layers="late")
        ac.CoreMethodConfig()  # default ok


class TestUnitAndOrth(unittest.TestCase):
    def test_unit_scaling_per_layer(self) -> None:
        v = np.array([[3.0, 4.0, 0.0], [0.0, 0.0, 8.0]])
        u = ac.unit(v)
        self.assertTrue(np.allclose(np.linalg.norm(u, axis=-1), 1.0))
        self.assertTrue(np.allclose(u[0], np.array([0.6, 0.8, 0.0])))

    def test_span_orthogonality_two_nuisances(self) -> None:
        r = ac.unit(np.array([[1.0, 0.0, 0.0, 0.0]]))
        j = ac.unit(np.array([[1.0, 1.0, 0.0, 0.0]]))
        v = ac.unit(np.array([[1.0, 1.0, 1.0, 0.0]]))
        q = ac.orthogonalize_span(v, r, j)
        self.assertLess(abs(float(q[0] @ r[0])), 1e-8)
        self.assertLess(abs(float(q[0] @ j[0])), 1e-8)
        self.assertAlmostEqual(float(np.linalg.norm(q[0])), 1.0, places=6)

    def test_sequential_can_reintroduce_r(self) -> None:
        r = ac.unit(np.array([[1.0, 0.0, 0.0, 0.0]]))
        j = ac.unit(np.array([[1.0, 1.0, 0.0, 0.0]]))
        v = ac.unit(np.array([[1.0, 1.0, 1.0, 0.0]]))
        seq = ac.sequential_orth_legacy(v, r, j)
        qr = ac.orthogonalize_span(v, r, j)
        # Sequential leftover on r is the reason QR is locked for multi-dir cleaning.
        self.assertGreater(abs(float(seq[0] @ r[0])), abs(float(qr[0] @ r[0])))
        self.assertLess(abs(float(qr[0] @ r[0])), 1e-8)

    def test_single_dir_matches_sequential(self) -> None:
        r = ac.unit(np.array([[0.2, 0.9, -0.1, 0.4], [0.0, 1.0, 0.0, 0.0]]))
        a = ac.unit(np.array([[0.5, 0.5, 0.5, 0.5], [1.0, 1.0, 0.0, 0.0]]))
        self.assertTrue(np.allclose(ac.orthogonalize_span(a, r), ac.sequential_orth_legacy(a, r), atol=1e-8))

    def test_random_perp_off_r(self) -> None:
        r = ac.unit(np.random.default_rng(0).normal(size=(5, 16)))
        rnd = ac.make_random_perp(r, seed=7)
        dots = np.abs(np.sum(rnd * r, axis=-1))
        self.assertTrue(np.all(dots < 1e-8))
        self.assertTrue(np.allclose(np.linalg.norm(rnd, axis=-1), 1.0))
        rnd2 = ac.make_random_perp(r, seed=7)
        self.assertTrue(np.allclose(rnd, rnd2))


class TestProjectionScope(unittest.TestCase):
    def test_window_mean_ignores_outside_layers(self) -> None:
        acts = np.zeros((4, 3))
        dirs = np.zeros((4, 3))
        acts[0] = np.array([100.0, 0.0, 0.0])
        acts[1] = np.array([1.0, 0.0, 0.0])
        acts[2] = np.array([3.0, 0.0, 0.0])
        acts[3] = np.array([100.0, 0.0, 0.0])
        dirs[:, 0] = 1.0
        dirs = ac.unit(dirs)
        p = ac.window_mean_projection(acts, dirs, [1, 2])
        self.assertAlmostEqual(p, 2.0)
        pall = ac.all_layer_mean_projection(acts, dirs)
        self.assertAlmostEqual(pall, (100.0 + 1.0 + 3.0 + 100.0) / 4.0)

    def test_normscaled_coefficients(self) -> None:
        norms = np.array([10.0, 20.0, 40.0])
        c = ac.normscaled_coefficients(norms, 0.008, [1, 2])
        self.assertNotIn(0, c)
        self.assertAlmostEqual(c[1], 0.16)
        self.assertAlmostEqual(c[2], 0.32)


class TestSplitsAndArtifacts(unittest.TestCase):
    def test_split_overlap_rejected(self) -> None:
        with self.assertRaises(ac.SplitOverlapError):
            ac.assert_disjoint_manifests(["a", "b"], ["b", "c"])

    def test_hashed_splits_disjoint_and_stable(self) -> None:
        ids = [f"img-{i}" for i in range(100)]
        m1 = ac.hashed_disjoint_ids(ids, seed=0)
        m2 = ac.hashed_disjoint_ids(ids, seed=0)
        self.assertEqual(m1["hash"], m2["hash"])
        self.assertEqual(m1["train_ids"], m2["train_ids"])
        ac.assert_disjoint_manifests(m1["train_ids"], m1["calib_ids"], m1["eval_ids"])
        self.assertEqual(sum(m1["n"].values()), 100)

    def test_frozen_v3_basename_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / ac.FROZEN_V3_BASENAME
            with self.assertRaises(ac.FrozenArtifactError):
                ac.assert_writable_result_path(p)
            with self.assertRaises(ac.FrozenArtifactError):
                ac.write_create_only(p, {"x": 1})

    def test_repo_frozen_v3_rejected(self) -> None:
        self.assertTrue(ac.FROZEN_V3_PATH.exists())
        with self.assertRaises(ac.FrozenArtifactError):
            ac.assert_writable_result_path(ac.FROZEN_V3_PATH)

    def test_create_only_rejects_existing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "core_results_v1.json"
            ac.write_create_only(p, {"ok": True})
            with self.assertRaises(FileExistsError):
                ac.write_create_only(p, {"ok": False})
            self.assertEqual(json.loads(p.read_text())["ok"], True)

    def test_refusal_score_sign(self) -> None:
        vocab = 20
        logits = np.zeros(vocab)
        refuse_ids, comply_ids = [1, 2], [10, 11]
        logits[1] = 5.0
        self.assertGreater(ac.first_token_refusal_score(logits, refuse_ids, comply_ids), 0.0)
        logits = np.zeros(vocab)
        logits[10] = 5.0
        self.assertLess(ac.first_token_refusal_score(logits, refuse_ids, comply_ids), 0.0)
        self.assertTrue(ac.is_refusal(0.1))
        self.assertFalse(ac.is_refusal(0.0))

    def test_calibrate_no_gate(self) -> None:
        out = ac.calibrate_gate_on_split(
            affect_refuse_at=lambda a: 0.9,
            random_refuse_at=lambda a: 0.1,
            coherent_at=lambda a: True,
        )
        self.assertEqual(out["status"], "NO_GATE")
        self.assertIsNone(out["alpha"])

    def test_calibrate_smallest_pass(self) -> None:
        out = ac.calibrate_gate_on_split(
            affect_refuse_at=lambda a: 0.10 if a >= 0.008 else 0.50,
            random_refuse_at=lambda a: 0.90,
            coherent_at=lambda a: True,
        )
        self.assertEqual(out["status"], "PASS")
        self.assertEqual(out["alpha"], 0.008)

    def test_joint_affect_construction(self) -> None:
        a_t = ac.unit(np.array([[1.0, 0.0, 0.0]]))
        a_i = ac.unit(np.array([[0.0, 1.0, 0.0]]))
        both = ac.build_joint_affect(a_t, a_i)
        r = ac.unit(np.array([[0.0, 0.0, 1.0]]))
        a_perp = ac.build_a_perp(both, r)
        self.assertLess(abs(float(a_perp[0] @ r[0])), 1e-8)


if __name__ == "__main__":
    unittest.main()
