# 03 — Prompt Testing with Promptfoo

## Learning objectives

By the end of this module, you should be able to:
- Explain why prompts need automated tests.
- Install and run Promptfoo.
- Configure a local Ollama model as a provider.
- Compare multiple prompt variants on identical test cases.
- Add deterministic assertions.
- Read evaluation results and investigate failures.
- Understand the limits of model-graded assertions.

## 1. What is Promptfoo?

Promptfoo is an open-source tool for evaluating prompts and LLM applications. It runs test cases against one or more model providers, applies assertions to outputs, and reports results.

Think of it as a test runner for model behavior:

~~~text
Prompt variants + test dataset + model provider
                    |
                    v
              Promptfoo runner
                    |
                    v
       Model outputs for each test case
                    |
                    v
            Assertions / graders
                    |
                    v
          Results and comparisons
~~~

Promptfoo does not magically discover the universally best prompt. It helps you run controlled comparisons and detect regressions.

Official documentation: https://www.promptfoo.dev/docs/

## 2. Install and verify

Install the CLI using the current official installation instructions. One common npm-based installation is:

~~~bash
npm install -g promptfoo
promptfoo --version
~~~

If Node.js/npm is not installed, install a supported Node.js release first. Promptfoo is a separate CLI tool; it does not replace your Python application.

## 3. Start Ollama

In one terminal:

~~~bash
ollama serve
~~~

In another terminal:

~~~bash
ollama pull llama3.2:3b
ollama list
curl http://localhost:11434/api/tags
~~~

Confirm the model name exactly as it appears in your local Ollama installation.

## 4. Create a project

From the repository root:

~~~bash
mkdir -p promptfoo
cd promptfoo
promptfoo init
~~~

The initialization wizard may change between releases. If it generates a sample configuration, inspect it and adapt it to the examples below rather than assuming every generated option is identical.

## 5. Configure an Ollama provider

Promptfoo provider identifiers and configuration fields can evolve. Consult the current Ollama provider documentation:
https://www.promptfoo.dev/docs/providers/ollama/

A typical configuration uses an Ollama chat provider and the local model name. For example, create a prompt file called prompts.txt with two variants:

~~~text
You are a sentiment classifier.
Classify the review as positive, negative, or neutral.
Return only the label.

Review: {{review}}
~~~

~~~text
Classify the sentiment of the review below.

Choose exactly one label:
- positive: the review expresses satisfaction or praise
- negative: the review expresses dissatisfaction or criticism
- neutral: the review is factual or has no clear sentiment

Return only one lowercase label: positive, negative, or neutral.

Review:
{{review}}
~~~

The second variant makes label definitions explicit. It is a hypothesis to test, not automatically a better prompt.

## 6. Create representative test cases

Create tests.yaml:

~~~yaml
description: Sentiment classification prompt comparison

providers:
  - ollama:chat:llama3.2:3b

prompts:
  - file://prompts.txt

tests:
  - vars:
      review: "I love this product. It works perfectly."
    assert:
      - type: equals
        value: positive

  - vars:
      review: "The package arrived broken and support did not help."
    assert:
      - type: equals
        value: negative

  - vars:
      review: "The package arrived on Tuesday."
    assert:
      - type: equals
        value: neutral
~~~

Important: verify the provider syntax against the installed Promptfoo version's Ollama provider page. Provider names and options are version-sensitive. If your installed version expects a different provider identifier, follow its current docs.

## 7. Run the evaluation

From the promptfoo directory:

~~~bash
promptfoo eval -c tests.yaml
~~~

Open the local results viewer if the CLI offers it, or inspect the terminal output and generated evaluation artifacts. Do not commit generated reports containing private inputs.

For each test, inspect:
- Input variables.
- Prompt variant.
- Provider/model.
- Raw output.
- Assertion result.
- Error details, if any.

## 8. Understand assertions

An assertion defines a condition that the output must satisfy.

Useful assertion categories include:
- Exact equality for fixed labels.
- Contains / not-contains checks.
- Regular-expression checks.
- JSON validity and schema checks.
- Similarity checks.
- Model-graded rubric assertions.

Prefer deterministic assertions when possible. A model-graded assertion is useful for nuanced quality, but it can be inconsistent. Calibrate it against human-reviewed examples and do not treat its score as ground truth.

## 9. Analyze a failure

Suppose a prompt returns:

~~~text
The sentiment is positive because the reviewer says they love it.
~~~

But your contract says return only the label. The semantic classification is correct, but the output contract failed.

This distinction matters in production. Track task correctness and output-format correctness separately.

A useful failure taxonomy:
- Wrong classification.
- Invalid or extra output.
- Missing answer.
- Unsupported claim.
- Failure to abstain.
- Timeout/provider error.

## 10. Controlled experiment

Run the same test cases against both prompt variants. Keep the model and generation settings fixed.

Record:
- Prompt variant name.
- Prompt text or hash.
- Model identifier.
- Test dataset version.
- Assertion configuration.
- Pass rate.
- Per-category failures.
- Latency and token usage if available.

Do not change the prompt, model, temperature, and dataset simultaneously. You will not know which change caused the result.

## 11. Exercises

1. Add at least 10 synthetic sentiment test cases.
2. Include ambiguous and borderline reviews.
3. Add a third prompt variant with two few-shot examples.
4. Run all variants against the same tests.
5. Add an assertion that rejects extra explanatory text.
6. Compare aggregate pass rate and category-level failures.
7. Change only one prompt feature and rerun.
8. Write a short experiment report explaining whether the candidate should be promoted.

## 12. Production considerations

- Pin and record the Promptfoo version used by the project.
- Keep test datasets versioned and free of sensitive data.
- Keep model and provider configuration explicit.
- Separate deterministic assertions from model-graded evaluations.
- Preserve a baseline evaluation before prompt changes.
- Run regression tests before release.
- Review failures rather than relying only on aggregate scores.
- Keep API keys in environment variables or a secret manager.
- Treat prompt injection and unsafe tool behavior as application security concerns, not merely prompt wording problems.

## Completion checklist

- [ ] Promptfoo CLI installed.
- [ ] Ollama provider configured and verified.
- [ ] At least two prompt variants evaluated.
- [ ] Test cases cover normal and edge inputs.
- [ ] Deterministic assertions are understood.
- [ ] Failures are categorized.
- [ ] Baseline results are recorded.
- [ ] Experiment report is written.

## Key takeaway

Promptfoo gives you a repeatable way to test prompt behavior. It does not replace good datasets, meaningful metrics, human review, or application-level safety controls.
