"""Checks on the data snapshot, the method and the outputs. Run: make test"""
import hashlib, json, os, pathlib, sys, unittest
import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
import build  # noqa: E402


class Snapshot(unittest.TestCase):
    def test_raw_files_match_manifest(self):
        manifest = json.loads(pathlib.Path(ROOT, "data", "raw", "MANIFEST.json").read_text())
        for name, m in manifest.items():
            body = pathlib.Path(ROOT, "data", "raw", m.get("file", name + ".json")).read_bytes()
            self.assertEqual(hashlib.sha256(body).hexdigest(), m["sha256"], name)

    def test_preregistration_is_timestamped(self):
        """The proof commits to this exact file and carries a Bitcoin block attestation (not only a pending one)."""
        ots = pathlib.Path(ROOT, "PREREGISTRATION.md.ots").read_bytes()
        digest = hashlib.sha256(pathlib.Path(ROOT, "PREREGISTRATION.md").read_bytes()).digest()
        self.assertIn(digest, ots)
        self.assertIn(bytes.fromhex("0588960d73d71901"), ots)  # BitcoinBlockHeaderAttestation tag

    def test_predictions_are_timestamped(self):
        """PREDICTIONS.md is frozen: its timestamp proof must commit to the file as it is now."""
        ots = pathlib.Path(ROOT, "PREDICTIONS.md.ots").read_bytes()
        self.assertIn(hashlib.sha256(pathlib.Path(ROOT, "PREDICTIONS.md").read_bytes()).digest(), ots)
        self.assertIn(bytes.fromhex("0588960d73d71901"), ots)  # Bitcoin block 975308


class Method(unittest.TestCase):
    """The estimators recover known answers on synthetic data."""

    def panel(self, shock=1.0, seed=0):
        rng = np.random.default_rng(seed)
        days = pd.date_range("2025-11-10", "2026-11-09")
        f = np.exp(np.cumsum(rng.normal(0, 0.05, len(days))))  # common market factor
        p = pd.DataFrame(index=days)
        for i in range(4):
            p[f"d{i}"] = 1e7 * f * np.exp(rng.normal(0, 0.05, len(days)))
        p["near_vol"] = 1e8 * f * np.exp(rng.normal(0, 0.1, len(days)))
        p["zec_vol"] = 1e8 * np.exp(rng.normal(0, 0.1, len(days)))
        p["volume"] = 5e7 * f * np.exp(rng.normal(0, 0.05, len(days)))
        evt = (days >= build.T) & (days < build.T + pd.Timedelta(days=build.HORIZON))
        p.loc[evt, "volume"] *= shock
        return p, [f"d{i}" for i in range(4)]

    def test_no_shock_gives_near_zero(self):
        p, donors = self.panel()
        stat, _ = build.event_stat(p, "volume", donors, build.T)
        self.assertLess(abs(stat), 0.05)

    def test_injected_loss_is_recovered(self):
        p, donors = self.panel(shock=0.6)
        stat, _ = build.event_stat(p, "volume", donors, build.T)
        self.assertAlmostEqual(stat, np.log(0.6), delta=0.05)

    def test_simplex_fit_recovers_weights(self):
        rng = np.random.default_rng(1)
        D = rng.uniform(0.5, 1.5, (200, 3))
        w_true = np.array([0.6, 0.3, 0.1])
        w = build.simplex_fit(D @ w_true, D)
        self.assertAlmostEqual(w.sum(), 1.0, places=9)
        self.assertTrue((w >= 0).all())
        np.testing.assert_allclose(w, w_true, atol=0.02)


class Outputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.R = build.main()

    def test_windows_match_preregistration(self):
        w = self.R["windows"]
        self.assertEqual((w["estimation"]["from"], w["estimation"]["to"]), ("2026-06-01", "2026-09-07"))
        self.assertEqual(w["event"]["days"], 28)

    def test_verdict_follows_rule(self):
        h = self.R["H1"]
        lost = h["stat_log"] < 0 and h["p_placebo_time"] < 0.10
        self.assertEqual(h["verdict"], "flow was lost" if lost else "no detectable loss")

    def test_tripwire_status_follows_limit(self):
        for t in self.R["tripwires"]:
            self.assertEqual(t["status"], "holding" if t["value"] >= t["limit"] else "broken", t["name"])

    def test_thesis_fully_rendered(self):
        self.assertNotIn("{{", pathlib.Path(ROOT, "THESIS.md").read_text())
        self.assertNotIn("{{", pathlib.Path(ROOT, "README.md").read_text())
        page = pathlib.Path(ROOT, "docs", "thesis.html").read_text()
        self.assertNotIn("{{", page)
        self.assertIn("<h1>", page)

    def test_dashboard_data_matches_results(self):
        js = pathlib.Path(ROOT, "docs", "data.js").read_text()
        results = json.loads(pathlib.Path(ROOT, "data", "processed", "results.json").read_text())
        self.assertEqual(json.loads(js[len("window.RESULTS = "):-2]), results)


if __name__ == "__main__":
    unittest.main()
