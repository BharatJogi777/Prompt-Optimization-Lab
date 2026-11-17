# Module 10 — Production Prompt Optimization Capstone

## Objective

Build a repeatable release process for an LLM application. The capstone combines the engineering practices from Modules 01–09:

- prompt design and versioning
- representative evaluation datasets
- deterministic and model-assisted evaluation
- RAG retrieval and answer-quality evaluation
- agent/tool-use evaluation
- tracing and failure analysis
- release gates, canary rollout, and rollback

The outcome is not a magic prompt optimizer. It is an engineering system that makes changes measurable, reviewable, and reversible.

## 1. Reference architecture

A production optimization platform can be divided into these components:

1. **Application runtime** — API, business workflow, RAG pipeline, or agent.
2. **Prompt registry** — immutable prompt versions and environment aliases.
3. **Model adapter** — provider/local model interface, model and parameter configuration.
4. **Retrieval layer** — parsers, chunkers, embeddings, vector/lexical retrieval, reranker.
5. **Tool layer** — typed application tools and optional MCP clients.
6. **Evaluation service** — offline datasets, metric calculations, regression comparisons.
7. **Observability** — traces, metrics, structured logs, error reporting.
8. **Release controller** — policy checks, approvals, staged rollout, rollback.
9. **Artifact store** — evaluation reports, prompt/model/config identifiers, dataset versions.

Keep responsibilities separate. A prompt registry should not execute tools. An evaluation runner should not have production write permissions. A model should not decide whether its own release passes the security gate.

## 2. Version the complete behavior, not just the prompt

A response can change when any of these change:

- prompt template or system instructions
- model provider, model name, or model revision
- temperature, top-p, maximum output tokens, stop sequences
- tool definitions and tool schema versions
- retrieval embedding model and its version
- chunking strategy, chunk size, overlap, metadata rules
- vector index and search parameters
- hybrid-search weights and reranker version
- context assembly and truncation policy
- application code and policy configuration

Create a release manifest that identifies the full combination. Otherwise, a quality regression may be impossible to reproduce.

Example manifest:

~~~json
{
  "release_id": "support-assistant-2026-01",
  "prompt_id": "support_answer",
  "prompt_version": "2.3.0",
  "model": "llama3.2:3b",
  "temperature": 0.1,
  "retrieval": {
    "embedding_model": "nomic-embed-text",
    "chunker_version": "recursive-v2",
    "top_k": 8,
    "reranker": "disabled"
  },
  "tool_schema_version": "3",
  "application_git_commit": "replace-with-real-commit",
  "evaluation_dataset_version": "support-eval-v5"
}
~~~

This is an illustrative manifest, not a claim that these settings are optimal.

## 3. Separate development, validation, and test data

Use three distinct data roles:

- **Development set:** inspect failures and improve prompts/configuration.
- **Validation set:** compare candidate variants and choose a release candidate.
- **Held-out test set:** estimate final generalization after choices are made.

Keep test labels and examples out of the optimization loop. Version datasets and record their provenance. Remove secrets and unnecessary personal data. Include normal, edge, no-answer, adversarial, and failure scenarios.

A dataset should include expected outcomes, not just inputs. For RAG, store relevant source/chunk IDs and answerability. For agents, store expected tool behavior, arguments, approval expectations, and task acceptance criteria.

## 4. Use a layered evaluation strategy

No single metric captures application quality. Use separate dimensions and define thresholds based on the product's risk.

### Prompt and answer quality

- correctness against reviewed expected answers
- instruction adherence and output-schema validity
- completeness and relevance
- refusal/abstention behavior when evidence is insufficient
- consistency across repeated runs where model output is stochastic

### RAG quality

- retrieval Precision@K, Recall@K, MRR, nDCG
- context relevance and coverage
- answer correctness and groundedness
- citation validity and citation precision
- abstention when the corpus does not support an answer

### Agent quality

- tool-selection and argument accuracy
- execution success and retry rate
- task success rate
- unnecessary tool calls and step count
- authorization/policy violation rate
- correct clarification, approval, and stop behavior

