"""
Tests for src/llm_guard.py's retry behavior.

This is the code that's easiest to get wrong precisely because it only runs during
failures - every live test so far has exercised the happy path (API call succeeds).
These tests simulate the failure paths directly, with time.sleep mocked out so the
suite doesn't actually wait through the backoff delays.
"""

import sys
sys.path.insert(0, ".")

from unittest.mock import MagicMock, patch

import anthropic
import httpx
import pytest

from src.llm_guard import guarded_call, parse_json_response


def _mock_response(text: str, input_tokens=100, output_tokens=50):
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    response.usage.input_tokens = input_tokens
    response.usage.output_tokens = output_tokens
    return response


def _rate_limit_error():
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    http_response = httpx.Response(429, request=request)
    return anthropic.RateLimitError("rate limited", response=http_response, body=None)


def _bad_request_error():
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    http_response = httpx.Response(400, request=request)
    return anthropic.BadRequestError("bad request", response=http_response, body=None)


@patch("time.sleep", return_value=None)  # skip real backoff delays in tests
def test_retries_on_rate_limit_then_succeeds(mock_sleep):
    client = MagicMock()
    client.messages.create.side_effect = [_rate_limit_error(), _mock_response("ok")]

    result = guarded_call(client, "claude-sonnet-4-5", "test prompt", max_tokens=100)

    assert result.text == "ok"
    assert result.attempts == 2
    assert client.messages.create.call_count == 2
    mock_sleep.assert_called_once()  # backoff happened between attempt 1 and 2


@patch("time.sleep", return_value=None)
def test_gives_up_after_max_retries(mock_sleep):
    client = MagicMock()
    client.messages.create.side_effect = [_rate_limit_error(), _rate_limit_error(), _rate_limit_error()]

    with pytest.raises(anthropic.RateLimitError):
        guarded_call(client, "claude-sonnet-4-5", "test prompt", max_tokens=100)

    assert client.messages.create.call_count == 3  # 1 initial + 2 retries (MAX_RETRIES)


def test_does_not_retry_on_non_transient_error():
    """A 400 bad request is a caller bug, not a transient failure - retrying it
    just guarantees the same failure three times instead of one."""
    client = MagicMock()
    client.messages.create.side_effect = _bad_request_error()

    with pytest.raises(anthropic.BadRequestError):
        guarded_call(client, "claude-sonnet-4-5", "test prompt", max_tokens=100)

    assert client.messages.create.call_count == 1  # no retry attempted


def test_succeeds_immediately_with_no_errors():
    client = MagicMock()
    client.messages.create.return_value = _mock_response("clean response")

    result = guarded_call(client, "claude-sonnet-4-5", "test prompt", max_tokens=100)

    assert result.text == "clean response"
    assert result.attempts == 1


def test_parse_json_response_strips_markdown_fences():
    raw = '```json\n{"key": "value"}\n```'
    assert parse_json_response(raw) == {"key": "value"}


def test_parse_json_response_raises_with_context_on_invalid_json():
    with pytest.raises(ValueError, match="did not return valid JSON"):
        parse_json_response("this is not json")
