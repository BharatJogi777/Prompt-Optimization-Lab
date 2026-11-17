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

## Core principle
Never accept an optimized prompt merely because it sounds better. Compare it with a baseline on representative data, inspect category-level failures, and evaluate on a held-out test set.

Prompt optimization changes instructions, examples, or program configuration. Fine-tuning changes model weights. They are different techniques.

Study each module in order, run the examples, complete the exercises, and record experiment results.