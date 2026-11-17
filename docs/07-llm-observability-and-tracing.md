# Module 07 — LLM Observability and Tracing

## Learning outcomes

After this module, you should be able to:

1. Explain why normal backend logs are insufficient for debugging LLM applications.
2. Distinguish traces, spans, generations, events, and scores.
3. Instrument a local Ollama call with Langfuse.
4. Represent a RAG or agent request as a parent-child trace.
5. Track latency, model identity, token usage, errors, and prompt versions.
6. Avoid leaking sensitive user data into observability systems.
7. Use traces to identify whether failures originate in retrieval, generation, tools, or validation.
8. Design a production observability strategy that supports evaluation and incident response.

---

## 1. Why LLM observability is different

In a normal backend, an HTTP request may call a database and another service. Logs and distributed traces help identify the slow or failing dependency.

An LLM request adds more uncertainty:

- the same input may produce different outputs;
- a syntactically valid answer may be factually wrong;
- a model may ignore part of the instruction;
- retrieval may return irrelevant documents;
- a tool-using agent may select the wrong tool or repeat calls;
- model latency and token usage can vary;
- a prompt change can cause a regression without any code exception.

A log such as "POST /ask returned 200" tells you almost nothing about answer quality.

LLM observability must connect the complete workflow: request, prompt version, retrieval, context, model call, tool execution, validation, and final response.

## 2. Core concepts

### Trace

A trace represents one end-to-end operation, such as one user question sent to a RAG endpoint.

### Observation

Langfuse uses observations as the general concept for recorded work. An observation may represent a span, generation, tool, retriever, agent, evaluator, or another operation type.

### Span

A span represents a unit of work and its duration. Examples include query rewriting, retrieval, reranking, or output validation.

### Generation

A generation represents a model invocation. Record the model identity, input, output, and usage when available.

### Event

An event records something that happened at a point in a workflow, such as a retry or a cache hit. It does not necessarily represent a duration.

### Score

A score records an evaluation or feedback signal, such as relevance, correctness, groundedness, or user feedback.

## 3. Trace hierarchy

Consider a RAG application:

~~~text
Trace: POST /ask
|
+-- Span: validate-request
|
+-- Span: retrieve-documents
|   |
|   +-- Span: vector-search
|   +-- Span: rerank-results
|
+-- Generation: answer-generation
|
+-- Span: validate-citations
|
+-- Span: build-response
~~~

For an agent:

~~~text
Trace: investigate-incident
|
+-- Agent: investigation-agent
|   |
|   +-- Generation: plan-next-step
|   |
|   +-- Tool: search_logs
|   |
|   +-- Generation: interpret-log-results
|   |
|   +-- Tool: query_metrics
|   |
|   +-- Generation: final-summary
|
+-- Span: validate-final-report
~~~

The parent-child relationship makes it possible to understand both total request time and the time spent in individual operations.

## 4. Metrics worth tracking

| Area | Useful measurements |
|---|---|
| Reliability | request success rate, timeout rate, exception rate |
| Latency | end-to-end latency, retrieval latency, model latency, tool latency |
| Model usage | input tokens, output tokens, model identifier, calls per request |
| Cost | estimated cost per model call and per completed task |
| Retrieval | number of candidates, relevant-document rate, context size |
| Generation quality | correctness, groundedness, schema validity, citation correctness |
| Agent behavior | tool selection, tool errors, steps per task, repeated actions, completion rate |
| User experience | feedback, retry rate, abandonment, accepted answer rate |

Do not collapse all quality into one score. A RAG system can have excellent retrieval and poor generation, or poor retrieval and a fluent but unsupported answer.

## 5. Set up Langfuse

Langfuse can be used as a hosted service or self-hosted. For a first learning exercise, the hosted service avoids running additional infrastructure on a laptop. If you self-host, use the official Docker Compose guide and check its hardware requirements.

Create a Langfuse project and obtain its project credentials. Configure:

~~~bash
export LANGFUSE_PUBLIC_KEY="your-public-key"
export LANGFUSE_SECRET_KEY="your-secret-key"
export LANGFUSE_BASE_URL="https://cloud.langfuse.com"
~~~

The base URL depends on your Langfuse region or self-hosted deployment. Do not commit credentials to Git.

