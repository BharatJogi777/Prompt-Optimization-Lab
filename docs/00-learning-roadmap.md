# 00 — Complete Prompt Optimization Roadmap

## What are we building?
A prompt optimization system answers four engineering questions:
1. Does this prompt solve the task?
2. How reliably does it solve the task across representative inputs?
3. Is a candidate measurably better than the baseline?
4. Can we release the change without unacceptable regressions?

## End-to-end workflow
~~~text
Task requirements
  -> Baseline prompt and model configuration
  -> Representative evaluation dataset
  -> Baseline run and failure analysis
  -> Candidate prompt/program variants
  -> Evaluation on identical data
  -> Human review and held-out test
  -> Version, release, trace, and monitor
~~~

## Phase 1 — Prompt engineering foundations
Study message roles, task definition, context, constraints, zero-shot and few-shot prompting, delimiters, untrusted input, structured output, and model parameters.
Deliverable: a prompt library with documented inputs, outputs, and failure behavior.

## Phase 2 — Evaluation fundamentals
Study representative datasets, golden answers, exact match, precision, recall, F1, rubric-based evaluation, model-assisted judges, human review, baselines, and regression testing.
Deliverable: a repeatable evaluation runner.

## Phase 3 — Promptfoo
Study providers, prompt variants, test cases, assertions, grading, local Ollama configuration, adversarial tests, and regression suites.
Deliverable: compare prompts using a repeatable test suite.

## Phase 4 — Manual optimization
Study failure taxonomies, instruction clarity, constraints, example selection, output schemas, decomposition, context ordering, token budgets, ablation tests, and controlled experiments.
Deliverable: an experiment log connecting each prompt change to an observed failure.

## Phase 5 — DSPy
Study signatures, modules, predictors, metrics, demonstrations, optimizers, compilation, multi-step programs, and held-out evaluation. Optimizer APIs can vary by DSPy version; verify against the installed release.
Deliverable: an optimized DSPy program with a test report.

## Phase 6 — Prompt management
Study templates, variables, versioning, immutable releases, environment promotion, rollback, and reproducibility.
Deliverable: a versioned prompt release process.

## Phase 7 — Observability
Study traces, spans, generations, latency, token usage, errors, safe logging, trace sampling, and evaluation from production traces.
Deliverable: diagnose a poor response from a trace.

## Phase 8 — RAG optimization
Separate retrieval quality from generation quality. Study relevance, evidence coverage, groundedness, citation correctness, abstention, query rewriting, context formatting, and token budgets.
Deliverable: evaluate a RAG pipeline with separate retrieval and answer metrics.

## Phase 9 — Agent optimization
Study tool descriptions, argument schemas, tool selection, planning, stopping conditions, loop prevention, state, error recovery, task completion, and safety metrics.
Deliverable: evaluate an agent on fixed tasks, including tool failures.

## Phase 10 — Production capstone
Build a service that loads versioned prompts, calls a configured model, runs offline evaluations, compares candidates with a baseline, enforces release gates, records safe traces, supports rollback, and includes tests and documentation.

## Critical concept: avoid overfitting
Keep optimization examples separate from held-out test examples. If an optimizer repeatedly sees the test set, it can overfit to it and the test score becomes misleading.

## Completion checklist
- [ ] Design clear prompts and output contracts.
- [ ] Build representative evaluation datasets.
- [ ] Define task-specific metrics.
- [ ] Compare prompts with Promptfoo.
- [ ] Optimize LM programs with DSPy.
- [ ] Explain overfitting and held-out testing.
- [ ] Version and roll back prompts.
- [ ] Trace and diagnose production failures.
- [ ] Evaluate RAG and agents independently.
- [ ] Release changes using measurable gates.