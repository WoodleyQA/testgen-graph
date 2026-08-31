# testgen-graph

A two-node LangGraph pipeline that generates QA test cases from a plain-text
requirement, then converts them into Playwright test skeletons — with a
from-scratch eval layer (automated + human) to measure output quality against
hand-labeled ground truth.

## What it does

```
requirement (text)
      │
      ▼
Node1: generate_cases      → structured test cases (JSON)
      │
      ▼
Node2: generate_skeletons  → Playwright TypeScript skeletons
```

Both LLM calls run through `src/llm_guard.py` — a wrapper providing timeouts,
retry-on-transient-failure, malformed-JSON handling, and per-call cost/latency
logging. Not a demo shortcut; the intent is a pipeline safe to run unattended.

## Eval layer

Ground truth (`eval/ground_truth.py`) is hand-written for 4 reference
requirements against a fixed rubric: `happy_path`, `negative`, `boundary`,
`auth_permission`.

- **Automated** (`eval/automated_eval.py`) — three deterministic, non-LLM
  checks: category coverage vs. ground truth, near-duplicate detection
  (`SequenceMatcher`), and keyword-overlap traceability back to the
  requirement text.
- **Human** (`eval/human_eval.py`) — CLI captures a blind 1-5 usefulness
  rating per generated case.
- **Agreement** (`eval/agreement.py`) — compares human ratings against
  automated flags to see where the two disagree.
- **Prompt regression** (`eval/prompt_regression.py`) — snapshots a coverage
  score as a baseline; re-running after a prompt edit flags a regression if
  the score drops more than a 10% tolerance.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
```

## Running

```bash
# Run the graph end to end (prints case/skeleton counts)
python -m src.graph

# Run the test suite (no API key needed - exercises eval logic and guardrail
# retry/error-handling paths against mocked data)
pytest tests/ -v

# After a live run, rate the generated cases (blind to automated score)
python -m eval.human_eval password_reset path/to/generated_cases.json
```

## Test suite

`tests/test_automated_eval.py` — validates coverage scoring, duplicate detection,
and traceability flagging against known mock inputs.

`tests/test_llm_guard.py` — validates the guardrail wrapper's failure paths
directly, since a live run only ever exercises the happy path: confirms retry-then-
succeed on a simulated rate limit, confirms it gives up after max retries, and
confirms a non-transient error (bad request) is never retried.

## Status

Core pipeline, eval logic, and guardrail failure paths are covered by an automated
test suite (`pytest tests/`, 13 tests, all passing). Node1/Node2 have also been run
live against a real API key — see `eval/results/` for the golden-run artifacts
(12 cases at 100% rubric coverage, 12 clean Playwright skeletons).
