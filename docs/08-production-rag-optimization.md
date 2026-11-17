# Module 08 — Production RAG Optimization

## 1. Learning outcomes

By the end of this module, you should be able to:

- Explain the complete RAG ingestion and question-answering lifecycles.
- Diagnose failures in parsing, chunking, embeddings, retrieval, reranking, context assembly, generation, and citations.
- Design controlled chunking and embedding experiments.
- Evaluate retrieval with Precision@K, Recall@K, Hit Rate@K, MRR, and nDCG@K.
- Compare vector, lexical, and hybrid retrieval.
- Decide when reranking justifies its latency and infrastructure cost.
- Assemble relevant, diverse, traceable context within a token budget.
- Evaluate answer correctness, groundedness, citation quality, and abstention separately.
- Instrument a RAG pipeline for production diagnosis.

The code lab uses only the Python standard library. It does not require an API key, a running LLM, or a large model.

---

## 2. RAG is a pipeline, not one prompt

A common beginner mistake is to describe RAG as an LLM connected to a vector database. That hides the stages where quality can fail.

### Offline ingestion lifecycle

1. Discover source documents.
2. Parse files into text and structured elements.
3. Normalize whitespace, encoding, headers, and metadata.
4. Chunk content into retrievable units.
5. Attach metadata: tenant, document ID, source path, page, heading, and version.
6. Embed each chunk with a selected embedding model.
7. Store chunk text, metadata, embedding, and version information.
8. Validate ingestion counts, failures, and index readiness.

### Online question lifecycle

1. Receive a question and authenticated identity.
2. Apply tenant and access-control filters.
3. Normalize or rewrite the question when justified.
4. Embed the query using the compatible embedding model.
5. Retrieve candidates using vector, lexical, or hybrid search.
6. Optionally rerank candidates.
7. Deduplicate and assemble context under a token budget.
8. Generate an answer using evidence-grounding instructions.
9. Validate citations and decide whether to abstain.
10. Return the answer, citations, and trace metadata.

~~~text
                 OFFLINE INGESTION
 files -> parse -> normalize -> chunk -> embed -> index
                                                   |
                                                   v
USER QUESTION -> auth/filter -> query embed -> retrieve candidates
                                              |          |
                                           vector     lexical
                                           search      search
                                              \          /
                                               hybrid merge
                                                    |
                                                  rerank
                                                    |
                                         context selection/packing
                                                    |
                                              LLM generation
                                                    |
                                        citation/grounding checks
                                                    |
                                         answer + source references
~~~

The debugging question is not simply "Why did the model hallucinate?" Ask which stage failed and collect evidence for that stage.

---

## 3. Build a failure taxonomy before tuning

| Symptom | Likely stage | Evidence to inspect | Typical correction |
|---|---|---|---|
| Relevant paragraph is absent from the index | Parsing/ingestion | Parsed text, ingestion logs | Fix parser or extraction |
| Answer needs adjacent paragraphs but neither chunk contains both | Chunking | Chunk boundaries and source layout | Structure-aware or parent-child chunks |
| Similar wording is not retrieved | Embedding/retrieval | Query and chunk rankings | Evaluate embedding model and query formulation |
| Exact product code or error ID is missed | Lexical retrieval | Keyword search results | Add BM25/full-text search and hybrid fusion |
| Correct source appears at rank 18 | Retrieval/ranking | Recall at larger candidate K | Improve candidate retrieval; test reranking |
| Top results repeat the same paragraph | Context assembly | Selected chunk IDs | Deduplicate and diversify |
| Context contains the answer, but response invents a detail | Generation/grounding | Prompt, context, answer | Improve evidence instructions and validation |
| Citation points to the wrong page | Metadata/citation mapping | Source IDs, page and offsets | Fix source metadata and citation construction |
| User can retrieve another tenant's content | Authorization | Filter construction and adversarial tests | Enforce server-side access filters before retrieval |

Do not use a generation prompt to compensate for missing evidence. If the correct source never reaches the model, changing the prompt cannot reliably repair retrieval.

---

## 4. Chunking strategies

A chunk is a unit the retrieval system can return. Chunking determines what information is available together when a question is asked.

### 4.1 Fixed-size chunking

Split text every N characters or tokens, optionally with overlap.

