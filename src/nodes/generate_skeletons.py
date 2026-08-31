import json
import anthropic

from ..state import GraphState
from ..llm_guard import guarded_call

MODEL = "claude-sonnet-4-5"  # match whatever model string your eval-harness uses

SKELETON_PROMPT = """Convert the following QA test case into a Playwright test skeleton
(TypeScript). This is a hypothetical requirement with no live application behind it —
use clearly-named placeholder selectors (data-testid style) and stub assertions with
comments where real values would depend on the actual UI. Do not invent a real URL.

Test case:
{test_case}

Return ONLY the code, no markdown fences, no explanation. Structure:
- one `test(...)` block
- selectors as `page.locator('[data-testid="..."]')` placeholders
- one assertion per expected_result, using expect(), with a comment if the exact
  value/selector would need to be filled in against a real app
"""


def generate_skeletons(state: GraphState) -> GraphState:
    client = anthropic.Anthropic()
    skeletons = []

    for case in state["generated_cases"]:
        prompt = SKELETON_PROMPT.format(test_case=json.dumps(case))
        result = guarded_call(client, MODEL, prompt, max_tokens=800)

        code = result.text.strip()
        for fence in ("```typescript", "```ts", "```"):
            code = code.removeprefix(fence)
        code = code.removesuffix("```").strip()

        skeletons.append({"test_case_id": case["id"], "code": code})

    return {**state, "skeletons": skeletons}
