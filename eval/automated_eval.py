"""
Automated eval for Node1 output.

Three checks, each independent — none of them requires an LLM judge, deliberately:
this is a structural/statistical eval, not an LLM-as-judge eval. Keeps it fast,
deterministic, and immune to judge-hallucination critique in the interview.
"""

from dataclasses import dataclass, field
from difflib import SequenceMatcher

from .ground_truth import GROUND_TRUTH

CATEGORIES = ["happy_path", "negative", "boundary", "auth_permission"]
DUPLICATE_THRESHOLD = 0.75  # title similarity above this = flagged as near-duplicate


@dataclass
class EvalResult:
    requirement_key: str
    coverage: dict[str, bool] = field(default_factory=dict)   # category -> hit ground truth?
    coverage_score: float = 0.0                                 # fraction of applicable categories hit
    duplicates: list[tuple[str, str, float]] = field(default_factory=list)  # (id_a, id_b, similarity)
    traceability_flags: list[str] = field(default_factory=list)  # generated case ids with no requirement-text overlap


def _title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def score_coverage(requirement_key: str, generated_cases: list[dict]) -> tuple[dict[str, bool], float]:
    gt = GROUND_TRUTH[requirement_key]["cases"]
    applicable_categories = {c["category"] for c in gt}
    generated_categories = {c["category"] for c in generated_cases}

    coverage = {cat: (cat in generated_categories) for cat in applicable_categories}
    score = sum(coverage.values()) / len(applicable_categories) if applicable_categories else 0.0
    return coverage, score


def find_duplicates(generated_cases: list[dict]) -> list[tuple[str, str, float]]:
    dupes = []
    for i, a in enumerate(generated_cases):
        for b in generated_cases[i + 1:]:
            sim = _title_similarity(a["title"], b["title"])
            if sim >= DUPLICATE_THRESHOLD:
                dupes.append((a["id"], b["id"], round(sim, 2)))
    return dupes


def check_traceability(requirement_key: str, generated_cases: list[dict]) -> list[str]:
    """
    Flags generated cases whose title/steps don't share meaningful vocabulary with the
    requirement text — a cheap proxy for 'did the model invent scope not in the spec.'
    Not a semantic check; a keyword-overlap floor. Cases below the floor get manually
    reviewed, not auto-rejected.
    """
    requirement_text = GROUND_TRUTH[requirement_key]["requirement"].lower()
    requirement_words = set(w.strip(".,") for w in requirement_text.split() if len(w) > 3)

    flagged = []
    for case in generated_cases:
        case_text = (case["title"] + " " + " ".join(case.get("steps", []))).lower()
        case_words = set(w.strip(".,") for w in case_text.split() if len(w) > 3)
        overlap = requirement_words & case_words
        if len(overlap) == 0:
            flagged.append(case["id"])
    return flagged


def evaluate(requirement_key: str, generated_cases: list[dict]) -> EvalResult:
    coverage, coverage_score = score_coverage(requirement_key, generated_cases)
    duplicates = find_duplicates(generated_cases)
    traceability_flags = check_traceability(requirement_key, generated_cases)

    return EvalResult(
        requirement_key=requirement_key,
        coverage=coverage,
        coverage_score=coverage_score,
        duplicates=duplicates,
        traceability_flags=traceability_flags,
    )


def print_report(result: EvalResult, run_metadata: dict | None = None) -> None:
    print(f"\n=== {result.requirement_key} ===")
    if run_metadata:
        failure_class = run_metadata.get("failure_class", "unknown")
        attempts = run_metadata.get("attempts", "?")
        latency_s = run_metadata.get("latency_s")
        latency_str = f"{latency_s:.2f}s" if isinstance(latency_s, (int, float)) else "?"
        print(f"Tool path: {failure_class} (attempts={attempts}, latency={latency_str})")
    print(f"Coverage: {result.coverage_score:.0%}")
    for cat, hit in result.coverage.items():
        print(f"  [{'x' if hit else ' '}] {cat}")
    if result.duplicates:
        print(f"Near-duplicates: {result.duplicates}")
    if result.traceability_flags:
        print(f"Traceability flags (no keyword overlap with requirement): {result.traceability_flags}")
