# Module 05 — DSPy Architecture and Internals

## Learning outcomes

After this module, you should be able to:

1. Explain why DSPy exists and how it differs from hand-written prompts.
2. Describe the DSPy execution and optimization lifecycle.
3. Define task contracts with Signatures.
4. Compose LLM operations with Modules such as Predict and ChainOfThought.
5. Build a dataset and a task-specific metric.
6. Run a baseline, compile an optimized program, and evaluate it on held-out examples.
7. Save and load a compiled program.
8. Identify what DSPy does not solve for production systems.

> Version note: DSPy evolves quickly. The examples use the current documented `dspy.LM`, `dspy.Signature`, `dspy.Module`, and optimizer APIs. Pin the version you test, and re-check the official migration notes before upgrading.

---

## 1. Why DSPy exists

A manually engineered LLM application often looks like this:

1. Write a prompt.
2. Try it against a few inputs.
3. Change the wording.
4. Try again.
5. Add examples when the model fails.
6. Repeat.

This can work, but the process is difficult to reproduce. Prompt quality depends on the engineer's intuition, and a prompt that improves one example may damage another.

DSPy approaches the problem as **programming with language models**. Instead of treating the entire application as a fixed prompt string, you define:

- the task's inputs and outputs;
- the modules and steps that perform the task;
- examples that represent desired behavior;
- a metric that scores predictions.

An optimizer can then search for better instructions and demonstrations for the program.

DSPy does not make evaluation data optional. The quality of the result depends heavily on the quality of your examples, metric, model, and validation process.

## 2. Manual prompting versus DSPy

| Concern | Manual prompting | DSPy |
|---|---|---|
| Task definition | Prompt text | Signature |
| LLM operation | API call or chain | Module |
| Examples | Manually inserted | Dataset and demonstrations |
| Quality measurement | Often informal | Explicit metric and evaluation |
| Improvement | Engineer edits prompt | Optimizer searches program parameters |
| Reproducibility | Depends on prompt/version discipline | Compiled program can be saved and versioned |

DSPy is not a replacement for every framework. LangChain provides integrations and orchestration abstractions; DSPy focuses on defining and optimizing LM programs. They can be used together when the architecture benefits from both.

## 3. DSPy mental model

Think of the system as this pipeline:

```
Task examples
     |
     v
Signature ----> Module / Program ----> Language Model
     |                 |                    |
     |                 v                    v
     +------------> Metric <------------ Prediction
                       |
                       v
                  Optimizer
                       |
                       v
              Compiled program
                       |
                       v
              Held-out evaluation
```

The main building blocks:

1. **Language model (LM):** the model DSPy calls, such as a local Ollama model.
2. **Signature:** the input/output contract for an LM operation.
3. **Module:** a reusable component that executes one or more LM operations.
4. **Program:** one module or a composition of modules.
5. **Example/dataset:** representative input and expected output records.
6. **Metric:** a function that scores a prediction against the expected result.
7. **Optimizer:** searches for better instructions and/or demonstrations.
8. **Compiled artifact:** the optimized program configuration that can be saved and loaded.

## 4. Configure a language model

Install DSPy in a virtual environment:

~~~bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install dspy
~~~

Start Ollama and pull a model:

~~~bash
ollama pull llama3.2:3b
ollama serve
~~~

If Ollama is already running as a background service, do not start a second server.

Configure DSPy:

~~~python
import dspy

lm = dspy.LM("ollama_chat/llama3.2:3b")
dspy.configure(lm=lm)
~~~

The current DSPy documentation lists the `ollama_chat/` route as a native local Ollama provider. The default local address is used by this route. If you use a non-default Ollama host, consult the current provider configuration documentation.

A configured LM is the default for DSPy modules in the process. For a specific block of code, DSPy also provides contextual configuration:

~~~python
with dspy.context(lm=lm):
    # Calls inside this block use this LM context.
    ...
~~~

Do not put credentials in source code. Use environment variables or a secret manager for hosted providers.

## 5. Signatures: define the task contract

A Signature describes what information goes into an LM operation and what information should come out.

The compact form:

~~~python
import dspy

class Sentiment(dspy.Signature):
    """Classify the sentiment expressed in a customer review."""
    review: str = dspy.InputField(desc="The customer's review text")
    sentiment: str = dspy.OutputField(
        desc="Exactly one label: positive, negative, or neutral"
    )
~~~

Here:

