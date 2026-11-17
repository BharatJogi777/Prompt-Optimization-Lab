# DSPy examples

These examples use a local Ollama model so you can learn without a hosted API key.

## Prerequisites

- Python 3.12 (or another supported Python 3.10+ version)
- Ollama running locally
- `llama3.2:3b` pulled in Ollama
- DSPy installed in the active virtual environment

From the repository root:

~~~bash
ollama pull llama3.2:3b
python -m pip install dspy
~~~

## Run the baseline

~~~bash
python examples/dspy/sentiment_baseline.py
~~~

## Run optimization

~~~bash
python examples/dspy/optimize_sentiment.py
~~~

The optimizer performs additional model calls. It may take time on a laptop CPU. The included dataset is intentionally tiny to keep the learning example understandable; it is not suitable for production evaluation.

The optimization script imports the baseline module from the same directory. If you prefer package-style imports in a larger project, add `__init__.py` files and run the examples as Python modules.

## Expected behavior

The scripts print model-generated labels and measured scores. Exact predictions and scores vary by model version and generation behavior. There is no hard-coded expected accuracy.