Advantages: simple, fast, reproducible, and useful as a baseline.

Disadvantages: can split sentences, code blocks, tables, or logical sections; a fixed character count is not a fixed token count; and a heading can become separated from the paragraph it explains.

Use it as a baseline, not as an assumption that one chunk size works for every corpus.

### 4.2 Recursive chunking

Try separators in order, such as paragraph boundaries, newlines, sentence boundaries, spaces, and finally character fallback. This attempts to preserve larger semantic units before splitting smaller ones. It is a practical general-purpose strategy for prose.

### 4.3 Structure-aware chunking

Use document structure:
- Markdown headings and sections.
- HTML elements.
- PDF page and heading boundaries.
- API reference sections.
- Code declarations and functions.
- Tables and their captions.

Store the hierarchy as metadata. A chunk should retain enough heading context to remain understandable after retrieval.

### 4.4 Semantic chunking

Split when meaning changes, often using embedding similarity between adjacent sentences or passages.

Potential benefit: chunks align more closely with topic boundaries.

Costs and risks:
- Additional embedding work during ingestion.
- Thresholds need evaluation.
- Similarity is not a perfect topic-boundary detector.
- Results may vary with embedding model changes.

Do not adopt semantic chunking because it sounds more intelligent. Compare it with a simpler baseline on a labeled evaluation set.

### 4.5 Parent-child retrieval

Store small child chunks for precise matching and link them to larger parent sections.

At query time, retrieve child chunks, deduplicate their parent IDs, and return the parent section or a controlled window around the child.

This can improve matching precision while providing enough surrounding explanation. It also increases storage and context-selection complexity.

### 4.6 Overlap

Overlap preserves context across adjacent chunks. A sentence near the end of one chunk may also appear at the beginning of the next.

Too little overlap can lose boundary context. Too much overlap creates duplicate results, redundant context, more embedding/storage cost, and lower effective diversity.

Treat overlap as an experiment variable. Do not blindly use the same percentage for every corpus.

### 4.7 Special content needs special parsing

**Tables:** preserve headers with rows. A row without its column names may be meaningless.

**Code:** split around functions, classes, or declarations where possible. Preserve imports and relevant type definitions when needed.

**PDFs:** preserve page numbers and section headings. Validate extraction quality; scanned PDFs may require OCR.

**Long policies and manuals:** keep section hierarchy and stable source anchors.

**Conversation history:** chunk by conversation or topic boundaries and preserve timestamps and speaker metadata when relevant.

---

## 5. Design a chunking experiment

Never compare chunking strategies using a few questions you remember. Create a fixed evaluation set first.

Hold these constant unless they are the variable being tested:
- Source corpus and document versions.
- Evaluation questions and relevance labels.
- Embedding model and model version.
- Retrieval algorithm and candidate K.
- Metadata filters.
- Reranker configuration.
- Generation model and prompt for answer-level comparisons.

Example experiment matrix:

| Experiment | Chunker | Target size | Overlap | Purpose |
|---|---|---:|---:|---|
| A | Fixed | 400 tokens | 40 | Baseline |
| B | Recursive | 400 tokens | 40 | Preserve boundaries |
| C | Recursive | 700 tokens | 70 | More surrounding context |
| D | Structure-aware | Section-based | N/A | Preserve headings and sections |
| E | Parent-child | Child 250 / parent 900 | N/A | Precision plus context |

These numbers are starting points for experiments, not universal best practices. Use token counts measured with the target model's tokenizer where possible.

Evaluate two different questions:

1. Can retrieval find the right evidence? Use retrieval metrics.
2. Can the application answer correctly using the selected evidence? Use answer-level evaluation.

A larger chunk can improve context completeness while reducing retrieval precision. A smaller chunk can improve matching while removing important surrounding details. Evaluation reveals the trade-off for your corpus.

---

## 6. Embedding models and embedding-space consistency

An embedding model maps text to a numeric vector. A vector database compares vectors to identify semantically related content.

### 6.1 Similarity is not correctness

A high similarity score means two vectors are close according to the selected distance function. It does not prove that a chunk answers the question.

A semantically related chunk may discuss a different product version, refer to another customer or tenant, describe an exception rather than the general rule, or contain a similar term without the requested fact.

