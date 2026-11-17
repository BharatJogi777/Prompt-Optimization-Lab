import unittest

from app.agent_eval.metrics import (
    argument_exact_match_rate,
    average_tool_calls,
    task_success_rate,
    tool_execution_success_rate,
    tool_selection_accuracy,
    unauthorized_call_rate,
)


class AgentMetricsTests(unittest.TestCase):
    def test_tool_selection_accuracy_includes_no_tool_cases(self):
        expected = ["search_logs", None, "get_service_status"]
        actual = ["search_logs", None, "restart_service"]
        self.assertAlmostEqual(tool_selection_accuracy(expected, actual), 2 / 3)

    def test_tool_selection_rejects_different_lengths(self):
        with self.assertRaises(ValueError):
            tool_selection_accuracy(["search_logs"], [])

    def test_argument_exact_match_rate(self):
        expected = [{"service": "payments", "limit": 20}, {"order_id": "ord-1"}]
        actual = [{"service": "payments", "limit": 20}, {"order_id": "ord-2"}]
        self.assertEqual(argument_exact_match_rate(expected, actual), 0.5)

    def test_tool_execution_success_rate(self):
        self.assertAlmostEqual(tool_execution_success_rate([True, False, True]), 2 / 3)

    def test_task_success_rate(self):
        self.assertEqual(task_success_rate([True, True, False]), 2 / 3)

    def test_average_tool_calls(self):
        self.assertEqual(average_tool_calls([0, 1, 3]), 4 / 3)

    def test_average_tool_calls_rejects_negative_counts(self):
        with self.assertRaises(ValueError):
            average_tool_calls([1, -1])

    def test_unauthorized_call_rate(self):
        self.assertEqual(unauthorized_call_rate([True, False, True, False]), 0.5)

    def test_empty_inputs(self):
        self.assertEqual(tool_selection_accuracy([], []), 0.0)
        self.assertEqual(argument_exact_match_rate([], []), 0.0)
        self.assertEqual(tool_execution_success_rate([]), 0.0)
        self.assertEqual(task_success_rate([]), 0.0)
        self.assertEqual(average_tool_calls([]), 0.0)
        self.assertEqual(unauthorized_call_rate([]), 0.0)


if __name__ == "__main__":
    unittest.main()
