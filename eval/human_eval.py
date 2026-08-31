"""
Human eval capture. Run this BEFORE looking at automated_eval output — ratings need
to be blind to the automated score, or the agreement number is meaningless.

Usage: python -m eval.human_eval <requirement_key> <path_to_generated_cases.json>
Writes ratings to eval/results/<requirement_key>_human_ratings.json
"""

import json
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"


def capture_ratings(requirement_key: str, generated_cases: list[dict]) -> dict:
    ratings = {}
    print(f"\nRating generated cases for: {requirement_key}")
    print("Scale: 1 = useless/wrong, 5 = exactly what a QA engineer would write\n")

    for case in generated_cases:
        print(f"[{case['id']}] ({case['category']}) {case['title']}")
        for step in case.get("steps", []):
            print(f"    - {step}")
        print(f"    expected: {case.get('expected_result', '')}")

        while True:
            raw = input("  Rating (1-5): ").strip()
            if raw.isdigit() and 1 <= int(raw) <= 5:
                ratings[case["id"]] = int(raw)
                break
            print("  Enter a number 1-5.")
        print()

    return ratings


def main():
    requirement_key = sys.argv[1]
    cases_path = sys.argv[2]

    generated_cases = json.loads(Path(cases_path).read_text())
    ratings = capture_ratings(requirement_key, generated_cases)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"{requirement_key}_human_ratings.json"
    out_path.write_text(json.dumps(ratings, indent=2))
    print(f"Saved ratings to {out_path}")


if __name__ == "__main__":
    main()