- `review` is an input field;
- `sentiment` is an output field;
- the class docstring provides task-level instructions;
- field descriptions clarify the meaning and expected shape of each field.

A shorthand Signature is also possible:

~~~python
predict = dspy.Predict("review -> sentiment")
~~~

Use a class-based Signature when the task needs clear descriptions, types, or a maintainable contract.

### A Signature is not a full application schema

A Signature tells the LM operation what it should receive and produce. Your application still needs to validate the result, handle errors, enforce business rules, and decide what to do when the output is invalid.

For example, if only three labels are allowed, validate the returned label in application code rather than trusting generated text blindly.

## 6. Modules: define how the LM operation runs

A Module is a reusable building block. Common modules include:

- `dspy.Predict`: performs a prediction according to a Signature.
- `dspy.ChainOfThought`: adds a reasoning-oriented intermediate field before the requested answer.
- `dspy.Module`: base class for composing a custom program.

Basic prediction:

~~~python
class Sentiment(dspy.Signature):
    """Classify the sentiment of a review."""
    review: str = dspy.InputField()
    sentiment: str = dspy.OutputField(
        desc="positive, negative, or neutral"
    )

class SentimentProgram(dspy.Module):
    def __init__(self):
        super().__init__()
        self.classify = dspy.Predict(Sentiment)

    def forward(self, review: str):
        return self.classify(review=review)

program = SentimentProgram()
result = program(review="The delivery was quick and the packaging was excellent.")
print(result.sentiment)
~~~

A custom Module is useful because it creates a stable program boundary. Later, you can add preprocessing, multiple predictors, retrieval, or other logic without changing the public call interface.

### Predict versus ChainOfThought

~~~python
direct = dspy.Predict("question -> answer")
reasoning = dspy.ChainOfThought("question -> answer")
~~~

Use direct prediction when the task is straightforward and a concise output is sufficient. Use ChainOfThought when intermediate reasoning improves the task and the model/provider supports the behavior reliably.

Do not assume that adding reasoning always improves quality. It can increase latency and token use, and it can still produce incorrect answers. Evaluate both approaches.

## 7. Examples and datasets

DSPy examples are structured records. Mark which fields are inputs using `with_inputs`:

~~~python
trainset = [
    dspy.Example(
        review="Fantastic quality and fast delivery.",
        sentiment="positive",
    ).with_inputs("review"),
    dspy.Example(
        review="The product arrived broken.",
        sentiment="negative",
    ).with_inputs("review"),
]
~~~

The expected output is available to the metric and optimizer, but it is not an input field supplied as part of the normal program call.

### Dataset discipline

Use separate data for:

- **Training set:** examples available to the optimizer.
- **Development/validation set:** examples used to compare candidate programs and make tuning decisions.
- **Test set:** held-out examples used for the final estimate of generalization.

Never optimize repeatedly against your final test set. That turns the test set into training feedback and makes the reported score overly optimistic.

A tiny dataset is useful for learning the API, not for claiming production quality.

## 8. Metrics: define what good means

An optimizer needs a score. The metric is therefore one of the most important parts of the system.

For a three-label classifier, begin with a deterministic metric:

~~~python
def normalize_label(value: str) -> str:
    return value.strip().lower().rstrip(".")

def sentiment_metric(example, prediction, trace=None) -> bool:
    expected = normalize_label(example.sentiment)
    actual = normalize_label(prediction.sentiment)
    return actual == expected
~~~

The metric receives:

- `example`: the dataset record, including expected output;
- `prediction`: the program's generated output;
- `trace`: optional execution information supplied by some evaluation/optimization paths.

A metric can return a Boolean or a numeric score. The score should reflect the real task. For more complex applications, you may need a metric that checks multiple requirements, such as correctness, schema validity, citation support, or policy compliance.

### Avoid weak metrics

Bad metric: reward any non-empty answer.

Why it fails: the optimizer can learn to produce plausible but incorrect answers.

Better metric: compare against reliable labels, validate structured fields, or score verifiable task outcomes.

For subjective tasks, an LLM judge can help, but it introduces judge bias and inconsistency. Calibrate it against human-reviewed examples and retain deterministic checks wherever possible.

## 9. Baseline evaluation comes before optimization

First run the unoptimized program on a development set. Record:

- exact model identifier;
- DSPy version;
- dataset version;
- metric implementation version;
- score and per-category failures;
- latency and token/call usage where available.