Install the SDK:

~~~bash
pip install langfuse
~~~

This course uses the current OpenTelemetry-based Python SDK style: get a client with get_client(), then create nested observations with start_as_current_observation(). Older examples using langfuse.trace(), trace.span(), or trace.generation() belong to older SDK APIs. Check the migration guide before copying older tutorials.

## 6. Trace a local Ollama call

The repository example is:

- examples/observability/ollama_langfuse_trace.py

It uses the Ollama Python SDK to call a local model and manually wraps the work in Langfuse observations.

The important structure:

~~~python
from langfuse import get_client

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="span",
    name="ollama-chat-request",
) as request_span:
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="ollama-generation",
        model="llama3.2:3b",
    ) as generation:
        # Call Ollama here.
        generation.update(output="model answer")

    request_span.update(output={"status": "success"})

langfuse.flush()
~~~

The outer span represents the application operation. The nested generation represents the model call. The SDK records observation timing and relationships. You explicitly attach model output and token usage when your provider exposes them.

### Why manual instrumentation?

Ollama is a local model runtime. The example calls it through its Python SDK and manually records the relevant fields. This makes the trace structure clear and avoids assuming that every Ollama SDK call is automatically instrumented.

For OpenAI-compatible endpoints, Langfuse also documents a Langfuse-wrapped OpenAI client. Choose the integration that matches your actual client library.

## 7. Capture token usage correctly

Ollama chat responses can include:

- prompt_eval_count: number of prompt tokens evaluated;
- eval_count: number of generated tokens;
- total_duration: total request duration in nanoseconds;
- load_duration: model loading duration;
- prompt_eval_duration: prompt evaluation duration;
- eval_duration: generation duration.

The example maps prompt and completion token counts to Langfuse usage details. Provider-specific usage fields differ, so do not assume every model API returns them.

If usage is unavailable, record it as unavailable rather than inventing a value. A rough token estimate may be useful for internal diagnostics, but label it as estimated.

## 8. Instrument each layer of a RAG pipeline

A good RAG trace should make each stage visible:

1. Request validation.
2. Query rewriting, if used.
3. Embedding generation.
4. Vector search.
5. Metadata filtering.
6. Reranking.
7. Context construction.
8. Prompt rendering and prompt version selection.
9. Answer generation.
10. Citation and output validation.

Capture enough information to reproduce a failure, but avoid storing raw confidential documents or personal information unless the data policy explicitly permits it.

Useful metadata includes:

- collection/index version;
- embedding model;
- retrieval top-k;
- filter configuration;
- document identifiers;
- prompt ID and version;
- generation model and parameters;
- output validation result.

A document ID is often safer than storing the entire document content in every trace.

## 9. Instrument each layer of an agent

For an agent, trace:

- the user's task;
- each model decision;
- selected tool name;
- validated tool arguments;
- tool execution result or error;
- retry and recovery behavior;
- step count;
- stopping reason;
- final output validation.

Do not record secrets or unrestricted tool payloads. Redact credentials, tokens, private keys, and sensitive business data before exporting observations.

A tool call is not successful merely because the model requested it. Record the actual tool execution result separately.

## 10. Errors and latency

Use nested observations so you can distinguish:

- total request duration;
- retrieval duration;
- model generation duration;
- external tool duration;
- post-processing duration.

When a function raises an exception inside a context-managed observation, the SDK can record the failed operation while the exception continues through normal application error handling.

Do not swallow exceptions just to produce a successful trace. Observability should describe the actual execution.

For production systems, define timeouts at each network boundary. Record retry count and final outcome. Avoid unbounded retries, especially for expensive model calls.

## 11. Privacy and data governance

Tracing can accidentally become a second database containing sensitive user data.

Before capturing inputs and outputs, decide:

- what data is allowed to leave the application;
- whether prompts and completions may contain personal information;
- which fields must be redacted;
- who can view traces;
- how long observations are retained;
- whether users can request deletion;
- whether trace data may be used for evaluation;
- how production and development projects are separated.

Practical controls:

1. Disable automatic input/output capture for sensitive functions.
2. Explicitly attach redacted or minimized data.
3. Prefer document IDs and metadata over full document content.
4. Never record API keys, passwords, access tokens, or private credentials.
5. Restrict access by project and role.
6. Set retention policies.
7. Test redaction logic.
8. Treat trace exports as sensitive artifacts.