Use labeled relevance judgments to measure retrieval.

### 6.2 Keep query and document embeddings compatible

Use the same embedding model and compatible preprocessing for document chunks and queries. Some models expose separate query/document instructions or modes; follow that model's documented contract.

Do not silently change the embedding model while keeping old vectors. Old and new vectors may inhabit different spaces even if their dimensions happen to match.

### 6.3 Dimension is a schema decision

If your database column is vector(768), the model must produce vectors with 768 dimensions for that index.

For a model migration:
1. Record the current embedding model and version.
2. Create a new versioned embedding/index space.
3. Re-embed the corpus.
4. Evaluate retrieval against the same test set.
5. Compare quality, latency, storage, and cost.
6. Switch traffic deliberately.
7. Retain rollback capability until the new index is stable.

Do not mix vectors from incompatible models in one index.

### 6.4 Cosine similarity and cosine distance

Cosine similarity measures directional similarity. Cosine distance is commonly expressed as:

cosine_distance = 1 - cosine_similarity

A larger cosine similarity means more similar. A smaller cosine distance means more similar.

Be careful with database operators and thresholds: an API returning distance is not returning similarity. Name fields explicitly, for example cosine_distance, rather than calling both values score.

### 6.5 Evaluate embeddings empirically

Use representative natural-language questions, exact identifiers and error codes, acronyms, multilingual queries if supported, short and long questions, multiple-constraint questions, and queries that should return no evidence.

Compare candidate models using retrieval metrics and operational measurements. Consider embedding quality, dimensions, latency, memory, throughput, licensing, and deployment constraints.

---

## 7. Vector, lexical, and hybrid retrieval

### 7.1 Vector retrieval

Vector retrieval finds chunks close to the query embedding. It is useful when the query and source use different wording but express similar meaning.

Potential weaknesses:
- Exact identifiers may not rank well.
- Similarity can be high for conceptually related but incorrect chunks.
- Approximate nearest-neighbor indexes trade exactness for speed.

### 7.2 Lexical retrieval

Lexical retrieval matches terms. BM25 is a widely used ranking method. PostgreSQL full-text search can provide a useful lexical baseline without adding a separate search service.

Lexical retrieval is especially useful for error codes, product IDs, API paths, names, rare terms, and exact phrases.

### 7.3 Hybrid retrieval

Hybrid retrieval combines lexical and vector candidates.

One common method is Reciprocal Rank Fusion (RRF). It combines ranks rather than trying to compare raw scores from different retrieval systems.

RRF(d) = sum over retrievers r of 1 / (c + rank_r(d))

Where rank_r(d) is the rank of document d in retriever r, and c is a smoothing constant chosen empirically. A document absent from a result list contributes zero for that retriever.

RRF is a practical baseline because vector similarity and lexical scores may have different scales. It still requires evaluation: fusion cannot recover a document that neither retriever returned.

### 7.4 Metadata filtering

Metadata filters can constrain retrieval by tenant or organization, user permissions, document type, product or service, effective date, document version, region, or language.

Authorization filters must be applied by trusted server-side code. Never let the model decide which tenant or private documents the user may access.

A filter that is missing or applied after retrieval can become a data-isolation vulnerability, not merely a relevance bug.

---

## 8. Candidate retrieval and reranking

Retrieval often has two stages:

1. Candidate generation: retrieve a reasonably broad set, such as top 20–100 candidates.
2. Reranking: score those candidates against the query and reorder them, then select a small final set.

A cross-encoder reranker jointly processes the query and each candidate. It can improve ordering because it evaluates the pair together, but it costs more than vector lookup.

Reranking may help when correct evidence appears in the candidate set but ranks too low, the corpus has many near-duplicates, or questions contain multiple constraints.

Reranking does not help when parsing failed, chunking removed necessary context, candidate retrieval never included the correct chunk, metadata filters excluded the right document, or the reranker is poorly suited to the language/domain.

A reranker improves ordering among candidates. It cannot retrieve evidence that candidate generation did not find.

Measure candidate Recall@K before reranking, final Precision@K after reranking, answer correctness and groundedness, added p50/p95 latency, and resource usage.

For a small local machine, start with a modest candidate count and a lightweight reranker only after proving that ranking is the bottleneck.

---

