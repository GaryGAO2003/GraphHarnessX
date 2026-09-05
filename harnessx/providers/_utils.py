# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
import uuid
from typing import Any, Callable

from ..core.events import Message, ToolCall, ToolSchema


def to_openai_tools(tools: list[ToolSchema]) -> list[dict]:
    """Convert ToolSchema list to the OpenAI function-calling wire format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.input_schema,
            },
        }
        for t in tools
    ]


def parse_tool_calls(raw_tool_calls) -> list[ToolCall]:
    """Parse an OpenAI-format tool_calls list into ToolCall dataclasses."""
    result = []
    for tc in raw_tool_calls:
        try:
            inp = json.loads(tc.function.arguments) if tc.function.arguments else {}
        except json.JSONDecodeError:
            inp = {}
        result.append(
            ToolCall(
                id=tc.id or str(uuid.uuid4()),
                name=tc.function.name,
                input=inp,
            )
        )
    return result


def count_tokens(messages: list[Message]) -> int:
    from ..core.events import rough_token_count

    return rough_token_count(messages)


def to_openai_content(content: "str | list") -> "str | list | None":
    """Convert internal content (Anthropic format) to OpenAI/litellm wire format.

    Anthropic image block::
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "..."}}
    becomes::
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
    """
    if isinstance(content, str):
        return content or None
    result = []
    for block in content:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype == "text":
            result.append({"type": "text", "text": block.get("text", "")})
        elif btype == "image":
            src = block.get("source", {})
            if src.get("type") == "base64":
                url = f"data:{src['media_type']};base64,{src['data']}"
                result.append({"type": "image_url", "image_url": {"url": url}})
            elif src.get("type") == "url":
                result.append({"type": "image_url", "image_url": {"url": src["url"]}})
    return result or None


def as_text_delta(value: Any) -> str:
    """Best-effort conversion of provider delta payloads to text."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                # OpenAI-style content list chunks may look like:
                # {"type":"text","text":"..."} or {"type":"output_text","text":"..."}
                t = item.get("text")
                if isinstance(t, str):
                    parts.append(t)
        return "".join(parts)
    return ""


def emit_stream_delta(
    stream_callback: "Callable[[object], None] | None",
    content: str,
    *,
    kind: str = "token",
) -> None:
    """Emit one stream delta to callback with backward compatibility.

    New callback payload shape:
      {"type": "token" | "thinking", "content": "..."}

    Legacy callbacks (CLI) accept plain string deltas only. We fall back to
    string mode for token deltas and ignore non-token kinds on legacy callbacks.
    """
    if stream_callback is None or not content:
        return
    if kind not in {"token", "thinking"}:
        return

    mode = getattr(stream_callback, "__harnessx_stream_mode__", None)
    if mode == "structured":
        try:
            stream_callback({"type": kind, "content": content})
        except Exception:
            return
        return
    if mode == "text":
        if kind != "token":
            return
        try:
            stream_callback(content)
        except Exception:
            return
        return

    try:
        stream_callback({"type": kind, "content": content})
        try:
            setattr(stream_callback, "__harnessx_stream_mode__", "structured")
        except Exception:
            pass
        return
    except Exception:
        try:
            setattr(stream_callback, "__harnessx_stream_mode__", "text")
        except Exception:
            pass
        if kind != "token":
            return
    try:
        stream_callback(content)
    except Exception:
        # Stream callback must be best-effort only; never fail the run for UI I/O.
        return


#: Statuses a gateway returns for "try again", not "your request is wrong".
#: 429 is rate limiting; 500/502/503/504 are the proxy or an upstream vLLM worker
#: being briefly unavailable; 529 is Anthropic's overloaded signal.
_RETRYABLE_STATUS = (429, 500, 502, 503, 504, 529)


