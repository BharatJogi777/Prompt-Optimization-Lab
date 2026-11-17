"""A small DSPy sentiment classifier using a local Ollama model.

Run from the repository root after installing DSPy and pulling llama3.2:3b:
    ollama pull llama3.2:3b
    python examples/dspy/sentiment_baseline.py

This is a learning example, not a production classifier.
"""

import dspy


class SentimentSignature(dspy.Signature):
    """Classify the sentiment expressed in a customer review."""
    review: str = dspy.InputField(desc="The customer's review")
    sentiment: str = dspy.OutputField(
        desc="Exactly one of: positive, negative, neutral"
    )


class SentimentProgram(dspy.Module):
    def __init__(self):
        super().__init__()
        self.classify = dspy.Predict(SentimentSignature)

    def forward(self, review: str):
        return self.classify(review=review)


def normalize_label(value: str) -> str:
    return value.strip().lower().rstrip(".")


def sentiment_metric(example, prediction, trace=None) -> bool:
    allowed = {"positive", "negative", "neutral"}
    expected = normalize_label(example.sentiment)
    actual = normalize_label(prediction.sentiment)
    return expected in allowed and actual == expected


def build_dataset():
    rows = [
        ("The delivery was quick and the product works perfectly.", "positive"),
        ("Excellent quality. I would definitely buy it again.", "positive"),
        ("Customer support solved my issue immediately.", "positive"),
        ("The packaging was neat and everything arrived safely.", "positive"),
        ("This is one of the best purchases I have made.", "positive"),
        ("The product stopped working after one day.", "negative"),
        ("The delivery was late and the box was damaged.", "negative"),
        ("Customer support never replied to my messages.", "negative"),
        ("The item is broken and completely unusable.", "negative"),
        ("Very poor quality for the price.", "negative"),
        ("The package arrived today.", "neutral"),
        ("The product is black and has two buttons.", "neutral"),
        ("I received the replacement unit this morning.", "neutral"),
        ("The order contains three separate items.", "neutral"),
        ("The manual is included inside the box.", "neutral"),
    ]

    examples = [
        dspy.Example(review=review, sentiment=sentiment).with_inputs("review")
        for review, sentiment in rows
    ]
    return examples


def evaluate(program, dataset):
    if not dataset:
        raise ValueError("Evaluation dataset cannot be empty")

    correct = 0
    for example in dataset:
        prediction = program(**example.inputs())
        correct += int(sentiment_metric(example, prediction))

    return correct / len(dataset)


def main():
    lm = dspy.LM("ollama_chat/llama3.2:3b")
    dspy.configure(lm=lm)

    examples = build_dataset()
    trainset = examples[:9]
    devset = examples[9:12]
    testset = examples[12:]

    program = SentimentProgram()

    print("Evaluating baseline on development examples...")
    print(f"Development accuracy: {evaluate(program, devset):.2%}")

    print("\nSample prediction:")
    result = program(
        review="The service was excellent and my issue was resolved quickly."
    )
    print(result.sentiment)

    print("\nFinal held-out test score (run only after decisions are complete):")
    print(f"Test accuracy: {evaluate(program, testset):.2%}")


if __name__ == "__main__":
    main()
