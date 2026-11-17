import unittest

from app.rag_eval.metrics import (
    hit_rate_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class RetrievalMetricsTests(unittest.TestCase):
    def test_precision_at_k(self):
        self.assertAlmostEqual(
            precision_at_k(["a", "x", "b", "y"], {"a", "b"}, 3),
            2 / 3,
        )

    def test_precision_uses_k_as_denominator_when_fewer_results_returned(self):
        self.assertAlmostEqual(precision_at_k(["a"], {"a", "b"}, 5), 1 / 5)

    def test_recall_at_k(self):
        self.assertAlmostEqual(
            recall_at_k(["x", "a", "y", "b"], {"a", "b", "c"}, 4),
            2 / 3,
        )

    def test_hit_rate_at_k(self):
        self.assertEqual(hit_rate_at_k(["x", "a"], {"a"}, 2), 1.0)
        self.assertEqual(hit_rate_at_k(["x", "y"], {"a"}, 2), 0.0)

    def test_reciprocal_rank(self):
        self.assertAlmostEqual(reciprocal_rank(["x", "y", "a"], {"a"}), 1 / 3)
        self.assertEqual(reciprocal_rank(["x", "y"], {"a"}), 0.0)

    def test_mean_reciprocal_rank(self):
        results = [["a", "x"], ["x", "b"], ["x", "y"]]
        judgments = [{"a"}, {"b"}, {"c"}]
        self.assertAlmostEqual(
            mean_reciprocal_rank(results, judgments),
            (1 + 0.5 + 0) / 3,
        )

    def test_ndcg_perfect_ranking(self):
        self.assertAlmostEqual(ndcg_at_k(["a", "b", "x"], {"a", "b"}, 3), 1.0)

    def test_ndcg_penalizes_lower_relevant_rank(self):
        ideal = ndcg_at_k(["a", "b", "x"], {"a", "b"}, 3)
        lower = ndcg_at_k(["x", "a", "b"], {"a", "b"}, 3)
        self.assertLess(lower, ideal)

    def test_empty_relevance_returns_zero(self):
        self.assertEqual(precision_at_k(["a"], set(), 3), 0.0)
        self.assertEqual(recall_at_k(["a"], set(), 3), 0.0)
        self.assertEqual(hit_rate_at_k(["a"], set(), 3), 0.0)
        self.assertEqual(ndcg_at_k(["a"], set(), 3), 0.0)

    def test_invalid_k(self):
        for value in (0, -1, True):
            with self.subTest(k=value):
                with self.assertRaises(ValueError):
                    precision_at_k(["a"], {"a"}, value)


if __name__ == "__main__":
    unittest.main()
