"""Record schemas for training JSONL.

Two formats are supported:

    prompt_completion (default, used for the judge model):
        {"id": "...", "prompt": [<messages>], "completion": [<assistant message>]}

    messages (plain chat SFT, loss on the whole sequence):
        {"id": "...", "messages": [<messages>]}

A message is {"role": ..., "content": ...}. Extra keys on a message (for
example tool call fields understood by the chat template) are kept. Extra
top-level keys such as "meta" are allowed and ignored by training.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

PROMPT_END_ROLES = {"user", "tool"}


class Message(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: str
    content: str


class PromptCompletionExample(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    prompt: list[Message] = Field(min_length=1)
    completion: list[Message] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_roles(self) -> "PromptCompletionExample":
        if self.prompt[-1].role not in PROMPT_END_ROLES:
            raise ValueError(
                f"prompt must end with a {sorted(PROMPT_END_ROLES)} message, "
                f"got '{self.prompt[-1].role}'"
            )
        if any(m.role != "assistant" for m in self.completion):
            raise ValueError("completion must contain only assistant messages")
        return self


class MessagesExample(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    messages: list[Message] = Field(min_length=1)


Example = PromptCompletionExample | MessagesExample


def parse_example(record: dict[str, Any]) -> Example:
    """Validate a raw JSONL record against the matching schema."""
    if "prompt" in record or "completion" in record:
        return PromptCompletionExample(**record)
    if "messages" in record:
        return MessagesExample(**record)
    raise ValueError("record has neither 'prompt'/'completion' nor 'messages'")
