# Copyright 2026 Darwin-Agent
# SPDX-License-Identifier: MIT
"""Every run goes through the LiteLLM gateway; nothing talks to a vendor directly.

The rule is about the URL, not the class name. A campaign was re-pointed at
``api.deepseek.com`` while still using ``LiteLLMProvider`` — the class name stayed
"litellm" the whole time and the run was off-ledger anyway. Conversely the AEGIS
chain runs on ``OpenAIProvider`` aimed at the gateway, which is compliant, because
the gateway speaks the OpenAI protocol.

So these tests assert on base_url in both directions for both clients, and pin the
retry gap that made the two behave differently against the same endpoint.
"""

from __future__ import annotations

import pytest

from harnessx.providers._utils import assert_gateway_base_url, classify_retryable
from harnessx.providers.litellm_provider import LiteLLMProvider
from harnessx.providers.openai_provider import OpenAIProvider

GATEWAY = "https://litellm.yangtzeailab.com/v1"


class _Err(Exception):
    def __init__(self, msg: str, status: int | None = None):
        super().__init__(msg)
        if status is not None:
            self.status_code = status


# --- the guard itself -------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://api.deepseek.com/v1",
        "https://api.openai.com/v1",
        "https://api.anthropic.com",
        "http://api.groq.com/openai/v1",
        "https://generativelanguage.googleapis.com/v1beta",
    ],
)
def test_direct_vendor_endpoints_are_refused(url):
    with pytest.raises(ValueError, match="direct vendor endpoint"):
        assert_gateway_base_url(url, "T")


@pytest.mark.parametrize("url", [GATEWAY, "https://litellm.yangtzeailab.com", None, ""])
def test_gateway_and_unset_are_allowed(url):
    assert_gateway_base_url(url, "T")  # must not raise


# --- wired into both clients ------------------------------------------------


def test_openai_provider_refuses_a_vendor_endpoint():
    """The class is named for the protocol, not the vendor — pointing it at the
    vendor is what the rule forbids."""
    with pytest.raises(ValueError, match="direct vendor endpoint"):
        OpenAIProvider(model="deepseek-v4-pro", base_url="https://api.deepseek.com/v1")


def test_openai_provider_accepts_the_gateway():
    """The AEGIS chain's actual construction. If this ever fails, the campaign stops."""
    p = OpenAIProvider(model="DeepSeek-V4-Flash", base_url=GATEWAY)
    assert p.base_url == GATEWAY


def test_litellm_provider_refuses_a_vendor_endpoint_via_kwargs():
    """``api_base`` arrives through the kwargs catch-all, which is how the August
    re-point slipped through unnoticed."""
    with pytest.raises(ValueError, match="direct vendor endpoint"):
        LiteLLMProvider(model="deepseek-v4-pro", api_base="https://api.deepseek.com/v1")


def test_litellm_provider_accepts_the_gateway():
    p = LiteLLMProvider(model="DeepSeek-V4-Flash", api_base=GATEWAY)
    assert p.kwargs["api_base"] == GATEWAY


# --- the retry gap ----------------------------------------------------------


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504, 529])
def test_gateway_5xx_is_retryable(status):
    """502 dominates when the gateway wobbles. ``LiteLLMProvider`` used to catch only
    ``RateLimitError``, so it died on the first 502 while ``OpenAIProvider`` retried
    the same failure six times against the same endpoint."""
    seen, retryable = classify_retryable(_Err("upstream", status))
    assert (seen, retryable) == (status, True)


@pytest.mark.parametrize("text", ["Request timed out", "504 Gateway Time-out", "read timeout"])
def test_timeouts_are_retryable_however_spelled(text):
    assert classify_retryable(_Err(text))[1] is True


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
def test_client_errors_are_not_retried(status):
    """Retrying a malformed or unauthorised request just burns the budget six times."""
    assert classify_retryable(_Err("bad request", status))[1] is False


def test_a_status_less_object_falls_back_to_the_message():
    """litellm wraps some failures without a status_code; the text still carries it."""
    assert classify_retryable(_Err("rate limit exceeded"))== (None, True)


class _ConnErr(Exception):
    """Shaped like openai.APIConnectionError: no status, and the bare message."""


_ConnErr.__name__ = "APIConnectionError"


def test_a_network_level_failure_is_retryable():
    """The most obviously transient class there is, and the predicate rejected it.

    openai's APIConnectionError carries no status code and its message is just
    "Connection error." — no rate, no timeout — so a status/keyword test judged it
    non-retryable and the rollout died on attempt 1. One 30-second blip during M14
    killed six rollouts across two arms, four on one and two on the other, which
    puts a bias straight into an arm comparison.
    """
    assert classify_retryable(_ConnErr("Connection error."))[1] is True


@pytest.mark.parametrize(
    "msg",
    ["Connection error.", "Remote end closed connection without response", "Server disconnected"],
)
def test_network_phrasings_are_all_retryable(msg):
    assert classify_retryable(Exception(msg))[1] is True


def test_both_openai_retry_loops_use_the_shared_predicate():
    """Two copies of this test is how the blind spot survived: the non-streaming
    path and the streaming path each had their own status/keyword expression, so
    fixing one left the other. Neither may reconstruct it inline again."""
    import inspect as _inspect

    from harnessx.providers import openai_provider

    src = _inspect.getsource(openai_provider)
    assert "is_retryable = status in (" not in src, (
        "a retry loop rebuilt the predicate inline instead of calling "
        "classify_retryable — that is the drift this consolidation removes"
    )
    assert src.count("classify_retryable(e)") == 2, "both retry loops must call it"


# --- localised OS errors ------------------------------------------------------


@pytest.mark.parametrize(
    "exc",
    [
        ConnectionResetError(10054, "远程主机强迫关闭了一个现有的连接。"),
        ConnectionResetError(104, "Connection reset by peer"),
        ConnectionAbortedError(10053, "你的主机中的软件中止了一个已建立的连接。"),
        ConnectionRefusedError(10061, "由于目标计算机积极拒绝，无法连接。"),
        BrokenPipeError(32, "管道已结束。"),
        TimeoutError("timed out"),
    ],
)
def test_os_level_connection_errors_are_retryable_in_any_language(exc):
    """The English-substring tests miss these twice over.

    ``ConnectionResetError`` is not caught by the class-name test — the string
    "connectionreseterror" does not contain "connectionerror" — and on a Chinese
    Windows the message is "[WinError 10054] 远程主机强迫关闭了一个现有的连接。",
    which has no English keyword to match. So the predicate answered "not
    retryable" for the most transient failure there is: the same shape as the
    M14 bug, one locale over.

    ConnectionResetError subclasses ConnectionError subclasses OSError, and
    isinstance is the same in every language.
    """
    assert classify_retryable(exc)[1] is True


def test_a_localised_client_error_is_still_not_retried():
    """Locale-blindness must not turn into retrying everything: a 400 stays a
    400 whatever language it is reported in."""
    assert classify_retryable(_Err("请求格式错误", 400))[1] is False


def test_the_predicate_does_not_depend_on_english_for_os_errors():
    """A message with no ASCII at all still resolves, because the class carries
    the answer."""
    assert classify_retryable(ConnectionResetError(10054, "远程主机强迫关闭"))[1] is True
