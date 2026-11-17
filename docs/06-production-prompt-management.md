# Module 06 — Production Prompt Management

## Learning outcomes

By the end of this module, you should be able to:

1. Explain why prompts need lifecycle management.
2. Separate prompt content from application code.
3. Build reusable templates with explicit input variables.
4. Use immutable prompt versions and environment-specific active versions.
5. Validate prompt variables before calling an LLM.
6. Promote a tested version and roll back to a known-good version.
7. Design a prompt release workflow with evaluation gates.
8. Understand when to use a local registry versus a dedicated prompt-management platform.

---

## 1. Why prompt management matters

Imagine your backend has 12 services and each service contains a prompt as a Python string.

A developer changes the wording in one service. Another service still uses the old wording. A third service has a slightly different copy. Nobody knows which version caused a quality regression.

This is a configuration and release-management problem.

A production prompt should have:

- a stable identifier;
- an immutable version;
- a clear description and owner;
- a declared input-variable contract;
- an evaluation report;
- an approval/release status;
- a known-good rollback target.

Treat prompt changes as production changes. A prompt can affect correctness, output format, safety behavior, latency, and cost.

## 2. Prompt lifecycle

~~~text
Author prompt
    |
    v
Create immutable version
    |
    v
Validate variables and formatting
    |
    v
Run deterministic tests
    |
    v
Run evaluation dataset
    |
    v
Review quality / latency / cost
    |
    v
Approve candidate
    |
    v
Promote to staging
    |
    v
Smoke test
    |
    v
Promote to production
    |
    +----> Monitor
    |
    +----> Roll back if required
~~~

The important separation is between **creating a version** and **activating a version**. A newly created prompt should not silently become the production prompt.

## 3. Prompt identity and versioning

Use a stable prompt identifier such as:

- `support_ticket_classifier`
- `customer_email_summarizer`
- `rag_answer_generator`
- `agent_tool_selector`

Use semantic versioning as a practical convention:

| Change | Example | Meaning |
|---|---|---|
| Major | 1.0.0 → 2.0.0 | Breaking input/output contract or major behavior change |
| Minor | 1.0.0 → 1.1.0 | Backward-compatible behavior improvement |
| Patch | 1.0.0 → 1.0.1 | Small correction with same contract |

Semantic versioning is a team convention, not a guarantee that LLM behavior is semantically compatible. Even a patch change can alter model output. Run evaluations for every change.

**Never overwrite a released prompt version.** Create a new version and retain the old artifact so deployments can be reproduced and rolled back.

## 4. Separate template, metadata, and activation

A useful minimal design separates three concerns:

1. **Template:** the actual prompt text.
2. **Registry metadata:** prompt ID, version, description, file path, and required variables.
3. **Environment activation:** which version is active in development, staging, or production.

Example repository layout:

~~~text
prompt-optimization-lab/
├── prompts/
│   ├── registry.json
│   └── templates/
│       └── support_ticket_classifier/
│           ├── 1.0.0.txt
│           └── 1.1.0.txt
├── config/
│   └── prompt-environments.json
├── app/
│   └── prompt_management/
│       └── prompt_registry.py
└── tests/
    └── test_prompt_registry.py
~~~

The example implementation in this module uses only the Python standard library. This keeps the registry easy to understand and test.

## 5. Template variables are an API contract

Consider this template:

~~~text
You are a support-ticket classifier.

Classify the ticket into one category:
- billing
- delivery
- technical
- account
- other

Ticket:
{ticket_text}

Return only the category.
~~~

The required variable is `ticket_text`.

Your application should fail before making an LLM request if the variable is missing or misspelled. Silent substitution can produce incomplete prompts and hard-to-diagnose model behavior.

For production systems, define:

- required variables;
- variable types and size limits;
- whether empty values are allowed;
- escaping rules for untrusted content;
- output schema and validation separately from the prompt template.

A template renderer is not a security boundary. User content remains untrusted even after interpolation.

## 6. Versioned registry example

The example registry file records the available versions:

~~~json
{
  "prompts": {
    "support_ticket_classifier": {
      "description": "Classifies a support ticket into a fixed category.",
      "versions": {
        "1.0.0": {
          "file": "prompts/templates/support_ticket_classifier/1.0.0.txt",
          "variables": ["ticket_text"]
        },
        "1.1.0": {
          "file": "prompts/templates/support_ticket_classifier/1.1.0.txt",
          "variables": ["ticket_text"]
        }
      }
    }
  }
}
~~~

The environment configuration selects an active version:

~~~json
{
  "development": {
    "support_ticket_classifier": "1.1.0"
  },
  "staging": {
    "support_ticket_classifier": "1.1.0"
  },
  "production": {
    "support_ticket_classifier": "1.0.0"
  }
}
~~~

This allows a new prompt to be tested in development and staging while production remains pinned to a known-good version.

## 7. Implement a small local prompt registry

The runnable example is in:

- `app/prompt_management/prompt_registry.py`
- `prompts/registry.json`
- `config/prompt-environments.json`

The registry performs these jobs:

1. Load registry metadata.
2. Resolve an explicit prompt ID and version, or the version active in an environment.
3. Ensure the template path stays inside the project root.
4. Check that declared variables match the variables in the template.
5. Render only when all required values are supplied.
6. Reject missing and unexpected variables.

Example usage:

~~~python
from pathlib import Path

from app.prompt_management.prompt_registry import PromptRegistry

root = Path(__file__).resolve().parents[2]
registry = PromptRegistry.from_files(
    root=root,
    registry_file="prompts/registry.json",
    environments_file="config/prompt-environments.json",
    environment="development",
)

prompt = registry.render(
    prompt_id="support_ticket_classifier",
    ticket_text="My payment was deducted twice.",
)

print(prompt)
~~~

For a real application, construct the registry once at application startup and inject it into the service layer. Avoid reading the JSON files from disk for every request.

## 8. Immutable releases and promotion

A safe release process:

1. Add a new template file, for example `1.2.0.txt`.
2. Add its metadata to the registry.
3. Run template-contract tests.
4. Run the evaluation suite against the candidate.
5. Compare with the currently active version.
6. Review quality, latency, token usage, and safety tests.
7. Promote by changing the environment activation mapping.
8. Deploy the activation configuration with an auditable commit.
9. Monitor after release.

Do not edit the content of `1.0.0.txt` after it has been released. A change should become `1.0.1.txt` or another appropriate new version.

## 9. Rollback

Rollback should be a configuration change, not an emergency prompt rewrite.

If production uses version `1.1.0` and it causes a regression, change the production mapping back to `1.0.0`, deploy the configuration, and verify the active version.

Keep old versions available for the retention period required by your audit and reproducibility policies.

A rollback restores the old prompt, but not necessarily the old behavior if the model provider, model version, decoding parameters, retrieval data, or application code have also changed. Record those dependencies.

## 10. Testing strategy

Use multiple layers of tests:

### Layer 1 — Unit tests

- Prompt ID exists.
- Version exists.
- Template file exists.
- Template variables match metadata.
- Missing variables are rejected.
- Unexpected variables are rejected.
- Path traversal is rejected.
- Environment mapping points to a registered version.

### Layer 2 — Prompt regression tests

Run representative inputs against each candidate prompt and compare outputs with expected behavior or task-specific metrics.

### Layer 3 — Adversarial tests

Include prompt injection attempts, malformed inputs, extremely long input, empty input, and content that resembles instructions.

### Layer 4 — Integration tests

Call the actual configured model and validate output shape, latency, failure handling, and cost.

Unit tests should not require Ollama or a hosted model. Keep model-dependent tests separate so they can be run intentionally.

## 11. Prompt management platforms

A local file-based registry is a good starting point for learning and small deployments. Larger teams may need a dedicated platform.

Examples include:

- **Langfuse:** prompt management, versioning, tracing, and evaluation workflows.
- **LangSmith:** tracing, evaluation, and prompt-related workflows in the LangChain ecosystem.
- **A custom internal service:** useful when access control, deployment, audit, or data residency requirements are unique.

Before choosing a platform, check:

- version immutability and rollback support;
- environment labels and promotion workflow;
- API availability and SDK compatibility;
- access control and audit logs;
- secret handling;
- data retention and residency;
- export and backup options;
- failure behavior when the platform is unavailable.

Do not add a remote prompt-management dependency to every request without considering caching, availability, latency, and fallback behavior. Many systems fetch or load a version at startup and refresh it through a controlled deployment process.

## 12. Production architecture

~~~text
                 CONTROL PLANE
  Prompt author -> Git / prompt registry -> Evaluation pipeline
                                             |
                                             v
                                       Approval gate
                                             |
                                  Environment activation
                                             |
                                             v
                 DATA PLANE          Versioned config
  Client -> API -> Prompt service -> Rendered prompt -> Model
                    |                               |
                    |                               v
                    +------------------------- Output validation
                                                    |
                                                    v
                                              API response

  Observability records prompt ID + version + model/config metadata.
~~~

### Control plane

The control plane manages authoring, review, testing, approvals, and promotion. It should not be coupled to every end-user request.

### Data plane

The data plane serves requests using an already-approved prompt version. It should have predictable latency and a defined fallback if prompt configuration cannot be loaded.

### Observability

For each model call, record safe metadata such as:

- prompt ID and version;
- application release;
- model/provider identifier;
- environment;
- latency;
- input/output token counts when available;
- validation status;
- error category;
- evaluation or user-feedback identifiers where appropriate.

Avoid logging raw personal data or secrets by default. Apply redaction, access control, and retention policies.

## 13. Security considerations

1. **Prompt injection:** delimit and treat user-provided content as data, not trusted instructions.
2. **Secret leakage:** never place API keys or credentials in prompt templates.
3. **Sensitive data:** minimize personal and confidential data sent to model providers.
4. **Template injection:** do not use arbitrary expression evaluation to render prompts.
5. **Path traversal:** validate registry paths before reading files.
6. **Authorization:** restrict who can create, approve, and promote prompt versions.
7. **Auditability:** record who promoted a version and when.
8. **Output validation:** never rely on prompt wording alone to enforce business rules.

## 14. Common mistakes

- Keeping prompts duplicated across multiple services.
- Updating a production prompt in place.
- Allowing missing variables to become empty strings.
- Promoting a candidate without an evaluation report.
- Using different evaluation data for baseline and candidate.
- Logging sensitive prompt inputs indiscriminately.
- Fetching remote prompt content on every request without caching or fallback.
- Assuming rollback restores behavior when the model has also changed.
- Treating prompt instructions as authorization or a security boundary.

## 15. Hands-on exercises

### Exercise A — Add a prompt

Create a `customer_email_summarizer` prompt with variables for email subject and body. Add metadata and tests for the required variables.

### Exercise B — Add a version

Create version `1.1.0` with a clearer output contract. Keep `1.0.0` unchanged. Compare both versions using the same evaluation dataset.

### Exercise C — Promote

Activate version `1.1.0` in development and staging while production remains on `1.0.0`.

### Exercise D — Roll back

Simulate a regression and switch production back to `1.0.0`. Verify the resolved version in a test.

### Exercise E — Add release gates

Write a script that fails the release if:
- required prompt variables do not match;
- output schema tests fail;
- evaluation score falls below a chosen threshold;
- a critical adversarial test fails.

## 16. Completion checklist

- [ ] I can explain prompt IDs and immutable versions.
- [ ] I can separate template content from application code.
- [ ] I can validate required template variables.
- [ ] I can resolve a version by environment.
- [ ] I can promote a candidate without editing its content.
- [ ] I can roll back to a known-good version.
- [ ] I can test templates without making model calls.
- [ ] I can design evaluation gates for prompt releases.
- [ ] I understand control-plane and data-plane separation.
- [ ] I can explain prompt-management security and observability requirements.

---

## Official references

- [Langfuse prompt management](https://langfuse.com/docs/prompt-management/overview)
- [LangSmith prompt engineering and management](https://docs.smith.langchain.com/)
- [Python string formatting](https://docs.python.org/3/library/string.html#formatstrings)
- [Python pathlib](https://docs.python.org/3/library/pathlib.html)