### Operations

- p50/p95 latency
- model and retrieval cost
- token usage
- timeout/error rate
- throughput and concurrency
- trace completeness

Do not average safety violations into a general quality score. A release that improves answer quality but introduces an unauthorized action must fail.

## 5. Deterministic checks before model judges

Run cheap, reproducible checks first:

- JSON/schema validation
- required fields and length constraints
- citation IDs exist in retrieved context
- links/source identifiers resolve to known records
- prohibited tool names are absent
- tool arguments satisfy schema and authorization policy
- no secret patterns are present in output
- maximum tool-call count and step budgets are respected

Use model-based judges only for qualities that cannot be checked deterministically. Calibrate judges against human-reviewed examples, measure judge disagreement, and retain human review for ambiguous or high-impact cases.

## 6. Release gate design

A release gate evaluates a candidate against explicit policy. Typical gate dimensions:

1. **Correctness:** candidate must meet minimum quality.
2. **Non-regression:** candidate must not fall below the baseline by more than an agreed tolerance.
3. **Safety:** policy violations and unauthorized actions must remain zero in the test suite.
4. **Reliability:** schema errors, tool failures, and timeouts remain within limits.
5. **Operations:** latency and cost stay within budgets.
6. **Coverage:** all required evaluation categories have enough examples.
7. **Reproducibility:** manifest, dataset version, and evaluation report are saved.

Thresholds are product-specific. A medical, financial, or infrastructure-changing workflow needs stricter controls than a low-risk text formatter. The included example gate is intentionally simple and deterministic; it is a teaching implementation, not a complete enterprise release controller.

### Baseline comparison

A candidate should not pass solely because it clears an absolute threshold. Compare it to the current production baseline on the same dataset and configuration wherever possible.

For a metric where higher is better:

`delta = candidate - baseline`

For a metric where lower is better (latency, cost, error rate):

`delta = candidate - baseline`

Set metric-specific regression tolerances and keep the direction explicit. Do not compare scores from different dataset versions without documenting the change.

## 7. Experiment protocol

For each experiment:

1. State the hypothesis.
2. Identify the one variable being changed.
3. Pin model, prompt, retrieval, tools, and dataset versions.
4. Run baseline and candidate under comparable conditions.
5. Save raw outputs and traces with privacy controls.
6. Calculate aggregate and category-level metrics.
7. Inspect failures, not only averages.
8. Run held-out tests.
9. Record decision, reviewer, and rationale.

If the model is nondeterministic, use repeated runs or confidence intervals where appropriate. Do not treat tiny score differences on a small dataset as meaningful improvements.

## 8. CI and release pipeline

A sensible pipeline:

~~~text
Pull request
  |
  v
Static checks + unit tests
  |
  v
Prompt/schema validation
  |
  v
Deterministic evaluation
  |
  v
RAG and agent regression suite
  |
  v
Candidate-vs-baseline release gate
  |
  +---- fail ----> report failures; block promotion
  |
  v
Human review / approval when required
  |
  v
Staging deployment
  |
  v
Smoke tests + limited canary
  |
  v
Production promotion
  |
  v
Monitor quality, safety, latency, cost
  |
  +---- regression ----> rollback to known-good manifest
~~~

Do not run destructive or costly live tools in ordinary pull-request tests. Use mocks, sandboxes, and read-only credentials. Keep production credentials out of CI logs and test fixtures.

## 9. Canary rollout and rollback

A canary reduces blast radius. Route a small, controlled share of traffic to the candidate, compare it with the stable release, and monitor:

- correctness/feedback signals
- refusal and escalation rates
- retrieval misses and citation failures
- tool errors and policy denials
- latency, token usage, and cost
- application exceptions

Define rollback triggers before rollout. Examples include a safety incident, sustained error-rate increase, severe latency regression, or a quality metric crossing a pre-agreed threshold.

Rollback should restore the entire known-good manifest, not just the prompt text. Preserve the failed release's traces and artifacts for diagnosis.

