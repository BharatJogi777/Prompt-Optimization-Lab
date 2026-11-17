"""Simple deterministic metrics for normalized agent evaluation records."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def _average(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def tool_selection_accuracy(expected_tools: Sequence[str | None], actual_tools: Sequence[str | None]) -> float:
    """Fraction of cases where the selected tool exactly matches expectation.

    None represents a case where no tool should be called.
    """
    if len(expected_tools) != len(actual_tools):
        raise ValueError("expected_tools and actual_tools must have equal length")
    if not expected_tools:
        return 0.0
    return _average([float(expected == actual) for expected, actual in zip(expected_tools, actual_tools)])


def argument_exact_match_rate(expected: Sequence[Mapping[str, Any]], actual: Sequence[Mapping[str, Any]]) -> float:
    """Fraction of tool calls whose argument mappings exactly match."""
    if len(expected) != len(actual):
        raise ValueError("expected and actual argument lists must have equal length")
    if not expected:
        return 0.0
    return _average([float(dict(left) == dict(right)) for left, right in zip(expected, actual)])


def tool_execution_success_rate(outcomes: Sequence[bool]) -> float:
    """Fraction of attempted tool executions that succeeded."""
    if not outcomes:
        return 0.0
    return _average([float(outcome) for outcome in outcomes])


def task_success_rate(outcomes: Sequence[bool]) -> float:
    """Fraction of evaluated tasks that met their authoritative success condition."""
    if not outcomes:
        return 0.0
    return _average([float(outcome) for outcome in outcomes])


def average_tool_calls(call_counts: Sequence[int]) -> float:
    """Average number of tool calls per task."""
    if any(count < 0 for count in call_counts):
        raise ValueError("tool call counts cannot be negative")
    return _average([float(count) for count in call_counts])


def unauthorized_call_rate(authorization_decisions: Sequence[bool]) -> float:
    """Fraction of attempted calls that were unauthorized."""
    if not authorization_decisions:
        return 0.0
    return _average([float(not allowed) for allowed in authorization_decisions])
