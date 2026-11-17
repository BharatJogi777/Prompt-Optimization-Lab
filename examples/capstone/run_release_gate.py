"""Run the local deterministic release-gate example."""

import json
from pathlib import Path

from app.release_gate.gate import evaluate_release

ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    report = load_json(ROOT / "examples" / "capstone" / "candidate_metrics.json")
    policy = load_json(ROOT / "config" / "release-gate.json")
    result = evaluate_release(report["baseline"], report["candidate"], policy)

    print("RELEASE GATE:", "PASS" if result["passed"] else "BLOCKED")
    for check in result["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        print(f"[{status}] {check['check']} — {check['detail']}")

    if result["failures"]:
        print("\nPromotion blocked:")
        for failure in result["failures"]:
            print(f"- {failure}")


if __name__ == "__main__":
    main()