A trace is not automatically safe because it is stored in an observability platform.

## 12. Production architecture

~~~text
                  Client
                    |
                    v
               FastAPI API
                    |
             Request / trace ID
                    |
                    v
              Application flow
                    |
        +-----------+-----------+
        |           |           |
        v           v           v
    Retriever   Model call   Tool executor
        |           |           |
        +-----------+-----------+
                    |
                    v
              Output validator
                    |
                    v
                Response

  Application instrumentation
             |
             v
       OpenTelemetry SDK
             |
             v
          Langfuse
             |
       Traces / metrics /
       scores / dashboards
~~~

Keep the application functional if the observability backend is temporarily unavailable. Telemetry should not become a critical dependency for answering user requests.

Use asynchronous/batched export where appropriate, bounded buffers, and explicit flush behavior for short-lived scripts. Monitor dropped telemetry and exporter failures separately.

## 13. Observability versus evaluation

Observability answers: "What happened during this request?"

Evaluation answers: "Was the result good?"

Examples:

| Observability | Evaluation |
|---|---|
| Model took 2.4 seconds | Answer was factually correct |
| Retriever returned 5 documents | Retrieved documents were relevant |
| Agent called search_logs twice | Agent completed the investigation correctly |
| Output was valid JSON | JSON fields contained correct values |
| Prompt version 1.1.0 was used | Version 1.1.0 improved held-out quality |

A mature system connects both. Traces provide examples for offline evaluation, while evaluation scores help identify quality regressions.

## 14. Common mistakes

1. Logging only the final answer.
2. Recording no prompt or model version.
3. Treating a successful HTTP response as proof of correctness.
4. Storing every raw prompt and document without privacy review.
5. Using one giant span for an entire agent workflow.
6. Failing to distinguish model calls from tool calls.
7. Ignoring token usage and model latency.
8. Allowing telemetry failure to break the main request.
9. Using an outdated Langfuse SDK tutorial without checking its version.
10. Assuming an LLM-as-a-judge score is objective ground truth.

## 15. Hands-on exercises

### Exercise A — First trace

Run the Ollama example and inspect its trace. Identify the parent span and nested generation.

### Exercise B — Add application metadata

Record a prompt ID, prompt version, model name, and environment. Do not record secrets.

### Exercise C — Add a retriever span

Wrap a mock retrieval function in a child observation. Record document IDs and retrieval count.

### Exercise D — Simulate a failure

Make the model call fail by using an unavailable model name. Inspect the recorded error and verify that your application still handles the exception correctly.

### Exercise E — Build a RAG trace

Instrument query rewriting, retrieval, reranking, generation, and citation validation as separate observations.

### Exercise F — Privacy review

Add a redaction function and test that API keys, email addresses, and other sensitive fields are not included in trace inputs.

### Exercise G — Quality feedback

Attach a score to a trace using a deterministic evaluation result. Compare trace timing with answer quality.

## 16. Completion checklist

- [ ] I can explain traces, observations, spans, generations, and scores.
- [ ] I can instrument a local Ollama call.
- [ ] I can create nested observations.
- [ ] I can record model identity and token usage.
- [ ] I can distinguish retrieval, generation, and tool latency.
- [ ] I can trace a multi-step RAG workflow.
- [ ] I can trace agent tool selection and execution.
- [ ] I can record errors without hiding them.
- [ ] I understand sensitive-data risks in traces.
- [ ] I can keep telemetry failure from breaking the application.
- [ ] I can explain the difference between observability and evaluation.

---

## Official references

- [Langfuse Python SDK overview](https://langfuse.com/docs/observability/sdk/overview)
- [Langfuse instrumentation](https://langfuse.com/docs/observability/sdk/instrumentation)
- [Langfuse observation types](https://langfuse.com/docs/observability/features/observation-types)
- [Langfuse Ollama integration guide](https://langfuse.com/docs/integrations/model-providers/ollama)
- [Langfuse self-hosting with Docker Compose](https://langfuse.com/self-hosting/deployment/docker-compose)
- [OpenTelemetry concepts](https://opentelemetry.io/docs/concepts/)
