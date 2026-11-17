"""Trace a local Ollama chat request with the Langfuse Python SDK.

Configure LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY and LANGFUSE_BASE_URL.
Then run:
    python examples/observability/ollama_langfuse_trace.py

Use synthetic data for this learning example. Review privacy and redaction
requirements before tracing real user prompts or model responses.
"""

import os

import ollama
from langfuse import get_client


MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def run_example() -> str:
    client = ollama.Client(host=OLLAMA_HOST)
    langfuse = get_client()

    question = "Explain why database indexes can improve read performance."

    try:
        with langfuse.start_as_current_observation(
            as_type="span",
            name="ollama-chat-request",
            input={"question": question},
            metadata={
                "environment": "local-learning",
                "provider": "ollama",
            },
        ) as request_span:
            messages = [
                {
                    "role": "system",
                    "content": "You are a concise backend engineering tutor.",
                },
                {"role": "user", "content": question},
            ]

            with langfuse.start_as_current_observation(
                as_type="generation",
                name="ollama-generation",
                model=MODEL,
                input={"messages": messages},
                metadata={"provider": "ollama"},
            ) as generation:
                response = client.chat(
                    model=MODEL,
                    messages=messages,
                    options={"temperature": 0},
                )

                answer = response.message.content
                prompt_tokens = response.prompt_eval_count
                completion_tokens = response.eval_count

                usage = {}
                if prompt_tokens is not None:
                    usage["input"] = prompt_tokens
                if completion_tokens is not None:
                    usage["output"] = completion_tokens

                generation.update(
                    output=answer,
                    usage_details=usage or None,
                    metadata={
                        "total_duration_ns": response.total_duration,
                        "load_duration_ns": response.load_duration,
                        "prompt_eval_duration_ns": response.prompt_eval_duration,
                        "eval_duration_ns": response.eval_duration,
                    },
                )

            request_span.update(
                output={"answer": answer},
                metadata={"status": "success"},
            )

        return answer
    finally:
        # Important for scripts and short-lived processes.
        langfuse.flush()


if __name__ == "__main__":
    if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY"):
        raise SystemExit(
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY before running."
        )

    print(run_example())
