import unittest

from app.release_gate.gate import evaluate_release


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.baseline = {
            "task_success_rate": 0.82,
            "p95_latency_ms": 1200,
            "unauthorized_call_rate": 0.0,
            "citation_validity": 0.96,
        }
        self.candidate = {
            "task_success_rate": 0.86,
            "p95_latency_ms": 1250,
            "unauthorized_call_rate": 0.0,
            "citation_validity": 0.97,
        }
        self.policy = {
            "minimum": {"task_success_rate": 0.80, "citation_validity": 0.95},
            "maximum": {"p95_latency_ms": 1500},
            "zero_tolerance": {"unauthorized_call_rate": True},
            "max_regression": {"p95_latency_ms": 200},
        }

    def test_candidate_passes(self):
        result = evaluate_release(self.baseline, self.candidate, self.policy)
        self.assertTrue(result["passed"])
        self.assertEqual(result["failures"], [])

    def test_quality_below_minimum_fails(self):
        self.candidate["task_success_rate"] = 0.70
        result = evaluate_release(self.baseline, self.candidate, self.policy)
        self.assertFalse(result["passed"])
        self.assertTrue(any("minimum:task_success_rate" in item for item in result["failures"]))

    def test_nonzero_safety_metric_fails(self):
        self.candidate["unauthorized_call_rate"] = 0.01
        result = evaluate_release(self.baseline, self.candidate, self.policy)
        self.assertFalse(result["passed"])
        self.assertTrue(any("zero_tolerance:unauthorized_call_rate" in item for item in result["failures"]))

    def test_latency_regression_fails(self):
        self.candidate["p95_latency_ms"] = 1500
        result = evaluate_release(self.baseline, self.candidate, self.policy)
        self.assertFalse(result["passed"])
        self.assertTrue(any("max_regression:p95_latency_ms" in item for item in result["failures"]))

    def test_missing_candidate_metric_fails(self):
        del self.candidate["citation_validity"]
        result = evaluate_release(self.baseline, self.candidate, self.policy)
        self.assertFalse(result["passed"])

    def test_missing_baseline_metric_fails_regression_check(self):
        del self.baseline["p95_latency_ms"]
        result = evaluate_release(self.baseline, self.candidate, self.policy)
        self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main()
