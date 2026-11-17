# Module 09 — Production Agent and Tool-Calling Optimization

## Learning outcomes

By the end of this module, you should be able to explain the agent loop, design safe tool contracts, evaluate tool selection and arguments, test multi-step workflows, connect MCP tools, and operate agents with bounded autonomy.

The lab is local-first. Its evaluation code uses only the Python standard library; it does not call an LLM.

## 1. What are we optimizing?

A basic LLM call maps input text to output text. An agentic application has a larger execution path:

User request → state/context → model decision → tool validation → tool execution → observation → next decision → final response.

An agent may repeat the decision/execution cycle. It can also stop, ask the user a question, or request approval.

A useful production mental model:

- **LLM:** proposes a plan, selects among actions, interprets observations, and writes a response.
- **Application code:** owns authorization, validation, state transitions, retries, budgets, and side effects.
- **Tools:** perform explicit operations such as searching logs, reading a database, or creating a ticket.
- **MCP:** standardizes how an MCP client discovers and invokes tools exposed by MCP servers. It does not provide planning, authorization policy, or safe business logic.

A model suggestion is untrusted input until application code validates it. Never delegate security decisions to a prompt.

### Agent versus workflow

Use a deterministic workflow when steps and branches are known in advance. Use an agent when the system genuinely needs to choose among actions based on observations.

| Problem | Better starting point | Why |
|---|---|---|
| Validate an order, charge payment, send receipt | Workflow | Steps are known and side effects must be predictable |
| Investigate an unfamiliar incident using read-only tools | Bounded agent | Next investigation step depends on evidence |
| Process thousands of records identically | Batch worker | An LLM loop adds cost and uncertainty |
| Draft a support response from retrieved policy | RAG + workflow | Autonomy may not be needed |

A production design can combine both: an agent proposes an investigation plan, while deterministic services execute approved operations.

## 2. The agent loop

A minimal loop has these stages:

1. Receive a request and create a run ID.
2. Load only context and tools this user is authorized to access.
3. Ask the model for a structured decision.
4. Validate the decision against an application-owned schema and policy.
5. Execute the tool with a timeout and resource limit.
6. Convert the result into a bounded observation.
7. Append the observation to run state.
8. Continue, ask for clarification, request approval, or stop.
9. Produce a final response with evidence and explicit status.

The model may suggest a tool call, but it must not directly execute arbitrary code. The application owns the loop and dispatcher.

### Explicit run state

Keep fields such as run ID, tenant/user identity, original request, current objective, completed steps, tool calls/outcomes, evidence references, remaining step/time/token budget, approval state, and terminal status.

Persist only what is needed. Treat tool outputs and retrieved documents as untrusted data; instructions inside them must not override system policy.

### Stop conditions

Enforce stop conditions in code:

- task completed and acceptance criteria satisfied
- maximum steps reached
- time or token budget exhausted
- repeated identical tool call detected
- unrecoverable tool error
- authorization denied
- user clarification required
- human approval pending

A loop without explicit bounds can become expensive or run indefinitely.

## 3. Tool contracts: the critical boundary

A tool is an API contract, not a paragraph in a prompt. A good tool has one responsibility, a stable name and description, typed/constrained input, predictable output, explicit error semantics, timeout/resource limits, external authorization, and defined idempotency behavior for writes.

Prefer a narrow search_logs(service, start_time, end_time, severity) tool over a generic run_shell(command) tool.

### Validate every argument

For every call:

1. Check that the tool is in the allow-list for this run.
2. Validate required fields, types, lengths, and allowed values.
3. Validate tenant and resource ownership using trusted identity, not model-supplied IDs.
4. Enforce limits such as maximum date range, result count, and payload size.
5. Apply authorization and approval policy.
6. Execute with a timeout.
7. Normalize errors into safe observations.
8. Record an audit event without leaking secrets.

Structured output reduces parsing ambiguity; it does not prove that an argument is safe or authorized.

### Read and write tools

Classify tools by risk:

- **Read-only:** search logs, fetch a document, inspect a deployment.
- **Reversible write:** create a draft or add a temporary label.
- **Consequential write:** deploy code, refund money, delete data, send external messages.

Use stronger controls as impact increases. Consequential actions should usually require explicit approval, an auditable identity, and an idempotency key.

## 4. Agent evaluation: measure each stage

