"""Run the synthetic retrieval evaluation example from the repository root."""

import json
from pathlib import Path

from app.rag_eval.metrics import (
    hit_rate_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


def main() -> None:
    dataset_path = Path(__file__).with_name("evaluation_dataset.json")
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    queries = dataset["queries"]
    ranked_by_query = dataset["ranked_results"]
    k = 3

    precision_scores = []
    recall_scores = []
    hit_scores = []
    ndcg_scores = []
    ranked_lists = []
    judgments = []

    print(f"Evaluating {len(queries)} synthetic queries at K={k}\\n")

    for query in queries:
        query_id = query["query_id"]
        relevant = set(query["relevant_chunk_ids"])
        ranked = ranked_by_query[query_id]

        precision = precision_at_k(ranked, relevant, k)
        recall = recall_at_k(ranked, relevant, k)
        hit = hit_rate_at_k(ranked, relevant, k)
        ndcg = ndcg_at_k(ranked, relevant, k)
        rr = reciprocal_rank(ranked, relevant)

        precision_scores.append(precision)
        recall_scores.append(recall)
        hit_scores.append(hit)
        ndcg_scores.append(ndcg)
        ranked_lists.append(ranked)
        judgments.append(relevant)

        print(f"{query_id}: {query['question']}")
        print(f"  ranked IDs: {ranked}")
        print(
            "  "
            f"Precision@{k}={precision:.3f} "
            f"Recall@{k}={recall:.3f} "
            f"HitRate@{k}={hit:.3f} "
            f"MRR={rr:.3f} "
            f"nDCG@{k}={ndcg:.3f}"
        )

    count = len(queries)
    if count:
        print("\\nMacro averages")
        print(f"  Precision@{k}: {sum(precision_scores) / count:.3f}")
        print(f"  Recall@{k}:    {sum(recall_scores) / count:.3f}")
        print(f"  HitRate@{k}:   {sum(hit_scores) / count:.3f}")
        print(f"  MRR:           {mean_reciprocal_rank(ranked_lists, judgments):.3f}")
        print(f"  nDCG@{k}:       {sum(ndcg_scores) / count:.3f}")

    print(
        "\\nNote: these are synthetic rankings for learning the metric calculations, "
        "not measured performance of a live retriever."
    )


if __name__ == "__main__":
    main()
