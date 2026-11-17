"""Compile a small sentiment program with DSPy BootstrapFewShot.

Run from the repository root:
    python examples/dspy/optimize_sentiment.py

Optimization makes extra LM calls. Start with this tiny budget when learning.
Do not use the final test set as optimizer input.
"""

from pathlib import Path

import dspy

from sentiment_baseline import (
    SentimentProgram,
    build_dataset,
    evaluate,
    sentiment_metric,
)


def main():
    dspy.configure(lm=dspy.LM("ollama_chat/llama3.2:3b"))

    examples = build_dataset()
    trainset = examples[:9]
    devset = examples[9:12]
    testset = examples[12:]

    student = SentimentProgram()
    baseline = evaluate(student, devset)
    print(f"Baseline development accuracy: {baseline:.2%}")

    optimizer = dspy.BootstrapFewShot(
        metric=sentiment_metric,
        max_bootstrapped_demos=2,
        max_labeled_demos=2,
        max_rounds=1,
    )

    optimized = optimizer.compile(
        student=student,
        trainset=trainset,
    )

    optimized_dev = evaluate(optimized, devset)
    print(f"Optimized development accuracy: {optimized_dev:.2%}")

    # This tiny teaching dataset is not sufficient for a meaningful quality claim.
    # The test split is printed for demonstration only; use a larger held-out set
    # for real model selection and release decisions.
    print(f"Held-out test accuracy: {evaluate(optimized, testset):.2%}")

    output_path = Path("artifacts")
    output_path.mkdir(exist_ok=True)
    optimized.save(str(output_path / "sentiment_optimized.json"))
    print(f"Saved compiled program to {output_path / 'sentiment_optimized.json'}")


if __name__ == "__main__":
    main()
