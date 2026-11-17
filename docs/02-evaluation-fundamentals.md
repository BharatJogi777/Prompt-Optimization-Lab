# 02 — Prompt Evaluation Fundamentals

## Why evaluation comes before optimization
If Prompt A succeeds on one example and Prompt B succeeds on another, you cannot determine which is better without a defined task, representative inputs, acceptable outputs, and a scoring method. Prompt optimization without evaluation is guesswork.

## 1. Evaluation loop
~~~text
Define task and failure costs
  -> Create representative dataset
  -> Choose metrics and thresholds
  -> Run baseline prompt
  -> Inspect individual failures
  -> Change one thing
  -> Re-run the same evaluation
  -> Compare, review, and decide
~~~

## 2. Dataset design
A test case should be reproducible. JSON Lines is convenient:
~~~json
{"id":"sentiment-001","input":"I love this product.","expected":"positive","category":"clear-positive"}
{"id":"sentiment-002","input":"The package arrived broken.","expected":"negative","category":"clear-negative"}
{"id":"sentiment-003","input":"The package arrived today.","expected":"neutral","category":"neutral"}
{"id":"sentiment-004","input":"It is not bad, but not great either.","expected":"neutral","category":"ambiguous"}
~~~
Include normal, boundary, ambiguous, empty, malformed, long, adversarial, and missing-evidence cases where relevant. Use synthetic or authorized data only.

## 3. Split the data
- Optimization/development set: inspect failures and improve the prompt.
- Validation set: compare candidate choices during development.
- Held-out test set: final, less-biased measurement.

Repeatedly optimizing against the held-out set causes overfitting. Keep it separate.

## 4. Metrics
Choose metrics based on the task.

Accuracy for fixed labels:
~~~text
accuracy = correct_predictions / total_predictions
~~~

Precision and recall:
~~~text
precision = TP / (TP + FP)
recall    = TP / (TP + FN)
~~~
Precision asks how many predicted positives were correct. Recall asks how many actual positives were found.

F1:
~~~text
F1 = 2 * precision * recall / (precision + recall)
~~~
F1 balances precision and recall. It may be unsuitable when false-positive and false-negative costs differ substantially.

For structured output, measure parse success, schema validity, required-field presence, and value constraints.

For RAG, measure retrieval relevance, evidence coverage, answer correctness, groundedness, citation correctness, and abstention when evidence is missing. Keep retrieval and generation metrics separate.

For agents, measure task completion, tool selection, argument correctness, unnecessary calls, safe recovery after tool errors, and loop/stopping failures.

## 5. Model-assisted evaluation
An LLM judge can score nuanced outputs against a rubric, but introduces bias and variance. Define observable criteria, calibrate against human-reviewed examples, keep judge versions fixed during comparisons, and inspect disagreements. A judge score is not objective ground truth.

## 6. Baselines and regression
Record a baseline before changing anything.

| Version | Accuracy | Valid output | Notes |
|---|---:|---:|---|
| baseline-v1 | 0.80 | 0.90 | Initial prompt |
| candidate-v2 | 0.87 | 0.97 | Added label definitions |
| candidate-v3 | 0.83 | 0.97 | Overly restrictive rule |

These figures are illustrative only. Inspect per-category scores; an average can hide a serious regression.

## 7. Experiment record
Record task name, prompt version/hash, model and parameters, dataset and evaluator versions, timestamp, per-example outputs and scores with privacy controls, aggregate metrics, and known limitations.

## 8. Exercises
1. Create 20 synthetic sentiment examples across four categories.
2. Define exact-match accuracy.
3. Run a baseline and calculate its score.
4. Group failures by category.
5. Change one prompt feature and rerun.
6. Keep five unseen examples for a held-out test.
7. Explain improvements and regressions.

## Production release gate
Define release conditions before the experiment: no critical safety regression, structured-output validity above a threshold, target metric improvement on validation data, acceptable latency/token usage, human review for high-impact changes, and a successful held-out evaluation.

## Key takeaway
Evaluation turns prompt improvement from subjective editing into measurable engineering. Dataset quality and metric choice determine whether the result means anything.