def classify_retryable(exc: Exception) -> tuple[int | None, bool]:
    """``(status, retryable)`` for a provider exception.

    Lives here because both OpenAI-protocol clients need the same answer and had
    drifted apart: ``LiteLLMProvider`` caught only ``RateLimitError``, so a 502 —
    the failure that actually dominates when the gateway wobbles — killed the run
    on the first hit while ``OpenAIProvider`` retried it six times against the same
    endpoint. Sharing the predicate is what keeps that gap from reopening.

    Timeouts count as retryable however the gateway spells them: providers return
    "timed out", nginx returns "504 Gateway Time-out".
    """
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if not isinstance(status, int):
        status = None
    text = str(exc).lower()
    # A network-level failure carries no status code and says nothing about rates
    # or timeouts — the OpenAI SDK raises APIConnectionError with the message
    # "Connection error." and nothing else — so a status/keyword test rejects the
    # single most obviously transient class there is. One 30-second blip killed six
    # rollouts outright across two arms of M14, unevenly (four and two), which puts
    # a bias straight into an arm comparison. Matched by exception class name as
    # well as text because the message alone is that bare.
    #
    # Class first, text second. Both string tests miss ``ConnectionResetError``:
    # ``"connectionreseterror"`` does not contain ``"connectionerror"``, and on a
    # Chinese Windows the message is "[WinError 10054] 远程主机强迫关闭了一个现有的
    # 连接。" — localised, so it carries no English keyword at all. A predicate
    # built on English substrings silently answers "not retryable" for the most
    # transient failure there is, which is the same shape as the M14 bug one
    # locale over. ``ConnectionResetError`` subclasses ``ConnectionError``
    # subclasses ``OSError``; isinstance says so in every language.
    connection = (
        isinstance(exc, (ConnectionError, TimeoutError))
        or "connection" in text
        or "connectionerror" in type(exc).__name__.lower()
        or "remote end closed" in text
        or "server disconnected" in text
    )
    retryable = (
        status in _RETRYABLE_STATUS
        or connection
        or "rate" in text
        or "timeout" in text
        or "timed out" in text
        or "time-out" in text
    )
    return status, retryable


#: Hosts that are a vendor's own API rather than the LiteLLM gateway. Reaching one
#: of these bypasses the gateway's billing, quota and audit trail, so a run that
#: used it produces numbers that cannot be reconciled with any other run — which is
#: why it is refused at construction rather than warned about at call time.
_DIRECT_VENDOR_HOSTS = (
    "api.openai.com",
    "api.anthropic.com",
    "api.deepseek.com",
    "api.mistral.ai",
    "api.together.xyz",
    "api.groq.com",
    "api.x.ai",
    "generativelanguage.googleapis.com",
    "openai.azure.com",
    "bedrock-runtime",
)


def assert_gateway_base_url(base_url: str | None, provider: str) -> None:
    """Refuse a base_url that points at a vendor's own endpoint.

    ``None`` is allowed: it means "resolve from the environment", and the env in
    this project points at the gateway. Only an explicit vendor host is refused,
    so unit tests that construct a provider with no base_url are unaffected.

    The policy this enforces is about *where the bytes go*, not what the client
    class is called. ``OpenAIProvider`` aimed at the gateway is compliant — the
    gateway speaks the OpenAI protocol, which is the only reason that class is in
    the chain — while ``LiteLLMProvider`` aimed at ``api.deepseek.com`` is not,
    despite the name. Checking the URL is the only check that tracks the rule.
    """
    if not base_url:
        return
    host = str(base_url).split("//", 1)[-1].split("/", 1)[0].lower()
    for bad in _DIRECT_VENDOR_HOSTS:
        if bad in host:
            raise ValueError(
                f"{provider}: base_url {base_url!r} is a direct vendor endpoint. "
                f"All traffic must go through the LiteLLM gateway. If the gateway "
                f"is unhealthy, wait for it, switch to another model name on it, or "
                f"shrink the run — do not route around it."
            )
