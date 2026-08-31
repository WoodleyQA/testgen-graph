"""
Agreement between human judgment and the automated eval.

Per-case automated "flag" is binary: was this case a near-duplicate of another,
or did it fail the traceability keyword-overlap check? Either flag = a signal the
automated eval considers this case weak.

Agreement = do human ratings of 1-2 (weak) line up with automated flags, and do
human ratings of 4-5 (strong) line up with the absence of flags?

This is intentionally a simple 2x2 agreement rate, not a correlation coefficient —
defensible with a 7-8 case sample, where a Pearson r would be noise dressed as rigor.
"""

import json
from pathlib import Path

from .automated_eval import find_duplicates, check_traceability

RESULTS_DIR = Path(__file__).parent / "results"
WEAK_THRESHOLD = 2   # human rating <= this = "weak"
STRONG_THRESHOLD = 4  # human rating >= this = "strong"


def per_case_flags(requirement_key: str, generated_cases: list[dict]) -> dict[str, bool]:
    dupe_ids = {case_id for pair in find_duplicates(generated_cases) for case_id in pair[:2]}
    trace_ids = set(check_traceability(requirement_key, generated_cases))
    flagged = dupe_ids | trace_ids
    return {case["id"]: (case["id"] in flagged) for case in generated_cases}


def compute_agreement(requirement_key: str, generated_cases: list[dict]) -> dict:
    ratings_path = RESULTS_DIR / f"{requirement_key}_human_ratings.json"
    if not ratings_path.exists():
        raise FileNotFoundError(f"No human ratings found — run human_eval.py first: {ratings_path}")

    human_ratings = json.loads(ratings_path.read_text())
    flags = per_case_flags(requirement_key, generated_cases)

    agree = 0
    disagree = []
    considered = 0

    for case_id, rating in human_ratings.items():
        is_flagged = flags.get(case_id, False)
        if rating <= WEAK_THRESHOLD:
            considered += 1
            if is_flagged:
                agree += 1
            else:
                disagree.append((case_id, rating, "human weak, automated missed it"))
        elif rating >= STRONG_THRESHOLD:
            considered += 1
            if not is_flagged:
                agree += 1
            else:
                disagree.append((case_id, rating, "human strong, automated flagged it"))
        # ratings of 3 (neutral) are excluded — not a disagreement, just no signal either way

    agreement_rate = agree / considered if considered else None

    return {
        "requirement_key": requirement_key,
        "agreement_rate": agreement_rate,
        "considered": considered,
        "agreed": agree,
        "disagreements": disagree,
    }


def print_agreement(result: dict) -> None:
    print(f"\n=== Agreement: {result['requirement_key']} ===")
    if result["agreement_rate"] is None:
        print("No non-neutral ratings to compare.")
        return
    print(f"Agreement: {result['agreed']}/{result['considered']} ({result['agreement_rate']:.0%})")
    if result["disagreements"]:
        print("Disagreements:")
        for case_id, rating, reason in result["disagreements"]:
            print(f"  [{case_id}] human={rating} — {reason}")