A single score such as “the answer looks good” hides the cause of failure. Build a dataset with expected actions and task outcomes.

| Metric | What it tells you |
|---|---|
| Tool selection accuracy | Did the agent choose the expected tool? |
| Argument accuracy | Were required argument values correct? |
| Tool-call precision | How many emitted calls were expected/useful? |
| Tool-call recall | How many expected calls were emitted? |
| Execution success rate | How many attempted calls completed successfully? |
| Task success rate | Did the run satisfy acceptance criteria? |
| Step count | How many decisions/calls were needed? |
| Retry rate | How often did execution need retrying? |
| Escalation rate | How often was human intervention needed? |
| Policy violation rate | Did it attempt an unauthorized/prohibited action? |

For one expected call set:

- precision = correct emitted calls / emitted calls
- recall = correct emitted calls / expected calls
- F1 = harmonic mean of precision and recall

Metrics must be interpreted together. An agent that never calls tools may have zero tool errors but also zero task success. An agent that completes tasks with too many unnecessary calls may be expensive and risky.

For multiple calls with repeated tools or ordered dependencies, compare call sequences or use task-specific matching. A set-based metric alone cannot detect ordering errors.

### Task success must be independently judged

Define observable acceptance criteria before experiments. Examples:

- Correct service identified from supplied evidence.
- Every factual claim references a valid log or document.
- No production mutation was attempted.
- The run stops when evidence is insufficient.
- A refund is not submitted without required approval.

Avoid using the same LLM prompt both to generate an answer and as the only judge of correctness. Use deterministic checks where possible and human review for ambiguous/high-impact cases.

## 5. Build an evaluation dataset

Store one record per scenario:

- stable case ID
- user request
- available tools
- expected tool calls, including required arguments
- task acceptance criteria
- whether the case is answerable
- expected escalation/approval behavior
- risk category

Include normal, negative, and adversarial cases:

1. Normal request with one obvious tool.
2. Request requiring multiple tools in a specific order.
3. Tool returns no results.
4. Tool times out.
5. Tool returns malformed data.
6. User requests an action they are not authorized to perform.
7. User asks for a prohibited action.
8. Tool output contains prompt-injection instructions.
9. Request is ambiguous and needs clarification.
10. Agent reaches its step budget without enough evidence.

Keep a held-out test set. Do not optimize prompts against every test example; that creates evaluation leakage.

## 6. Tool failures, retries, and idempotency

A timeout does not prove that a write operation failed. The remote service may have completed the operation while the response was lost.

For read-only operations, a bounded retry with exponential backoff and jitter is often appropriate. For writes, use an idempotency key or query operation status before retrying.

Distinguish:

- validation error: do not retry unchanged arguments
- authorization error: do not retry
- rate limit: retry only according to service guidance
- transient network error: bounded retry
- timeout with unknown write outcome: reconcile before retry
- permanent tool error: report or escalate

Never let the LLM decide to retry a financial or destructive action without application-enforced idempotency and policy.

## 7. MCP integration

MCP standardizes client/server communication for exposing tools and other context capabilities. A common architecture is:

Agent runtime → MCP client → MCP server → domain service.

The agent runtime decides whether a tool is useful. The MCP client handles protocol communication. The MCP server exposes a tool contract and calls the underlying service.

Production considerations:

- use explicit server configuration and tool allow-lists
- authenticate and authorize at the server/domain-service boundary
- validate inputs again on the server
- isolate servers by trust boundary and capability
- set timeouts and response-size limits
- log tool name, duration, outcome, and correlation ID
- avoid giving credentials or unrestricted filesystem access to the model
- version tool schemas and test compatibility
- treat tool descriptions and results as untrusted data

Connecting an MCP server does not make its tools safe. MCP is a protocol boundary; authorization and business rules remain application responsibilities.

## 8. Agent prompt optimization workflow

1. Establish a baseline prompt and model configuration.
2. Run a representative dataset and save every trace.
3. Categorize failures: wrong tool, wrong arguments, missing call, unnecessary call, poor interpretation, unsafe action, premature stop.
4. Change one instruction or example.
5. Re-run the exact same dataset.
6. Compare aggregate and per-category metrics.
7. Run a held-out regression set.
8. Review high-risk cases manually.
9. Promote only if quality improves without unacceptable latency, cost, or safety regressions.

