"""Evaluate synthetic, normalized agent tool-use traces."""

import json
from pathlib import Path

from app.agent_eval.metrics import (
    argument_exact_match_rate,
    average_tool_calls,
    task_success_rate,
    tool_execution_success_rate,
    tool_selection_accuracy,
    unauthorized_call_rate,
)

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "examples" / "agents" / "evaluation_dataset.json"


def main() -> None:
    payload = json.loads(DATASET.read_text(encoding="utf-8"))
    cases = payload["cases"]

    summary = {
        "cases": len(cases),
        "tool_selection_accuracy": tool_selection_accuracy(
            [case["expected_tool"] for case in cases],
            [case["actual_tool"] for case in cases],
        ),
        "argument_exact_match_rate": argument_exact_match_rate(
            [case["expected_arguments"] for case in cases],
            [case["actual_arguments"] for case in cases],
        ),
        "tool_execution_success_rate": tool_execution_success_rate(
            [case["tool_succeeded"] for case in cases if case["actual_tool"] is not None]
        ),
        "task_success_rate": task_success_rate(
            [case["task_succeeded"] for case in cases]
        ),
        "average_tool_calls": average_tool_calls(
            [case["tool_call_count"] for case in cases]
        ),
        "unauthorized_call_rate": unauthorized_call_rate(
            [
                case["authorized"]
                for case in cases
                if case["actual_tool"] is not None
            ]
        ),
    }

    for name, value in summary.items():
        print(f"{name}: {value:.3f}" if isinstance(value, float) else f"{name}: {value}")


if __name__ == "__main__":
    main()
