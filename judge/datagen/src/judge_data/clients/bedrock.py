"""Generic Amazon Bedrock Converse client. Install with the `[bedrock]` extra.

Takes any `model_id` the Converse API serves. Requests can be spread round robin over several
credential sets (AWS profiles, regions, or roles to assume), each with its own concurrency limit.
Role credentials are refreshed automatically on long runs.

Model specific request fields (for example a reasoning or thinking switch) go through
`additional_model_request_fields`. Some models reject `temperature`; pass `send_temperature=False`
for those.
"""
from __future__ import annotations

import logging
import random
import threading
import time
from dataclasses import dataclass

from judge_data.clients.base import CachedClient, Result

logger = logging.getLogger(__name__)

RETRYABLE = {
    "ThrottlingException", "TooManyRequestsException", "ServiceUnavailableException",
    "ServiceQuotaExceededException", "ModelTimeoutException", "ModelNotReadyException",
    "InternalServerException", "ExpiredTokenException", "ConnectionError",
    "ReadTimeoutError", "EndpointConnectionError", "ConnectTimeoutError",
}
MAX_ATTEMPTS = 8


@dataclass
class BedrockAccount:
    """One credential set. All fields optional: the default is the ambient AWS credentials."""
    region: str | None = None
    profile: str | None = None
    role_arn: str | None = None
    max_concurrent: int = 16


def _session(acct: BedrockAccount):
    import boto3

    base = boto3.Session(profile_name=acct.profile, region_name=acct.region)
    if not acct.role_arn:
        return base
    from botocore.credentials import RefreshableCredentials
    from botocore.session import get_session

    def refresh():
        r = base.client("sts").assume_role(RoleArn=acct.role_arn,
                                           RoleSessionName="judge-data")["Credentials"]
        return {"access_key": r["AccessKeyId"], "secret_key": r["SecretAccessKey"],
                "token": r["SessionToken"], "expiry_time": r["Expiration"].isoformat()}

    creds = RefreshableCredentials.create_from_metadata(
        metadata=refresh(), refresh_using=refresh, method="sts-assume-role")
    bs = get_session()
    bs._credentials = creds
    if acct.region:
        bs.set_config_variable("region", acct.region)
    return boto3.Session(botocore_session=bs)


class BedrockConverseClient(CachedClient):
    def __init__(self, model_id: str, accounts: list[BedrockAccount] | None = None,
                 cache_path: str | None = "llm_cache.sqlite", send_temperature: bool = True,
                 additional_model_request_fields: dict | None = None,
                 read_timeout: int = 300):
        if not model_id:
            raise ValueError("bedrock backend requires a model id")
        try:
            from botocore.config import Config
        except ImportError as e:  # pragma: no cover - depends on the environment
            raise ImportError("the bedrock backend needs boto3: pip install 'evalkit-judge-data[bedrock]'") from e
        accounts = accounts or [BedrockAccount()]
        super().__init__(model_id=model_id, cache_path=cache_path,
                         concurrency=sum(a.max_concurrent for a in accounts))
        cfg = Config(retries={"max_attempts": 2, "mode": "standard"},
                     read_timeout=read_timeout, connect_timeout=20)
        self._clients = []
        self._sems = []
        for a in accounts:
            s = _session(a)
            self._clients.append(s.client("bedrock-runtime", region_name=a.region or s.region_name,
                                          config=cfg))
            self._sems.append(threading.Semaphore(a.max_concurrent))
        self._i = 0
        self._ilock = threading.Lock()
        self.send_temperature = send_temperature
        self.extra = additional_model_request_fields

    def _key_extra(self) -> object:
        return {"extra": self.extra, "temp": self.send_temperature}

    def _pick(self) -> int:
        with self._ilock:
            i = self._i % len(self._clients)
            self._i += 1
        return i

    def _call(self, prompt: str, max_tokens: int, temperature: float | None) -> Result:
        inf: dict = {"maxTokens": max_tokens}
        if temperature is not None and self.send_temperature:
            inf["temperature"] = temperature
        kw = dict(modelId=self.model_id,
                  messages=[{"role": "user", "content": [{"text": prompt}]}],
                  inferenceConfig=inf)
        if self.extra:
            kw["additionalModelRequestFields"] = self.extra
        last = "unknown"
        for attempt in range(MAX_ATTEMPTS):
            i = self._pick()
            with self._sems[i]:
                try:
                    r = self._clients[i].converse(**kw)
                    blocks = (r.get("output", {}).get("message", {}).get("content") or [])
                    text = "".join(b["text"] for b in blocks if isinstance(b, dict) and "text" in b)
                    u = r.get("usage", {})
                    if not text:
                        stop = r.get("stopReason")
                        if stop in ("content_filtered", "guardrail_intervened"):
                            return Result(text="", ok=False, error=stop, filtered=True)
                        return Result(text="", ok=False, error=f"no text block, stopReason={stop}",
                                      input_tokens=u.get("inputTokens", 0),
                                      output_tokens=u.get("outputTokens", 0))
                    return Result(text=text, input_tokens=u.get("inputTokens", 0),
                                  output_tokens=u.get("outputTokens", 0))
                except Exception as e:  # noqa: BLE001
                    last = f"{type(e).__name__}: {str(e)[:200]}"
                    code = (getattr(e, "response", None) or {}).get("Error", {}).get("Code", "")
                    if type(e).__name__ not in RETRYABLE and code not in RETRYABLE:
                        return Result(text="", ok=False, error=last)
            time.sleep(min(2 ** attempt + random.uniform(0, 1.5), 45))
        return Result(text="", ok=False, error=f"exhausted retries: {last}")
