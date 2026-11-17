# Production capstone release-gate lab

This dependency-free lab evaluates a synthetic candidate report against a JSON policy. It does not call an LLM, deploy an application, or promote a release.

From the repository root:

~~~bash
python -m unittest discover -s tests -p "test_release_gate.py" -v
python examples/capstone/run_release_gate.py
~~~

## Experiment

Edit candidate_metrics.json and try:

- lowering task_success_rate below the minimum
- increasing unauthorized_call_rate above zero
- increasing p95_latency_ms beyond the absolute maximum
- increasing latency beyond the allowed baseline regression
- removing a required metric

The gate should block a candidate when any configured check fails.

## Important limitations

- The policy values are illustrative, not universal production thresholds.
- The caller must ensure baseline and candidate metrics use comparable datasets and measurement procedures.
- The example does not calculate metrics from raw traces; it consumes an already generated report.
- A real release controller needs signed/versioned artifacts, identity and approval checks, audit storage, canary orchestration, monitoring, and rollback automation.
