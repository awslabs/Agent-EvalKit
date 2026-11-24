"""Build a `ModelClient` from a backend name or from parsed CLI flags."""
from __future__ import annotations

import argparse
import json

from judge_data.clients.base import ModelClient

BACKENDS = ("vllm", "openai", "bedrock", "mock")


def make_client(backend: str, *, model_id: str | None = None, base_url: str | None = None,
                api_key: str | None = None, cache_path: str | None = "llm_cache.sqlite",
                concurrency: int | None = None, chat_template_kwargs: dict | None = None,
                region: str | None = None, aws_profile: str | None = None,
                role_arn: str | None = None, send_temperature: bool = True,
                additional_model_request_fields: dict | None = None) -> ModelClient:
    """`backend` is one of vllm, openai, bedrock, mock.

    vllm and openai both talk to an OpenAI compatible endpoint. vllm also sends
    `chat_template_kwargs={"enable_thinking": false}` by default, openai sends nothing extra.
    """
    if backend in ("vllm", "openai"):
        from judge_data.clients.openai_compat import OpenAICompatClient
        if not base_url:
            raise ValueError(f"the {backend} backend needs --base-url")
        if not model_id:
            raise ValueError(f"the {backend} backend needs --model-id")
        return OpenAICompatClient(base_url=base_url, model_id=model_id, api_key=api_key,
                                  cache_path=cache_path, concurrency=concurrency or 256,
                                  chat_template_kwargs=chat_template_kwargs,
                                  disable_thinking=backend == "vllm")
    if backend == "bedrock":
        from judge_data.clients.bedrock import BedrockAccount, BedrockConverseClient
        if not model_id:
            raise ValueError("the bedrock backend needs --model-id")
        regions = [r.strip() for r in (region or "").split(",") if r.strip()] or [None]
        profiles = [p.strip() for p in (aws_profile or "").split(",") if p.strip()] or [None]
        accounts = [BedrockAccount(region=r, profile=p, role_arn=role_arn,
                                   max_concurrent=concurrency or 16)
                    for p in profiles for r in regions]
        return BedrockConverseClient(model_id=model_id, accounts=accounts, cache_path=cache_path,
                                     send_temperature=send_temperature,
                                     additional_model_request_fields=additional_model_request_fields)
    if backend == "mock":
        from judge_data.clients.mock import MockClient
        return MockClient(model_id=model_id or "mock")
    raise ValueError(f"unknown backend {backend!r}, use one of {', '.join(BACKENDS)}")


def add_backend_args(ap: argparse.ArgumentParser) -> None:
    """Add the shared model backend flags to a parser."""
    g = ap.add_argument_group("model backend")
    g.add_argument("--backend", default="vllm", choices=BACKENDS,
                   help="vllm or openai (OpenAI compatible HTTP), bedrock (Converse API), "
                        "or mock (canned replies for tests). Default: vllm")
    g.add_argument("--model-id", default=None, help="Model name as the endpoint knows it (required "
                   "except for mock)")
    g.add_argument("--base-url", default=None,
                   help="OpenAI compatible base URL ending in /v1. Several replicas of one model "
                        "may be comma separated")
    g.add_argument("--api-key", default=None, help="Bearer token for the endpoint, if it needs one")
    g.add_argument("--cache", default="llm_cache.sqlite",
                   help="SQLite reply cache path, or 'none' (default: llm_cache.sqlite)")
    g.add_argument("--concurrency", type=int, default=None,
                   help="Requests in flight: total for HTTP backends (default 256), per credential "
                        "set for bedrock (default 16)")
    g.add_argument("--chat-template-kwargs", default=None,
                   help='HTTP backends: JSON chat_template_kwargs, e.g. \'{"enable_thinking": true}\'. '
                        "With thinking on, reasoning before </think> is dropped from replies")
    g.add_argument("--region", default=None, help="bedrock: AWS region, or several comma separated")
    g.add_argument("--aws-profile", default=None,
                   help="bedrock: AWS profile, or several comma separated")
    g.add_argument("--role-arn", default=None, help="bedrock: IAM role to assume for every call")
    g.add_argument("--no-temperature", action="store_true",
                   help="bedrock: never send temperature, for models that reject it")
    g.add_argument("--additional-model-request-fields", default=None,
                   help="bedrock: JSON passed as additionalModelRequestFields")


def client_from_args(a: argparse.Namespace) -> ModelClient:
    def js(v):
        return json.loads(v) if v else None
    return make_client(
        a.backend, model_id=a.model_id, base_url=a.base_url, api_key=a.api_key,
        cache_path=a.cache, concurrency=a.concurrency,
        chat_template_kwargs=js(a.chat_template_kwargs), region=a.region,
        aws_profile=a.aws_profile, role_arn=a.role_arn, send_temperature=not a.no_temperature,
        additional_model_request_fields=js(a.additional_model_request_fields))
