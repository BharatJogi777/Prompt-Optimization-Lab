"""Evaluate synthetic normalized agent traces from the repository root."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent_eval.metrics import (
    argument_exact_match_rate,
    average_tool_calls,
    task_success_rate,
    tool_execution_success_rate,
    tool_selection_accuracy,
    unauthorized_call_rate,
)


def main() -> None:
    dataset_path = Path(__file__).with_name("evaluation_dataset.json")
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    cases = dataset["cases"]

    expected_tools = [case["expected_tool"] for case in cases]
    actual_tools = [case["actual_tool"] for case in cases]
    expected_arguments = [case["expected_arguments"] for case in cases]
    actual_arguments = [case["actual_arguments"] for case in cases]
    execution_outcomes = [case["tool_succeeded"] for case in cases if case["actual_tool"]]
    authorization = [case["authorized"] for case in cases if case["actual_tool"]]

    print(f"Evaluating {len(cases)} synthetic agent cases\n")
    for case in cases:
        print(f"{case['case_id']}: {case['request']}")
        print(
            f"  expected tool={case['expected_tool']!r}; "
            f"actual tool={case['actual_tool']!r}; "
            f"task success={case['task_succeeded']}"
        )

    print("\nAggregate metrics")
    print(f"  Tool selection accuracy:      {tool_selection_accuracy(expected_tools, actual_tools):.3f}")
    print(f"  Argument exact-match rate:    {argument_exact_match_rate(expected_arguments, actual_arguments):.3f}")
    print(f"  Tool execution success rate:  {tool_execution_success_rate(execution_outcomes):.3f}")
    print(f"  Task success rate:            {task_success_rate([c['task_succeeded'] for c in cases]):.3f}")
    print(f"  Average tool calls per task:  {average_tool_calls([c['tool_call_count'] for c in cases]):.3f}")
    print(f"  Unauthorized call rate:       {unauthorized_call_rate(authorization):.3f}")

    print(
        "\nNote: synthetic records demonstrate metric calculations; "
        "they are not measurements of a live agent."
    )


if __name__ == "__main__":
    main()
