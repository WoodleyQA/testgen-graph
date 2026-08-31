import logging

import anthropic

from ..state import GraphState
from ..llm_guard import guarded_call, parse_json_response

logger = logging.getLogger("testgen_graph")

MODEL = "claude-sonnet-4-5"  # match whatever model string your eval-harness uses

RUBRIC_PROMPT = """You are a senior QA engineer writing test cases for the following requirement:

{requirement}

Generate test cases covering these four categories. Not every category will always
apply — if a category is not applicable to this requirement, omit it and do not force one in.

- happy_path: the requirement works as intended under normal conditions
- negative: invalid input, wrong state, or expected failure
- boundary: edge of a limit (min/max size, empty set, expiry, exact threshold)
- auth_permission: access control, ownership, or session validity

Return ONLY a JSON array, no preamble, no markdown fences. Each element:
{{
  "id": "tc-1",
  "title": "short descriptive title",
  "category": "happy_path" | "negative" | "boundary" | "auth_permission",
  "steps": ["step 1", "step 2", ...],
  "expected_result": "what should happen"
}}
"""


def generate_cases(state: GraphState) -> GraphState:
    client = anthropic.Anthropic()
    prompt = RUBRIC_PROMPT.format(requirement=state["requirement"])

    result = guarded_call(client, MODEL, prompt, max_tokens=2000)

    try:
        cases = parse_json_response(result.text)
    except ValueError:
        run_metadata = {
            "failure_class": "malformed_json",
            "attempts": result.attempts,
            "latency_s": result.latency_s,
        }
        logger.error("generate_cases run_metadata=%s", run_metadata)
        raise

    run_metadata = {
        "failure_class": result.failure_class,
        "attempts": result.attempts,
        "latency_s": result.latency_s,
    }

    return {**state, "generated_cases": cases, "run_metadata": run_metadata}
