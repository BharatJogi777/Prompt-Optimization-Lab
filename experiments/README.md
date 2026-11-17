# Prompt Experiments

Store experiment reports here. Use one Markdown file per experiment.

Recommended naming:

~~~text
YYYY-MM-DD_<task>_<experiment-id>.md
~~~

Copy this template:

~~~markdown
# Experiment: <ID>

## Objective
What task behavior are we trying to improve?

## Baseline
- Prompt version:
- Model and version:
- Parameters:
- Dataset version:
- Evaluator version:

## Failure analysis
Which failure category is the priority? Include example IDs, not sensitive raw data.

## Hypothesis
What single change do we expect to improve which metric, and what regression might it cause?

## Change
Describe exactly what changed. Link the candidate prompt version.

## Results
| Metric | Baseline | Candidate |
|---|---:|---:|
| Primary metric | | |
| Output validity | | |
| Critical-case pass rate | | |
| Median latency | | |

## Error analysis
Which cases improved? Which regressed? Why?

## Held-out result
Record separately. Do not tune against this set and reuse its score as an unbiased final result.

## Decision
Keep / revise / reject.

## Limitations
What does this experiment not establish?
~~~

Do not commit secrets, private user inputs, or sensitive production traces.