## 9. Context assembly and token budgeting

The context sent to the LLM should not simply be the top K raw chunks concatenated together.

A robust context builder should:
1. Remove duplicate chunk IDs.
2. Detect near-duplicate text where practical.
3. Preserve source and section metadata.
4. Prefer evidence that directly answers the question.
5. Include complementary evidence when the question needs multiple facts.
6. Avoid contradictory versions unless the question asks for a comparison.
7. Respect a token budget measured for the generation model.
8. Preserve stable citation identifiers.

Example:

~~~text
[Source: policy-2025, section: Refunds, page: 12, chunk: c-104]
Refunds are available within 30 days when...

[Source: policy-2025, section: Exceptions, page: 13, chunk: c-105]
The 30-day rule does not apply when...
~~~

The source label is part of the evidence contract. If the model generates a citation, the application must map its identifier to a real source record. Do not trust a citation URL or document ID invented by the model.

Long-context models do not guarantee equal attention to every token position. Test whether ordering affects answer quality: most relevant evidence first, evidence grouped by source, direct answer evidence before supporting detail, and contradictory or superseded material excluded or explicitly labeled.

---

## 10. Generation prompts for grounded answers

A RAG prompt should make the evidence boundary explicit. Example:

~~~text
You are an evidence-grounded assistant.

Answer the user's question using only the supplied context.
If the context does not contain enough evidence, say that you cannot
determine the answer from the available documents.
Do not fill gaps with assumptions or outside knowledge.
Distinguish explicit facts from reasonable interpretations.
For every factual claim, include the source chunk IDs that support it.
Never invent source IDs, page numbers, quotations, or URLs.

Context:
{context}

Question:
{question}

Return:
- answer
- citations: a list of source chunk IDs
- insufficient_evidence: true or false
~~~

This prompt helps establish behavior, but it is not a security boundary and does not guarantee truth. Validate output structure and citations in application code. The model can still make unsupported claims or cite an irrelevant chunk.

### Citation validation

For each citation:
- Confirm the chunk ID exists in the retrieved context.
- Confirm it belongs to an authorized source.
- Map it to a stable document version and page/section anchor.
- Optionally verify that the cited chunk supports the associated claim.

A citation being present is not the same as a citation being correct.

---

## 11. Retrieval evaluation metrics

Build a small labeled dataset before tuning. For each query, annotate the chunk IDs that contain relevant evidence.

The code in app/rag_eval/metrics.py implements these metrics without third-party dependencies.

### Precision@K

Of the first K retrieved chunks, what fraction is relevant?

Precision@K = relevant chunks in top K / K

This implementation uses K as the denominator, even if fewer than K results were returned. Missing result slots therefore count against precision.

### Recall@K

Of all known relevant chunks, what fraction appeared in the first K results?

Recall@K = relevant chunks in top K / all relevant chunks

Recall is useful for candidate generation. If the right evidence is not in the candidate set, later stages cannot use it.

### Hit Rate@K

Did at least one relevant chunk appear in the first K results? This measures whether a query has any relevant evidence in the returned shortlist.

### Mean Reciprocal Rank (MRR)

For each query, find the rank of the first relevant result and take its reciprocal. Average across queries.

RR = 1 / rank_of_first_relevant_result

MRR rewards placing the first useful result near the top.

### Normalized Discounted Cumulative Gain (nDCG@K)

nDCG rewards relevant results near the top more than relevant results near the bottom. This example uses binary relevance.

DCG@K = sum(rel_i / log2(i + 1))

Here i is a one-based rank. nDCG divides DCG by the ideal DCG for the same number of relevant items.

### No-answer queries

A query with no relevant evidence is not an ordinary retrieval-positive query. Track it separately:
- Did the system abstain?
- Did it make an unsupported claim?
- Did it cite irrelevant evidence?

Do not quietly count no-answer queries as successful retrievals. Evaluate abstention and false-answer rate explicitly.

---

## 12. Answer-level evaluation

Retrieval metrics cannot tell you whether the final answer is correct. Evaluate these dimensions:

| Dimension | Question |
|---|---|
| Correctness | Does the answer satisfy the user's question? |
| Groundedness | Are factual claims supported by retrieved evidence? |
| Context relevance | Was the supplied context useful for this question? |
| Citation precision | Do cited sources actually support the claims attached to them? |
| Citation completeness | Are important factual claims supported by citations? |
| Abstention quality | Does the system decline to answer when evidence is insufficient? |
| Instruction compliance | Did the response follow required format and constraints? |

Use human-reviewed reference answers for important domains. LLM-as-judge can help triage larger test sets, but it is itself a model-based measurement and can be biased or inconsistent. Calibrate it against human judgments and retain examples of disagreements.

A useful dataset includes straightforward answerable questions, questions requiring multiple chunks, questions involving tables or code, exact identifier questions, conflicting document versions, absent answers, misleading but topically similar evidence, and permission-boundary cases.

Do not tune repeatedly against the final test set. Keep separate development and held-out test sets to reduce overfitting.

---

## 13. Run the local retrieval-metrics example

From the repository root:

~~~bash
python -m unittest discover -s tests -p "test_rag_metrics.py" -v
python examples/rag/evaluate_retrieval.py
~~~

The example uses a tiny synthetic dataset to demonstrate metric calculation; it is not a benchmark of an actual embedding model or vector database.

To evaluate your own retriever:
1. Create a dataset with stable query IDs.
2. Record relevant chunk IDs for each query.
3. Run the real retriever and record its ranked chunk IDs.
4. Feed ranked IDs and relevance labels into the metric functions.
5. Aggregate metrics across queries.
6. Inspect failures individually; aggregate scores hide important failure patterns.

---

## 14. Applying this to FastAPI + Ollama + pgvector

A production architecture can keep responsibilities separate:

~~~text
FastAPI
  |
  +-- ingestion service
  |     +-- parser
  |     +-- chunker
  |     +-- Ollama embedding client
  |     +-- PostgreSQL/pgvector repository
  |
  +-- query service
        +-- authentication and tenant filter
        +-- query embedding
        +-- vector + lexical retrieval
        +-- optional reranker
        +-- context builder
        +-- LLM generation
        +-- citation validator
        +-- response formatter
~~~

If your current index uses nomic-embed-text with 768-dimensional vectors, keep the database dimension and embedding model contract aligned. A model change should be treated as an index migration, not as a configuration-only change.

Suggested API boundaries:
- POST /documents: register a document.
- POST /documents/{document_id}/process: parse, chunk, embed, and index.
- GET /documents/{document_id}: inspect ingestion status and version.
- POST /search: return ranked chunks and scores with source metadata.
- POST /ask: execute retrieval, context assembly, generation, and citation validation.

Keep retrieval separately callable from answer generation. This lets you debug retrieval without involving an LLM and measure each stage independently.

Example search response contract (illustrative values only):

~~~json
{
  "query": "How long does the refund window last?",
  "results": [
    {
      "chunk_id": "chunk-104",
      "document_id": "policy-2025",
      "text": "Refunds are available within 30 days...",
      "score": 0.18,
      "score_type": "cosine_distance",
      "metadata": {
        "section": "Refunds",
        "page": 12
      }
    }
  ]
}
~~~

A distance score must be labeled as distance; do not interpret it as a similarity score.

---

## 15. Langfuse tracing for RAG

Trace the full request and create nested observations/spans for meaningful stages. Exact SDK APIs depend on the Langfuse version in your environment; use the API documented for the version you pin.

Recommended trace structure:

~~~text
rag.request
  ├── query.normalize
  ├── query.embed
  ├── retrieval.vector
  ├── retrieval.lexical
  ├── retrieval.fusion
  ├── retrieval.rerank
  ├── context.build
  ├── llm.generate
  └── citation.validate
~~~

Capture privacy-conscious metadata:
- Request and trace IDs.
- Prompt version.
- Model identifier and generation parameters.
- Embedding model and version.
- Chunker and index version.
- Candidate count and final context count.
- Retrieved chunk IDs and rank positions.
- Retrieval and generation latency.
- Token usage when available.
- Whether the system abstained.
- Evaluation labels when available.

Avoid logging secrets, access tokens, full private documents, or raw personal data by default. Define retention and redaction policies before production rollout.

---

## 16. Production reliability and security checklist

