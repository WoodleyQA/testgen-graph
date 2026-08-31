"""
Thin wrapper both nodes call through instead of hitting the Anthropic API directly.

Why this exists (interview framing): the eval layer proves the graph's OUTPUT is
correct. This proves the graph is safe to run unattended — timeouts, retries, and
malformed-output handling are what stand between a demo and something you'd trust
in a CI pipeline running unattended 500x/day.
"""

import json
import time
import logging
from dataclasses import dataclass

import anthropic

logger = logging.getLogger("testgen_graph")

# Rough per-1M-token pricing, USD — update to match whatever model you're actually on.
# Not billing-accurate, just enough to log a per-call order-of-magnitude cost.
PRICING = {
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
}

DEFAULT_TIMEOUT_S = 30
MAX_RETRIES = 2
RETRY_BACKOFF_S = 2


@dataclass
class CallResult:
    text: str
    input_tokens: int
    output_tokens: int
    latency_s: float
    estimated_cost_usd: float
    attempts: int


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = PRICING.get(model)
    if not rates:
        return 0.0
    return (input_tokens / 1_000_000) * rates["input"] + (output_tokens / 1_000_000) * rates["output"]


def guarded_call(
    client: anthropic.Anthropic,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> CallResult:
    """
    Calls the API with a timeout and retries transient failures (rate limits,
    connection errors, timeouts). Does NOT retry on bad input (4xx other than 429) —
    that's a caller bug, not a transient failure, and retrying it just burns time
    and money for the same guaranteed failure.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 2):  # MAX_RETRIES retries = MAX_RETRIES+1 attempts
        start = time.monotonic()
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                timeout=timeout_s,
                messages=[{"role": "user", "content": prompt}],
            )
            latency = time.monotonic() - start

            text = response.content[0].text
            in_tok = response.usage.input_tokens
            out_tok = response.usage.output_tokens
            cost = _estimate_cost(model, in_tok, out_tok)

            logger.info(
                "llm_call ok attempt=%d latency=%.2fs in_tok=%d out_tok=%d est_cost=$%.5f",
                attempt, latency, in_tok, out_tok, cost,
            )

            return CallResult(
                text=text,
                input_tokens=in_tok,
                output_tokens=out_tok,
                latency_s=latency,
                estimated_cost_usd=cost,
                attempts=attempt,
            )

        except (anthropic.RateLimitError, anthropic.APITimeoutError, anthropic.APIConnectionError) as e:
            last_error = e
            logger.warning("llm_call transient_failure attempt=%d error=%s", attempt, e)
            if attempt <= MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_S * attempt)  # linear backoff
                continue
            raise

        except anthropic.APIStatusError as e:
            # Non-transient (bad request, auth, etc.) — don't retry, fail loud.
            logger.error("llm_call non_transient_failure attempt=%d error=%s", attempt, e)
            raise

    raise last_error  # unreachable, satisfies type checkers


def log_state_transition(node_name: str, state: dict) -> None:
    """
    Logs a snapshot of state after each node runs — separate from the per-call
    cost/latency logging above. That logs "how much did this call cost." This logs
    "what did the state actually look like at this point in the graph," which is
    what you need Sunday if Node1's output looks wrong and you want to know exactly
    what Node2 received, without re-running anything.

    Summarized, not dumped verbatim — full test-case/skeleton text would bloat logs
    fast and isn't what you need for a health check. Counts and identifiers are.
    """
    summary = {
        "node": node_name,
        "timestamp": time.time(),
        "requirement_len": len(state.get("requirement", "")) if state.get("requirement") else 0,
        "generated_cases_count": len(state.get("generated_cases") or []),
        "generated_case_ids": [c.get("id") for c in (state.get("generated_cases") or [])],
        "skeletons_count": len(state.get("skeletons") or []),
    }
    logger.info("state_transition %s", json.dumps(summary))


def parse_json_response(raw: str) -> dict | list:
    """
    Strips markdown fences the model sometimes adds despite instructions, then parses.
    Raises with the raw text attached so a failure is debuggable, not a bare traceback.
    """
    cleaned = raw.strip()
    for fence in ("```json", "```typescript", "```ts", "```"):
        cleaned = cleaned.removeprefix(fence)
    cleaned = cleaned.removesuffix("```").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON: {e}\n---raw output---\n{raw}") from e
