# LLM observability examples

## Local Ollama + Langfuse

The example instruments a local Ollama chat call with a parent span and a nested model generation.

### 1. Install dependencies

From the repository root, activate your virtual environment and install the project requirements:

~~~bash
pip install -r requirements.txt
~~~

### 2. Start Ollama

~~~bash
ollama pull llama3.2:3b
~~~

Ensure the Ollama service is running and responds at http://localhost:11434.

### 3. Configure Langfuse

Create a Langfuse project and configure the project's API keys:

~~~bash
export LANGFUSE_PUBLIC_KEY="your-public-key"
export LANGFUSE_SECRET_KEY="your-secret-key"
export LANGFUSE_BASE_URL="https://cloud.langfuse.com"
~~~

Use the correct base URL for your region or self-hosted instance. Never commit these values.

### 4. Run the example

~~~bash
python examples/observability/ollama_langfuse_trace.py
~~~

Open your Langfuse project and inspect the trace. You should see an application span with a nested generation observation.

### Notes

- This example uses the current Langfuse Python SDK observation context-manager API.
- It records a synthetic learning question. Do not enable raw production input/output capture until privacy and retention requirements have been reviewed.
- Token counts and duration fields come from Ollama's response. Availability depends on the response and installed Ollama SDK version.
- The example has not been executed as part of the GitHub commit workflow. Run it in your environment and verify the trace before adapting it for production.
