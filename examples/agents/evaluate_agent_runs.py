"""Evaluate a small synthetic set of agent tool-call traces."""

import json
from pathlib import Path

from app.agent_eval.metrics import evaluate_agent_runs, evaluate_run


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "examples" / "agents" / "evaluation_dataset.json"


def main() -> None:
    runs = json.loads(DATASET.read_text(encoding="utf-8"))
    print("Per-case results")
    for run in runs:
        result = evaluate_run(
            expected_calls=run["expected_calls"],
            actual_calls=run["actual_calls"],
            task_success=run["task_success"],
        )
        print(
            f'{run["case_id"]}: precision={result["tool_precision"]:.2f}, '
            f'recall={result["tool_recall"]:.2f}, '
            f'F1={result["tool_f1"]:.2f}, '
            f'task_success={result["task_success"]:.0f}'
        )

    print("\nMacro-averaged summary")
    summary = evaluate_agent_runs(runs)
    for key, value in summary.items():
        print(f"{key}: {value:.3f}" if isinstance(value, float) else f"{key}: {value}")


if __name__ == "__main__":
    main()
