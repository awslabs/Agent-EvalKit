"""Model clients. Every stage accepts any object that satisfies `ModelClient`.

- `OpenAICompatClient`: any OpenAI compatible endpoint (vLLM, SGLang, LiteLLM, hosted APIs).
- `BedrockConverseClient`: Amazon Bedrock Converse API, any model id (needs the `[bedrock]` extra).
- `MockClient`: deterministic canned replies for every stage, for tests and dry runs.

Use `make_client(...)` in code, or `add_backend_args(parser)` plus `client_from_args(args)` in a CLI.
"""
from judge_data.clients.base import CachedClient, ModelClient, Result
from judge_data.clients.factory import BACKENDS, add_backend_args, client_from_args, make_client

__all__ = ["BACKENDS", "CachedClient", "ModelClient", "Result", "add_backend_args",
           "client_from_args", "make_client"]
