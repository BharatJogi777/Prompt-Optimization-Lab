# Agent evaluation example

This example evaluates synthetic, normalized agent traces. It is independent of an LLM framework and MCP server so the evaluation definitions can be understood and tested first.

## Run

From the repository root:

~~~bash
python -m unittest discover -s tests -p "test_agent_metrics.py" -v
python examples/agents/evaluate_agent_runs.py
~~~

No API key or third-party dependency is required.

## Files

- evaluation_dataset.json: synthetic expected decisions and observed outcomes.
- evaluate_agent_runs.py: calculates aggregate metrics.
- app/agent_eval/metrics.py: reusable evaluation functions.
- tests/test_agent_metrics.py: deterministic unit tests.

## Metric interpretation

- Tool selection accuracy includes cases where no tool should be called.
- Argument exact-match rate compares complete mappings.
- Tool execution success rate considers attempted calls only.
- Task success rate must be based on an authoritative completion condition, not the model's final claim.
- Average tool calls per task measures efficiency but does not indicate quality on its own.
- Unauthorized call rate measures the fraction of attempted calls that were unauthorized. It should be zero in a correctly enforced system.

## Connect to your own agent

Export one normalized record per evaluation case. Keep expected labels independent of the model. Record actual tool calls, validated arguments, execution status, authorization result, call count, and final verified task status.

For multiple tool calls per task, extend the schema to represent an ordered list of calls and evaluate each decision separately. The compact example uses one expected/observed tool decision per case for clarity.

These metrics do not replace human review, adversarial testing, or production authorization controls.