A baseline tells you whether optimization actually helped. Without it, you cannot distinguish a real improvement from a change in test conditions.

For a small exercise, you can call the program over the examples and calculate the score manually:

~~~python
def evaluate(program, dataset):
    correct = 0
    for example in dataset:
        prediction = program(**example.inputs())
        correct += int(sentiment_metric(example, prediction))
    return correct / len(dataset)

baseline_score = evaluate(program, devset)
print(f"Baseline accuracy: {baseline_score:.2%}")
~~~

For larger evaluations, use DSPy's evaluation utilities and keep the evaluation configuration consistent between baseline and optimized versions.

## 10. Optimizers: how DSPy improves a program

An optimizer uses your program, examples, and metric to search for a better configuration.

The key idea is that the optimizer does not need you to manually write every possible prompt variation. It can propose or construct instructions and demonstrations, execute candidates, score them, and retain promising configurations.

### BootstrapFewShot

At a high level:

1. Run a teacher/program on training examples.
2. Compare generated predictions with the expected behavior using your metric.
3. Keep demonstrations that pass the metric.
4. Attach selected demonstrations to the student program.

Example:

~~~python
optimizer = dspy.BootstrapFewShot(
    metric=sentiment_metric,
    max_bootstrapped_demos=4,
    max_labeled_demos=4,
)

optimized_program = optimizer.compile(
    program,
    trainset=trainset,
)
~~~

The optimizer can make additional LM calls. With a local 3B model, start with a small dataset and small limits because optimization can be slow and the model may be less reliable at generating high-quality demonstrations.

### MIPROv2

MIPROv2 can optimize instructions and few-shot demonstrations jointly. It proposes candidate instructions and demonstrations, then searches for a good combination using a more involved optimization procedure.

Conceptual usage:

~~~python
optimizer = dspy.MIPROv2(
    metric=sentiment_metric,
    auto="light",
)

optimized_program = optimizer.compile(
    program,
    trainset=trainset,
)
~~~

MIPROv2 can require many more model calls than a simple baseline. Do not begin with an expensive optimization run before you have a trustworthy metric and a useful dataset.

### Choosing an optimizer

| Situation | Starting point |
|---|---|
| Very small dataset, learning the workflow | BootstrapFewShot |
| More examples and candidate comparisons | BootstrapFewShotWithRandomSearch |
| Optimize instructions and demonstrations together | MIPROv2 |
| Need a zero-shot instruction search | MIPROv2 configured for zero-shot use |

These are starting suggestions, not guaranteed thresholds. Dataset size, task complexity, model quality, metric reliability, and optimization budget all matter.

## 11. The compile lifecycle

The standard lifecycle is:

1. Define the Signature.
2. Build a Module/program.
3. Prepare training and development data.
4. Define a meaningful metric.
5. Evaluate the unoptimized baseline.
6. Select an optimizer and budget.
7. Compile the program using training examples.
8. Evaluate the compiled program on held-out data.
9. Inspect failures and compare trade-offs.
10. Save the chosen compiled artifact.

Compilation means searching for an improved program configuration. In the common prompt-optimization workflow, this is not the same as changing the underlying model weights.

## 12. Save and load optimized programs

After compilation:

~~~python
optimized_program.save("artifacts/sentiment_v1.json")
~~~

Load it into a fresh instance of the same program structure:

~~~python
loaded_program = SentimentProgram()
loaded_program.load("artifacts/sentiment_v1.json")
~~~

Treat the saved program as a versioned deployment artifact. Store metadata alongside it:

- DSPy version;
- model/provider and model version;
- source-code commit;
- training dataset version/hash;
- metric version;
- optimizer and configuration;
- evaluation results;
- compile date and owner.

Do not assume an artifact will remain compatible across every future DSPy release. Test loading and inference as part of an upgrade.

## 13. What DSPy does not do for you

DSPy does not automatically:

- guarantee factual correctness;
- create a representative evaluation dataset;
- define your business success metric;
- protect your application from prompt injection;
- validate every generated value against business rules;
- implement authorization or tenant isolation;
- provide a complete production monitoring platform;
- guarantee that an optimized program generalizes to unseen data;
- fine-tune model weights in its ordinary prompt-optimization workflow.

These remain application and platform engineering responsibilities.

## 14. Production architecture

A practical production flow looks like this:

~~~text
                 OFFLINE / BUILD TIME
  Curated data -> Train/dev split -> DSPy optimizer
                                      |
                                      v
                               Compiled artifact
                                      |
                               Evaluation gate
                                      |
                               Versioned release
                                      |
                 ONLINE / RUNTIME    v
  Client -> API -> Input validation -> DSPy program
                                      |
                                  Ollama/LM
                                      |
                             Output validation
                                      |
                           Business rules/guardrails
                                      |
                              API response
~~~

Recommended controls:

- Pin the DSPy package and model version.
- Keep optimization separate from request-serving processes.
- Do not run expensive compilation during normal API requests.
- Validate inputs and outputs at the application boundary.
- Add timeouts, bounded retries, concurrency limits, and request-size limits.
- Track latency, failures, model calls, token usage where available, and quality feedback.
- Keep sensitive user data out of training/optimization datasets unless approved.
- Evaluate a candidate artifact before promoting it.
- Retain the previous known-good artifact for rollback.
- Use authorization and tenant isolation outside the prompt.
- Treat retrieved documents and user-provided content as untrusted input.

For a FastAPI service, load the selected compiled program during application startup, then expose a narrow application service method. Keep DSPy-specific types out of your public HTTP contract.

## 15. DSPy with RAG and agents

DSPy is not limited to classification or question answering.

You can build a program with multiple stages, for example:

1. Rewrite a user's query.
2. Retrieve relevant documents.
3. Rerank or select evidence.
4. Generate an answer from evidence.
5. Validate the answer or citations.

Each stage can be represented by a Signature and Module. A metric can evaluate the final answer and, where useful, intermediate behavior.

For an agentic workflow, a module may select an action or call a tool. However, the application must still enforce tool permissions, validate arguments, limit execution, and handle failures. Never treat an LLM-generated decision as authorization.

## 16. Common mistakes

1. **Optimizing without a baseline:** you cannot prove improvement.
2. **Using the test set during compilation:** the final score becomes contaminated.
3. **Using a weak metric:** the optimizer learns to maximize the wrong thing.
4. **Using too few examples:** the optimized behavior may be brittle.
5. **Starting with a large optimization budget:** costs time and model calls before the pipeline is understood.
6. **Assuming compilation fine-tunes weights:** prompt/program optimization and weight fine-tuning are different operations.
7. **Skipping output validation:** generated output is still untrusted.
8. **Ignoring model/version changes:** an artifact that worked with one model may behave differently with another.

## 17. Hands-on exercises

### Exercise A — Understand the abstractions

Create a Signature for extracting the following from a support ticket:

- issue category;
- urgency;
- short summary.

Write descriptions for every field. Define which values are allowed for category and urgency.

### Exercise B — Build a baseline

Create at least 30 labeled examples for a classification task. Split them into train, dev, and test sets. Build a `dspy.Predict` program and calculate baseline accuracy.

### Exercise C — Optimize

Run BootstrapFewShot with a deliberately small budget. Compare the baseline and optimized program on the same held-out test set. Record model calls, latency, and accuracy.

### Exercise D — Robustness

Add examples containing typos, sarcasm, very short reviews, long reviews, mixed sentiment, and irrelevant text. Analyze which categories fail.

### Exercise E — Production release

Save the compiled program, record its metadata, load it into a fresh process, and run a regression suite before promoting it.

## 18. Completion checklist

- [ ] I can explain Signature, Module, Program, Metric, Dataset, and Optimizer.
- [ ] I can configure DSPy with local Ollama.
- [ ] I can build a class-based Signature.
- [ ] I can implement a custom Module.
- [ ] I can create DSPy Examples with input fields.
- [ ] I can write a deterministic metric.
- [ ] I can measure a baseline before compiling.
- [ ] I can run BootstrapFewShot.
- [ ] I understand the purpose of MIPROv2.
- [ ] I can evaluate on held-out data.
- [ ] I can save and reload a compiled program.
- [ ] I understand the production controls DSPy does not provide.

---

## Official references

- [DSPy installation and LM setup](https://dspy.ai/getting-started/installation/)
- [DSPy programming with language models](https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/programming/language_models.md)
- [DSPy optimizers](https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/optimization/optimizers.md)
- [MIPROv2 API reference](https://github.com/stanfordnlp/dspy/blob/main/docs/docs/api/optimizers/MIPROv2.md)
- [DSPy FAQ: saving and loading](https://github.com/stanfordnlp/dspy/blob/main/docs/docs/faqs.md)