## 10. Security, privacy, and governance

- Treat user input, retrieved documents, and tool outputs as untrusted.
- Keep authorization in application/service code.
- Apply tenant isolation to retrieval, caches, traces, and evaluation data.
- Redact sensitive values before logging.
- Restrict who can publish prompts and promote releases.
- Audit prompt edits, tool changes, approvals, and rollbacks.
- Define data retention and deletion propagation.
- Review dependencies and model/provider data handling.
- Use least-privilege credentials and separate read/write capabilities.
- Require human approval for high-impact actions.

Prompt injection defenses are layered controls, not a single clever instruction. A model can be manipulated; tool authorization and output validation must remain outside the model.

## 11. Local capstone lab

This repository contains a small release-gate implementation using only the Python standard library.

Run it from the repository root:

~~~bash
python -m unittest discover -s tests -p "test_release_gate.py" -v
python examples/capstone/run_release_gate.py
~~~

The example reads a candidate metric report and policy thresholds from JSON. It checks minimum quality, baseline regression, and zero-tolerance safety metrics. It does not invoke an LLM, access production systems, deploy software, or automatically promote a release.

Inspect the sample report and deliberately change one value:

- reduce task success below its minimum
- increase unauthorized call rate above zero
- increase latency beyond the allowed regression
- reduce citation validity below its threshold

Run the gate again and observe why promotion is blocked.

## 12. Your final implementation project

Build a support assistant or an internal DevOps investigation assistant. A recommended sequence:

### Phase A — Baseline application

- Implement a simple API and a local model adapter.
- Define a narrow application scope.
- Add structured input/output schemas.
- Record a baseline dataset and baseline metrics.

### Phase B — RAG

- Ingest versioned documents.
- Compare at least two chunking configurations.
- Evaluate embedding/retrieval behavior.
- Add hybrid search and reranking only when measurements justify them.
- Return source identifiers and abstain when evidence is insufficient.

### Phase C — Agent tools

- Add read-only tools first.
- Validate tool schemas and permissions in application code.
- Add step/time budgets and explicit stop conditions.
- Test timeouts, empty results, malformed outputs, and prompt injection.
- Add approval gates before any consequential write action.

### Phase D — Optimization

- Version prompts and configuration.
- Compare candidates on development and validation data.
- Inspect category-level failures.
- Run held-out regression tests.
- Trace representative runs.

### Phase E — Release operations

- Generate a release manifest and evaluation report.
- Apply deterministic release gates.
- Require review for high-risk changes.
- Deploy to staging and run smoke tests.
- Canary, monitor, and practice rollback.

## 13. Capstone acceptance criteria

Your project is complete when:

- [ ] Every release identifies prompt, model, tools, retrieval, application, and dataset versions.
- [ ] Evaluation datasets have development, validation, and held-out test splits.
- [ ] RAG retrieval and answer generation are evaluated separately.
- [ ] Agent tool choice, arguments, execution, and task success are evaluated separately.
- [ ] Deterministic safety/schema checks run before promotion.
- [ ] Candidate results are compared with a baseline.
- [ ] Release thresholds are documented and risk-based.
- [ ] Traces support failure investigation without exposing secrets.
- [ ] High-impact actions require authorization and approval.
- [ ] A canary and rollback procedure has been tested.
- [ ] Evaluation reports and release decisions are reproducible.

## 14. After completing this curriculum

You should now be able to approach prompt optimization as an engineering discipline:

- Define quality before changing prompts.
- Build representative evaluation datasets.
- Diagnose failures at the correct pipeline stage.
- Optimize prompts and LM programs systematically.
- Measure RAG and agent behavior independently.
- Trace production executions.
- Release changes through measurable gates.
- Roll back safely when behavior regresses.

Mastery comes from building, measuring, debugging, and operating a real application—not from memorizing prompt templates. Use the capstone as a project you can demonstrate in a technical interview and continue improving with real, reviewed evaluation data.