### Ingestion
- [ ] Ingestion is idempotent for a document version.
- [ ] Parser failures are visible and retryable.
- [ ] Empty or suspiciously short extraction is detected.
- [ ] Chunk IDs are stable within a document version.
- [ ] Chunker and embedding model versions are recorded.
- [ ] Reprocessing does not leave stale chunks active.
- [ ] Document deletion removes or disables derived chunks and embeddings.

### Retrieval
- [ ] Tenant and permission filters are applied server-side.
- [ ] Query and document embedding models are compatible.
- [ ] Vector dimensions match the database schema.
- [ ] Distance and similarity are not confused.
- [ ] Candidate recall is measured.
- [ ] Hybrid search is evaluated against vector-only and lexical-only baselines.
- [ ] Index recall/latency trade-offs are monitored.

### Generation
- [ ] Context has a measured token budget.
- [ ] Every citation maps to a real authorized source.
- [ ] Unsupported questions can be refused.
- [ ] Output schema is validated.
- [ ] Prompt and model versions are recorded.
- [ ] Sensitive context is not exposed through logs.

### Operations
- [ ] p50/p95 latency is tracked per stage.
- [ ] Empty retrieval and low-confidence retrieval are measured.
- [ ] Errors and timeouts are observable.
- [ ] Evaluation runs are repeatable.
- [ ] Model, prompt, chunker, and index rollouts can be rolled back.
- [ ] Cache keys include relevant tenant, model, index, and query-version dimensions.

---

## 17. Practical lab

Complete these in order. Do not skip directly to reranking.

### Lab A — Establish a baseline
1. Choose a small representative document collection.
2. Create at least 20 realistic questions.
3. Label relevant chunk IDs for each question.
4. Run your current retriever with top K = 5 and K = 10.
5. Record Precision@K, Recall@K, Hit Rate@K, MRR, and nDCG@K.

### Lab B — Improve chunking
1. Keep corpus and evaluation labels fixed.
2. Compare fixed-size and recursive chunking.
3. Compare at least two target sizes and two overlap values.
4. Re-embed each variant.
5. Compare retrieval metrics and inspect boundary failures.

### Lab C — Compare retrieval
1. Run vector-only retrieval.
2. Run lexical-only retrieval.
3. Run hybrid retrieval with RRF.
4. Compare exact identifiers and natural-language questions separately.
5. Inspect queries where one retriever finds evidence the other misses.

### Lab D — Add reranking
1. Save the initial candidate list.
2. Rerank only those candidates.
3. Compare candidate Recall@K and final Precision@K.
4. Measure p50 and p95 added latency.
5. Keep reranking only if quality gains justify operational cost.

### Lab E — Evaluate answers
1. Use the same questions and retrieved evidence.
2. Generate answers with a versioned prompt.
3. Score correctness, groundedness, citation quality, and abstention.
4. Manually inspect disagreements between automated judges and human review.
5. Add every confirmed failure as a regression case.

### Lab F — Productionize
1. Add per-stage tracing.
2. Add document, chunker, embedding, index, and prompt versions.
3. Add tenant-isolation tests.
4. Add deletion and re-ingestion tests.
5. Add dashboards and alerts for latency, empty retrieval, and error rates.

---

## 18. Knowledge check

Explain these without memorizing definitions:

1. Why can a correct answer be impossible if candidate retrieval misses the evidence?
2. Why might a smaller chunk improve retrieval but hurt answer quality?
3. What is the difference between cosine similarity and cosine distance?
4. Why should exact identifiers often be tested with lexical retrieval?
5. What does RRF combine, and why does it not require raw scores to share a scale?
6. What can a reranker improve, and what can it never fix?
7. Why is a citation ID existing not enough to prove that the citation supports a claim?
8. Why should no-answer queries be evaluated separately?
9. Why is changing an embedding model a data/index migration?
10. Which stage would you inspect if a correct chunk is in the candidate list but absent from final context?

### Completion criteria

You have completed Module 08 when you can build a labeled retrieval evaluation set, run and interpret the retrieval metrics, compare chunking and retrieval strategies fairly, explain reranking trade-offs, validate citations in application code, and trace a RAG request stage by stage.

**Next module:** Module 09 — Agent and Tool-Calling Optimization. We will evaluate planning, tool selection, argument correctness, execution reliability, retries, state, and end-to-end agent outcomes.
