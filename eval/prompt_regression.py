"""
Prompt-as-tested-artifact.

The idea: a prompt edit is a code change and should be able to break tests, same as
any other change. This doesn't re-run the LLM to detect regressions (that's slow,
costs money, and is nondeterministic) — it snapshots automated_eval's SCORE for a
known-good run, and flags when a new run's score drops below that baseline by more
than a small tolerance. The LLM's raw output can vary between runs; the coverage
score is what actually needs to stay stable.

Workflow:
  1. Run the graph for a requirement, get generated_cases.
  2. record_baseline(...) once, when you're happy with the output.
  3. After any prompt edit, re-run and call check_regression(...) — it diffs the new
     score against the saved baseline and tells you if the prompt got worse.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .automated_eval import evaluate

BASELINE_DIR = Path(__file__).parent / "baselines"
SCORE_TOLERANCE = 0.10  # allow up to a 10-point coverage drop before flagging


def _prompt_hash(prompt_text: str) -> str:
    return hashlib.sha256(prompt_text.encode()).hexdigest()[:10]


@dataclass
class RegressionResult:
    requirement_key: str
    baseline_score: float
    current_score: float
    delta: float
    regressed: bool
    prompt_changed: bool


def record_baseline(requirement_key: str, generated_cases: list[dict], prompt_text: str) -> None:
    result = evaluate(requirement_key, generated_cases)
    BASELINE_DIR.mkdir(exist_ok=True)

    baseline = {
        "prompt_hash": _prompt_hash(prompt_text),
        "coverage_score": result.coverage_score,
        "duplicate_count": len(result.duplicates),
        "traceability_flag_count": len(result.traceability_flags),
    }
    (BASELINE_DIR / f"{requirement_key}.json").write_text(json.dumps(baseline, indent=2))
    print(f"Baseline recorded for {requirement_key}: coverage={result.coverage_score:.0%}")


def check_regression(requirement_key: str, generated_cases: list[dict], prompt_text: str) -> RegressionResult:
    path = BASELINE_DIR / f"{requirement_key}.json"
    if not path.exists():
        raise FileNotFoundError(f"No baseline recorded for {requirement_key} — run record_baseline first")

    baseline = json.loads(path.read_text())
    result = evaluate(requirement_key, generated_cases)

    delta = result.coverage_score - baseline["coverage_score"]
    prompt_changed = _prompt_hash(prompt_text) != baseline["prompt_hash"]
    regressed = delta < -SCORE_TOLERANCE

    return RegressionResult(
        requirement_key=requirement_key,
        baseline_score=baseline["coverage_score"],
        current_score=result.coverage_score,
        delta=delta,
        regressed=regressed,
        prompt_changed=prompt_changed,
    )


def print_regression(r: RegressionResult) -> None:
    status = "REGRESSED" if r.regressed else "ok"
    changed = " (prompt text changed since baseline)" if r.prompt_changed else ""
    print(f"[{status}] {r.requirement_key}: baseline={r.baseline_score:.0%} current={r.current_score:.0%} "
          f"delta={r.delta:+.0%}{changed}")
