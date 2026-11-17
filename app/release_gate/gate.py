"""Evaluate candidate metrics against a JSON-compatible release policy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def evaluate_release(
    baseline: Mapping[str, Any],
    candidate: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a pass/fail decision and human-readable reasons.

    Policy format:
      minimum: metric -> minimum acceptable value (higher is better)
      maximum: metric -> maximum acceptable value (lower is better)
      max_regression: metric -> maximum allowed candidate-baseline delta
                      for lower-is-better metrics.
      zero_tolerance: metric -> metric must equal zero.

    The caller is responsible for supplying validated, comparable metrics
    from the same evaluation dataset and measurement procedure.
    """
    failures: list[str] = []
    checks: list[dict[str, Any]] = []

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": passed, "detail": detail})
        if not passed:
            failures.append(f"{name}: {detail}")

    for metric, threshold in policy.get("minimum", {}).items():
        if metric not in candidate:
            record(f"minimum:{metric}", False, "candidate metric is missing")
            continue
        value = float(candidate[metric])
        record(
            f"minimum:{metric}",
            value >= float(threshold),
            f"value={value}, required>={threshold}",
        )

    for metric, threshold in policy.get("maximum", {}).items():
        if metric not in candidate:
            record(f"maximum:{metric}", False, "candidate metric is missing")
            continue
        value = float(candidate[metric])
        record(
            f"maximum:{metric}",
            value <= float(threshold),
            f"value={value}, required<={threshold}",
        )

    for metric, threshold in policy.get("zero_tolerance", {}).items():
        if metric not in candidate:
            record(f"zero_tolerance:{metric}", False, "candidate metric is missing")
            continue
        value = float(candidate[metric])
        record(
            f"zero_tolerance:{metric}",
            value == 0.0,
            f"value={value}, required=0",
        )

    for metric, allowed_delta in policy.get("max_regression", {}).items():
        if metric not in baseline or metric not in candidate:
            record(f"max_regression:{metric}", False, "baseline or candidate metric is missing")
            continue
        delta = float(candidate[metric]) - float(baseline[metric])
        record(
            f"max_regression:{metric}",
            delta <= float(allowed_delta),
            f"candidate-baseline delta={delta}, allowed<={allowed_delta}",
        )

    return {
        "passed": not failures,
        "checks": checks,
        "failures": failures,
    }