Useful prompt components include objective and boundaries, tool descriptions, selection criteria, output schema, missing-information behavior, stop/clarification conditions, and evidence requirements.

Do not put secrets, authorization policy, or safety-critical enforcement only in the prompt.

Example experiment:

| Version | Tool accuracy | Task success | Avg. calls | Policy violations |
|---|---:|---:|---:|---:|
| Baseline | 0.78 | 0.65 | 3.8 | 0 |
| Variant A | 0.86 | 0.76 | 3.1 | 0 |
| Variant B | 0.91 | 0.72 | 5.9 | 1 |

Variant B has better tool accuracy but worse task success and a policy violation. It should not be promoted.

## 9. Observability and trace design

Trace one complete agent run and create child spans/events for input/context preparation, model decision, tool validation, tool execution, observation processing, final response, and approval/escalation.

Capture metadata such as model/version, prompt version, tool name/schema version, step index, latency, retry count, token usage when available, and outcome category.

Do not indiscriminately capture raw prompts, customer data, credentials, or tool payloads. Redact or hash sensitive fields and define retention/access controls.

A useful trace answers: what did the model propose, what did the application allow, what did the tool actually do, and why did the run stop?

## 10. Production architecture

A practical service boundary:

- **API layer:** authentication, request validation, rate limits.
- **Agent orchestrator:** run state, step loop, budgets, stop conditions.
- **Model adapter:** provider/local model abstraction and structured outputs.
- **Tool registry:** allowed tools and schemas.
- **Tool adapters/MCP clients:** protocol and service integration.
- **Policy layer:** authorization, approval, risk checks.
- **Persistence:** run state, audit records, evaluation traces.
- **Observability:** logs, metrics, traces, alerts.
- **Evaluation service:** offline datasets, regression tests, release gates.

Keep the agent runtime separate from domain services. The agent requests actions through narrow interfaces; domain services remain authoritative for business rules.

Operational controls include per-user/tenant quotas, maximum steps/time/tokens, tool-level timeouts, concurrency limits, circuit breakers, bounded retries, idempotency, audit trails, approval workflows, kill switches, version pinning, canary rollout, rollback, tenant isolation, and data deletion propagation.

## 11. Local lab

The repository includes a dependency-free evaluator:

~~~bash
python -m unittest discover -s tests -p "test_agent_metrics.py" -v
python examples/agents/evaluate_agent_runs.py
~~~

It calculates tool-call precision, recall, F1, and task success over a synthetic dataset. It does not run an LLM, connect to MCP, or execute tools. Its purpose is to make evaluation semantics concrete before connecting a real agent.

### Metric semantics

- Calls are matched exactly by tool name and complete argument mapping.
- Calls are treated as a multiset; duplicates count separately.
- Precision, recall, and F1 are macro-averaged per run by the aggregate helper.
- Empty expected and actual call sets receive precision and recall of 1.0: no call was the correct action.
- An empty expected set with actual calls receives precision 0.0 and recall 0.0.
- Task success is a separately supplied label; it is not inferred from tool-call matching.

This is a strict teaching baseline. Real agents need ordered-sequence checks, partial argument matching, execution outcomes, policy checks, latency/cost, and independently verified task acceptance criteria.

### Exercises

1. Add a case where the agent emits an unnecessary tool call.
2. Add a multi-tool case and explain why order matters.
3. Add a no-answer case where the correct behavior is to stop and ask a question.
4. Add an execution timeout field and compute execution success separately from task success.
5. Design an approval-required tool and specify which checks must happen outside the LLM.
6. Connect a read-only MCP tool and record a trace for one run.
7. Create a held-out regression dataset and compare two prompt versions.

### Completion checklist

- [ ] I can explain every stage of the agent loop.
- [ ] Tool contracts are narrow and arguments are validated.
- [ ] Authorization is enforced in application/service code.
- [ ] The run has explicit step, time, and token budgets.
- [ ] Retries distinguish read operations from writes.
- [ ] Evaluation separates tool decisions from task outcomes.
- [ ] No-answer, adversarial, and failure cases are included.
- [ ] Traces expose failure causes without leaking secrets.
- [ ] High-impact actions require approval and auditability.

## 12. What comes next?

Module 10 is the production capstone. It combines prompt versioning, offline evaluation, RAG, agent/tool evaluation, tracing, release gates, and rollback into one coherent engineering workflow.
