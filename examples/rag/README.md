# RAG retrieval evaluation example

This example demonstrates retrieval ranking metrics using a tiny synthetic dataset. It is deliberately independent of Ollama, LangChain, PostgreSQL, and pgvector so you can understand and test evaluation logic separately.

## Run

From the repository root:

~~~bash
python -m unittest discover -s tests -p "test_rag_metrics.py" -v
python examples/rag/evaluate_retrieval.py
~~~

No third-party dependency or API key is required.

## Files

- evaluation_dataset.json: three example queries, relevance labels, and ranked chunk IDs.
- evaluate_retrieval.py: calculates per-query and macro-averaged metrics.
- app/rag_eval/metrics.py: reusable metric functions.
- tests/test_rag_metrics.py: deterministic unit tests.

## Connect it to a real retriever

Replace the synthetic ranked results with ordered chunk IDs returned by your search endpoint. Keep relevance judgments independent: a person should label which chunks genuinely contain evidence for each question.

Do not generate relevance labels from the retriever being evaluated. That would make the evaluation circular.

## Important metric conventions

- Precision@K divides by K, even if fewer than K results were returned.
- Recall@K divides by the number of relevant chunk IDs for that query.
- Queries with no relevant evidence return zero in these helper functions, but should be analyzed separately as no-answer/abstention cases.
- nDCG uses binary relevance.
- MRR is averaged across the supplied query list.

These metrics evaluate ranking only. They do not measure answer correctness, groundedness, citation validity, or user-perceived usefulness.
