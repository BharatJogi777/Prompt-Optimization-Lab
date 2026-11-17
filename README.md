# Prompt Optimization Lab

A production-oriented curriculum for prompt engineering, prompt evaluation, automated optimization, and operating prompts in real applications.

## Goal
Build a repeatable engineering workflow that measures whether a prompt or language-model program is better—not merely whether the wording sounds better.

## Local-first stack
- Python 3.12+
- Ollama with llama3.2:3b as a starter model
- Promptfoo for prompt testing
- DSPy for programmatic optimization
- Langfuse or LangSmith for tracing and prompt operations
- pytest for deterministic tests

Hosted APIs are optional. Never commit API keys or private evaluation data.

## Quick start
~~~bash
git clone https://github.com/BharatJogi777/Prompt-Optimization-Lab.git
cd Prompt-Optimization-Lab
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
ollama pull llama3.2:3b
pytest -q
~~~

Make sure Ollama is running. Verify it with:
~~~bash
curl http://localhost:11434/api/tags
~~~

## Curriculum
| Module | Topic | Outcome |
|---|---|---|
| 00 | Roadmap | Understand the complete learning path |
| 01 | Prompt engineering foundations | Design clear, constrained prompts |
| 02 | Evaluation fundamentals | Build datasets, metrics, and baselines |
| 03 | Promptfoo | Test variants and prevent regressions |
| 04 | Manual optimization | Improve prompts through controlled experiments |
| 05 | DSPy | Optimize LM programs against a metric |
| 06 | Prompt management | Version, promote, and roll back prompts |
| 07 | Observability | Trace quality, latency, and failures |
| 08 | RAG optimization | Evaluate retrieval and generation separately |
| 09 | Agent optimization | Measure tool use and task completion |
| 10 | Production capstone | Build a measurable optimization pipeline |

## Module 06 — Prompt management example

The repository includes a local, versioned prompt registry with environment-specific activation and unit tests:

~~~bash
python -c 'from pathlib import Path; from app.prompt_management.prompt_registry import PromptRegistry; r=PromptRegistry.from_files(root=Path.cwd(), registry_file="prompts/registry.json", environments_file="config/prompt-environments.json", environment="development"); print(r.render("support_ticket_classifier", ticket_text="My payment was deducted twice."))'
pytest -q tests/test_prompt_registry.py
~~~

Read [Module 06](docs/06-production-prompt-management.md) before using the example in an application. The file-based registry is a learning implementation, not a hosted multi-user prompt platform.

## Module 07 — Observability example

A local Ollama call can be traced with Langfuse. Configure Langfuse credentials as environment variables, then run:

~~~bash
pip install -r requirements.txt
python examples/observability/ollama_langfuse_trace.py
~~~

See [Module 07](docs/07-llm-observability-and-tracing.md) and the [example guide](examples/observability/README.md). Review privacy requirements before tracing real user data.

## Core principle
Never accept an optimized prompt merely because it sounds better. Compare it with a baseline on representative data, inspect category-level failures, and evaluate on a held-out test set.

Prompt optimization changes instructions, examples, or program configuration. Fine-tuning changes model weights. They are different techniques.

Study each module in order, run the examples, complete the exercises, and record experiment results.